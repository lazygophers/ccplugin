"""rename 命令测试 — skein.py rename <tid> [sid] [--id NEW] [--name NEW]。

经 conftest 的 skein_cli/ws fixture 跑真实 skein.py CLI 子进程 (tmp_path 隔离)。
覆盖 (9 用例):
  1. task --name 改: name 变、id 不变。
  2. task --id 改 (pending): 旧目录去/新目录在, task.json id+branch 同步, 顶层索引换。
  3. task --id 同步别 task deps: B deps A → rename A → B deps 指 A2。
  4. task --id 同步 child parent: C parent P → rename P → C parent 指 P2。
  5. 非 pending 改 --id 拒 (returncode!=0, stderr 含 pending)。
  6. 改到已占用 id 拒 (returncode!=0)。
  7. subtask --name 改: 子任务 name 变。
  8. subtask --id 改 + 同步同 task 内别 subtask depends_on。
  9. 无 --id 无 --name → 拒。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from conftest import SkeinCli


def _task(ws: Path, tid: str) -> dict[str, Any]:
    """读 per-task task.json 真值 (.skein/task/<tid>/task.json)。"""
    return cast(dict[str, Any], json.loads((ws / ".skein" / "task" / tid / "task.json").read_text()))


def _top(ws: Path) -> list[dict[str, Any]]:
    """读顶层索引 tasks[] (.skein/task.json)。"""
    return cast(list[dict[str, Any]], json.loads((ws / ".skein" / "task.json").read_text())["tasks"])


def _fill_prd(ws: Path, tid: str) -> None:
    """写规范 prd.md 过 start 的 _validate_prd 门 (章节齐 + 无 TODO 占位)。"""
    (ws / ".skein" / "task" / tid / "prd.md").write_text(
        f"# {tid} — PRD\n\n## 目标\n- 解决 X\n\n"
        "## 边界\n- a\n\n## 验收标准\n- 通过\n\n## 索引\n- design.md\n")


def _sub(t: dict[str, Any], sid: str) -> dict[str, Any] | None:
    return next((x for x in t.get("subtasks", []) if x.get("sid") == sid), None)


# ---------- 1. task --name 改 ----------
def test_task_rename_name(skein_cli: SkeinCli, ws: Path) -> None:
    """rename <tid> --name 新名: name 变、id 不变。"""
    skein_cli(ws, "create", "task-a", "--name", "旧名", "--desc", "d")
    skein_cli(ws, "rename", "task-a", "--name", "新名")
    t = _task(ws, "task-a")
    assert t["name"] == "新名", f"name 未改: {t['name']!r}"
    assert t["id"] == "task-a", f"id 不应变: {t['id']!r}"


# ---------- 2. task --id 改 (pending) ----------
def test_task_rename_id_pending(skein_cli: SkeinCli, ws: Path) -> None:
    """rename <old> --id <new>: 目录迁移 + task.json id/branch + 顶层索引同步。"""
    skein_cli(ws, "create", "task-old", "--name", "n", "--desc", "d")
    skein_cli(ws, "rename", "task-old", "--id", "task-new")
    assert not (ws / ".skein" / "task" / "task-old").exists(), "旧目录未删"
    assert (ws / ".skein" / "task" / "task-new").exists(), "新目录未建"
    t = _task(ws, "task-new")
    assert t["id"] == "task-new", f"task.json id 未改: {t['id']!r}"
    assert t["branch"] == "skein/task-new", f"branch 未同步: {t['branch']!r}"
    ids = [x["id"] for x in _top(ws)]
    assert "task-new" in ids and "task-old" not in ids, f"顶层索引未换: {ids}"


# ---------- 3. task --id 同步别 task deps ----------
def test_task_rename_id_sync_deps(skein_cli: SkeinCli, ws: Path) -> None:
    """B deps A → rename A --id A2: B 的 deps 含 A2 不含 A。"""
    skein_cli(ws, "create", "task-a", "--name", "a", "--desc", "d")
    skein_cli(ws, "create", "task-b", "--name", "b", "--desc", "d", "--deps", "task-a")
    skein_cli(ws, "rename", "task-a", "--id", "task-a2")
    deps = _task(ws, "task-b").get("deps") or []
    assert "task-a2" in deps and "task-a" not in deps, f"deps 未同步: {deps}"


# ---------- 4. task --id 同步 child parent ----------
def test_task_rename_id_sync_parent(skein_cli: SkeinCli, ws: Path) -> None:
    """C parent P → rename P --id P2: C 的 parent==P2。"""
    skein_cli(ws, "create", "epic-p", "--name", "p", "--desc", "d", "--kind", "supertask")
    skein_cli(ws, "create", "child-c", "--name", "c", "--desc", "d", "--parent", "epic-p")
    skein_cli(ws, "rename", "epic-p", "--id", "epic-p2")
    assert _task(ws, "child-c")["parent"] == "epic-p2", \
        f"child parent 未同步: {_task(ws, 'child-c')['parent']!r}"


# ---------- 5. 非 pending 改 --id 拒 ----------
def test_task_rename_id_non_pending_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """active task 改 --id → 拒 (returncode!=0, stderr 含 pending)。"""
    skein_cli(ws, "create", "task-a", "--name", "a", "--desc", "d")
    skein_cli(ws, "subtask", "add", "task-a", "s1", "--name", "x", "--desc", "d",
              "--agent", "skein-executor")
    _fill_prd(ws, "task-a")
    skein_cli(ws, "start", "task-a")
    r = skein_cli(ws, "rename", "task-a", "--id", "task-x", check=False)
    assert r.returncode != 0 and "pending" in r.stderr, f"非 pending 改 id 未拒: {r.stderr!r}"


# ---------- 6. 改到已占用 id 拒 ----------
def test_task_rename_id_occupied_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """rename A --id B 当 B 已存在 → 拒 (returncode!=0)。"""
    skein_cli(ws, "create", "task-a", "--name", "a", "--desc", "d")
    skein_cli(ws, "create", "task-b", "--name", "b", "--desc", "d")
    r = skein_cli(ws, "rename", "task-a", "--id", "task-b", check=False)
    assert r.returncode != 0, f"占用 id 未拒: rc={r.returncode}"


# ---------- 7. subtask --name 改 ----------
def test_subtask_rename_name(skein_cli: SkeinCli, ws: Path) -> None:
    """rename <tid> s1 --name 新子名: subtasks 中 s1 的 name 变。"""
    skein_cli(ws, "create", "task-a", "--name", "a", "--desc", "d")
    skein_cli(ws, "subtask", "add", "task-a", "s1", "--name", "旧子名", "--desc", "d")
    skein_cli(ws, "rename", "task-a", "s1", "--name", "新子名")
    s = _sub(_task(ws, "task-a"), "s1")
    assert s is not None and s["name"] == "新子名", f"子任务 name 未改: {s}"


# ---------- 8. subtask --id 改 + 同步 depends_on ----------
def test_subtask_rename_id_sync_depends(skein_cli: SkeinCli, ws: Path) -> None:
    """s2 depends s1 → rename <tid> s1 --id s1x: s1x 存在, s2.depends_on 含 s1x 不含 s1。"""
    skein_cli(ws, "create", "task-a", "--name", "a", "--desc", "d")
    skein_cli(ws, "subtask", "add", "task-a", "s1", "--name", "一", "--desc", "d")
    skein_cli(ws, "subtask", "add", "task-a", "s2", "--name", "二", "--desc", "d", "--deps", "s1")
    skein_cli(ws, "rename", "task-a", "s1", "--id", "s1x")
    t = _task(ws, "task-a")
    assert _sub(t, "s1x") is not None and _sub(t, "s1") is None, "sid 未改名"
    dep = _sub(t, "s2")["depends_on"]
    assert "s1x" in dep and "s1" not in dep, f"depends_on 未同步: {dep}"


# ---------- 9. 无 --id 无 --name 拒 ----------
def test_rename_no_flags_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """rename <tid> 无 --id 无 --name → 拒 (returncode!=0)。"""
    skein_cli(ws, "create", "task-a", "--name", "a", "--desc", "d")
    r = skein_cli(ws, "rename", "task-a", check=False)
    assert r.returncode != 0, f"无参数 rename 未拒: rc={r.returncode}"
