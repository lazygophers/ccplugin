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
  9. 最新 task.json schema: parent/kind 字段由 create 落盘。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from conftest import SkeinCli
from skeinlib.task.model import TaskStatus


def _task(ws: Path, tid: str) -> dict[str, Any]:
    """读 per-task task.json 真值 (.skein/task/<tid>/task.json)。"""
    return cast(dict[str, Any], json.loads((ws / ".skein" / "task" / tid / "task.json").read_text()))


def _fill_prd(ws: Path, tid: str) -> None:
    """写规范 prd.md 过 start 的 _validate_prd 门 (章节齐 + 无 TODO 占位)。"""
    (ws / ".skein" / "task" / tid / "prd.md").write_text(
        f"# {tid} — PRD\n\n## 目标\n- 解决 X\n\n"
        "## 边界\n- a\n\n## User Stories\n1. As a user, I want X\n\n"
        "## 验收标准\n- 通过\n\n## Testing Decisions\n- 复用现有单测\n\n## 索引\n- design.md\n")


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
        skein_cli(ws, "subtask", "add", cid, "s1", "--name", "x", "--desc", "d", "--estimate", "1")
        _fill_prd(ws, cid)
        skein_cli(ws, "estimate", cid, "--set", "1")  # estimate 硬门: confirm 前须填实工时
        skein_cli(ws, "confirm", cid)  # 待处理→进行中 (confirm 吸收 start)
        skein_cli(ws, "check", cid)
        skein_cli(ws, "finishing", cid)  # 检查中→收尾中 (finish 仅接受收尾中态入参)
        skein_cli(ws, "finish", cid)

    # supertask 自身无 worktree (聚合层不 exec), 需手动置收尾中才走 finish 门
    #   — 但 finish 要求 status == TaskStatus.FINISHING; supertask create 即 pending。
    #   聚合归档门先于 worktree 合并, 验「child 全 done 才放行」语义:
    #   把一个 child 改回 active → super finish 应被聚合门挡并列出。
    ca = _task(ws, "child-a")
    ca["status"] = TaskStatus.ACTIVE
    _write_task(ws, "child-a", ca)
    # super 也置收尾中才进 finish 分支 (聚合门在 worktree 合并前, 无 worktree 不影响门验)
    se = _task(ws, "epic-1")
    se["status"] = TaskStatus.FINISHING
    _write_task(ws, "epic-1", se)
    skein_cli(ws, "board")  # 触发 _sync 重算索引
    r = skein_cli(ws, "finish", "epic-1", check=False)
    assert r.returncode != 0 and "未完成 child" in r.stderr and "child-a" in r.stderr, \
        f"未 done child 未挡 super finish: {r.stderr!r}"

    # child-a 重回 done → super finish 通过聚合门 (无 worktree 合并即落 done)
    ca["status"] = TaskStatus.DONE
    _write_task(ws, "child-a", ca)
    skein_cli(ws, "board")
    r2 = skein_cli(ws, "finish", "epic-1", check=False)
    assert r2.returncode == 0, f"child 全 done 后 super finish 应通过: {r2.stderr!r}"
    assert _task(ws, "epic-1")["status"] == TaskStatus.DONE, "super finish 未置 done"


# ---------- 9. 最新 task.json schema ----------
def test_task_json_schema_fields(skein_cli: SkeinCli, ws: Path) -> None:
    """create 写入最新 parent/kind/status schema。"""
    skein_cli(ws, "create", "task-one", "--name", "任务", "--desc", "d")
    t = _task(ws, "task-one")
    assert t["parent"] is None, f"parent 应落 None: {t}"
    assert t["kind"] == "task", f"kind 应落 task: {t}"
    assert t["status"] == TaskStatus.PENDING, f"status 应落英文 enum: {t}"
