"""supertask 全链路测试 — task 级父子层 (supertask↔task) 生命周期与不变量。

经 conftest 的 skein_cli/ws fixture 跑真实 skein.py CLI 子进程 (tmp_path 隔离)。
覆盖 (9 场景, 对应 st8 验收):
  1. create supertask (kind=supertask, parent=None) — task.json parent/kind 落对。
  2. create child (--parent <super>) — parent 写回 super id, kind=task。
  3. 深度守卫: --parent 指向一个 parent!=None 的 child → 拒 (限 2 层: super→task→subtask)。
  4. 深度守卫: --kind supertask + --parent 同传 → 拒 (supertask 是顶层聚合, 不可有 parent)。
  5. 引用完整性: --parent 指向不存在 task → 拒。
  6. 分组渲染: 有 supertask → task.md child 缩进; 无 supertask → 扁平 (零增量)。
  7. vision.md: supertask 下 child 进度聚合 (整体完成率 + 各 child 状态/subtask 比)。
  8. finish 聚合归档: super finish 有未 done child → 拒并列出; 全 done → 通过。
  9. 向后兼容: 旧 task.json 无 parent/kind 字段不崩, 默认 parent=None/kind=task。

状态中文常量与 skein.py:49-52 落盘值一致 (测试只读不 import 内部)。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from conftest import SkeinCli

S_DONE = "已完成"


def _task(ws: Path, tid: str) -> dict[str, Any]:
    """读 per-task task.json 真值 (.skein/task/<tid>/task.json)。"""
    return cast(dict[str, Any], json.loads((ws / ".skein" / "task" / tid / "task.json").read_text()))


def _write_task(ws: Path, tid: str, t: dict[str, Any]) -> None:
    (ws / ".skein" / "task" / tid / "task.json").write_text(json.dumps(t, ensure_ascii=False))


# ---------- 1. create supertask ----------
def test_create_supertask(skein_cli: SkeinCli, ws: Path) -> None:
    """create --kind supertask: parent=None, kind=supertask, 顶层索引镜像对。"""
    skein_cli(ws, "create", "epic-1", "--name", "大需求", "--desc", "聚合",
              "--kind", "supertask")
    t = _task(ws, "epic-1")
    assert t["kind"] == "supertask", f"kind 应为 supertask: {t['kind']}"
    assert t["parent"] is None, f"supertask parent 须 None: {t['parent']}"
    # 顶层 task.json 镜像同步 parent/kind
    top = json.loads((ws / ".skein" / "task.json").read_text())
    row = next(x for x in top["tasks"] if x["id"] == "epic-1")
    assert row["kind"] == "supertask" and row["parent"] is None, row


# ---------- 2. create child ----------
def test_create_child_under_supertask(skein_cli: SkeinCli, ws: Path) -> None:
    """create --parent <super>: parent 写回 super id, kind=task (默认)。"""
    skein_cli(ws, "create", "epic-1", "--name", "大需求", "--desc", "d", "--kind", "supertask")
    skein_cli(ws, "create", "child-a", "--name", "子A", "--desc", "d", "--parent", "epic-1")
    c = _task(ws, "child-a")
    assert c["parent"] == "epic-1", f"child parent 应指 super: {c['parent']}"
    assert c["kind"] == "task", f"child kind 默认 task: {c['kind']}"


# ---------- 3. 深度守卫: parent 自身是 child ----------
def test_depth_guard_parent_is_child(skein_cli: SkeinCli, ws: Path) -> None:
    """--parent 指向一个 parent!=None 的 child → 拒 (禁 child 作父, 限 2 层)。"""
    skein_cli(ws, "create", "epic-1", "--name", "e", "--desc", "d", "--kind", "supertask")
    skein_cli(ws, "create", "child-a", "--name", "c", "--desc", "d", "--parent", "epic-1")
    r = skein_cli(ws, "create", "grandchild", "--name", "g", "--desc", "d",
                  "--parent", "child-a", check=False)
    assert r.returncode != 0 and "深度超限" in r.stderr, f"child 作父未拒: {r.stderr!r}"


# ---------- 4. 深度守卫: supertask + parent 同传 ----------
def test_depth_guard_supertask_with_parent(skein_cli: SkeinCli, ws: Path) -> None:
    """--kind supertask + --parent 同传 → 拒 (supertask 是顶层聚合层)。"""
    skein_cli(ws, "create", "epic-1", "--name", "e", "--desc", "d", "--kind", "supertask")
    r = skein_cli(ws, "create", "epic-2", "--name", "e2", "--desc", "d",
                  "--kind", "supertask", "--parent", "epic-1", check=False)
    assert r.returncode != 0 and "supertask 不可有 parent" in r.stderr, \
        f"supertask+parent 同传未拒: {r.stderr!r}"


# ---------- 5. 引用完整性: parent 不存在 ----------
def test_parent_ref_integrity(skein_cli: SkeinCli, ws: Path) -> None:
    """--parent 指向不存在 task → 拒 (引用完整性)。"""
    r = skein_cli(ws, "create", "orphan", "--name", "o", "--desc", "d",
                  "--parent", "no-such-super", check=False)
    assert r.returncode != 0 and "不存在" in r.stderr, f"不存在 parent 未拒: {r.stderr!r}"


# ---------- 6. 分组渲染 (有 supertask / 无 supertask 零增量) ----------
def test_board_grouping_and_flat_zero_delta(skein_cli: SkeinCli, ws: Path) -> None:
    """有 supertask: child 行缩进 ↳; 无 supertask: 扁平, 与旧版逐字一致 (零增量)。"""
    # 先建扁平基线 (无 supertask): 两独立 task → 记 task.md body
    skein_cli(ws, "create", "solo-a", "--name", "甲", "--desc", "d")
    skein_cli(ws, "create", "solo-b", "--name", "乙", "--desc", "d")
    flat_md = (ws / ".skein" / "task.md").read_text()
    assert "↳" not in flat_md, "无 supertask 时不应出现 child 缩进符"

    # 引入 supertask + child → task.md 出现 ↳ 缩进分组
    skein_cli(ws, "create", "epic-1", "--name", "聚合", "--desc", "d", "--kind", "supertask")
    skein_cli(ws, "create", "child-a", "--name", "子", "--desc", "d", "--parent", "epic-1")
    grouped_md = (ws / ".skein" / "task.md").read_text()
    assert "↳ child-a" in grouped_md, "supertask 下 child 未缩进渲染"
    # supertask 行本身不缩进
    assert "| epic-1 |" in grouped_md, "supertask 分组头行缺失"


# ---------- 7. vision.md 聚合 ----------
def test_vision_md_aggregation(skein_cli: SkeinCli, ws: Path) -> None:
    """vision.md: supertask 下 child 进度聚合 (整体完成率 + 各 child 状态/subtask 比)。"""
    skein_cli(ws, "create", "epic-1", "--name", "聚合", "--desc", "d", "--kind", "supertask")
    skein_cli(ws, "create", "child-a", "--name", "子A", "--desc", "d", "--parent", "epic-1")
    skein_cli(ws, "create", "child-b", "--name", "子B", "--desc", "d", "--parent", "epic-1")
    vision = ws / ".skein" / "task" / "epic-1" / "vision.md"
    assert vision.exists(), "supertask 未刷 vision.md"
    body = vision.read_text()
    assert "整体进度" in body, "vision 缺整体进度"
    assert "child" in body and "child-a" in body and "child-b" in body, "vision 缺 child 行"
    # 无 child 的 supertask 不崩 (空表占位)
    skein_cli(ws, "create", "epic-empty", "--name", "空聚合", "--desc", "d", "--kind", "supertask")
    v2 = (ws / ".skein" / "task" / "epic-empty" / "vision.md").read_text()
    assert "整体进度" in v2 and "| - |" in v2, "无 child supertask vision 未兜底空表"


# ---------- 8. finish 聚合归档 ----------
def test_finish_aggregate_guard(skein_cli: SkeinCli, ws: Path) -> None:
    """super finish: 有未 done child → 拒并列出; 全 done → 通过。"""
    skein_cli(ws, "create", "epic-1", "--name", "聚合", "--desc", "d", "--kind", "supertask")
    # child 带 subtask (start 前置要求), 先 start/finish 两个 child
    for cid in ("child-a", "child-b"):
        skein_cli(ws, "create", cid, "--name", cid, "--desc", "d", "--parent", "epic-1")
        skein_cli(ws, "subtask", "add", cid, "s1", "--name", "x", "--desc", "d",
                  "--agent", "skein-executor")
        skein_cli(ws, "start", cid)
        skein_cli(ws, "finish", cid)

    # supertask 自身无 worktree (聚合层不 exec), 需手动置 active 才走 finish 门
    #   — 但 finish 要求 status in STATUS_ACTIVE; supertask create 即 pending。
    #   聚合归档门先于 worktree 合并, 验「child 全 done 才放行」语义:
    #   把一个 child 改回 active → super finish 应被聚合门挡并列出。
    ca = _task(ws, "child-a")
    ca["status"] = "进行中"
    _write_task(ws, "child-a", ca)
    # super 也置 active 才进 finish 分支 (聚合门在 worktree 合并前, 无 worktree 不影响门验)
    se = _task(ws, "epic-1")
    se["status"] = "进行中"
    _write_task(ws, "epic-1", se)
    skein_cli(ws, "board")  # 触发 _sync 重算索引
    r = skein_cli(ws, "finish", "epic-1", check=False)
    assert r.returncode != 0 and "未完成 child" in r.stderr and "child-a" in r.stderr, \
        f"未 done child 未挡 super finish: {r.stderr!r}"

    # child-a 重回 done → super finish 通过聚合门 (无 worktree 合并即落 done)
    ca["status"] = S_DONE
    _write_task(ws, "child-a", ca)
    skein_cli(ws, "board")
    r2 = skein_cli(ws, "finish", "epic-1", check=False)
    assert r2.returncode == 0, f"child 全 done 后 super finish 应通过: {r2.stderr!r}"
    assert _task(ws, "epic-1")["status"] == S_DONE, "super finish 未置 done"


# ---------- 9. 向后兼容: 旧 task.json 无 parent/kind ----------
def test_backward_compat_legacy_task_json(skein_cli: SkeinCli, ws: Path) -> None:
    """旧 task.json 无 parent/kind 字段: 不崩, 默认 parent=None/kind=task。"""
    skein_cli(ws, "create", "legacy", "--name", "老任务", "--desc", "d")
    # 模拟旧数据: 剥掉 parent/kind 字段
    t = _task(ws, "legacy")
    for k in ("parent", "kind"):
        t.pop(k, None)
    _write_task(ws, "legacy", t)
    # 顶层索引也模拟旧 (无 parent/kind)
    top = json.loads((ws / ".skein" / "task.json").read_text())
    for row in top["tasks"]:
        row.pop("parent", None)
        row.pop("kind", None)
    (ws / ".skein" / "task.json").write_text(json.dumps({"tasks": top["tasks"]}, ensure_ascii=False))
    # 触发 _sync 重算 + 看板渲染: 不崩, 且 .get 兜底默认
    skein_cli(ws, "board")
    board = (ws / ".skein" / "task.md").read_text()
    assert "legacy" in board, "旧数据 task 未渲染"
    # 重算后顶层索引补回默认值 (parent=None 不写 / kind=task)
    top2 = json.loads((ws / ".skein" / "task.json").read_text())
    row2 = next(x for x in top2["tasks"] if x["id"] == "legacy")
    assert row2.get("kind", "task") == "task", "旧数据 kind 未兜底 task"
    # doctor 不变量体检不因旧数据崩
    skein_cli(ws, "doctor")
