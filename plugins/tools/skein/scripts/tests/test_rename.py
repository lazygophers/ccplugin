"""rename 命令测试 — skein.py task rename <tid> [--id NEW] [--name NEW] / subtask rename <tid> <sid>。

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
    """写齐 prd.md frontmatter (TaskSpec 四要素) + design 接缝, 过 confirm 的 planning 硬门。"""
    (ws / ".skein" / "task" / tid / "prd.md").write_text("---\ndesc: 解决 X 问题\nboundary:\n  should:\n  - 范围内a\n  should_not: []\nestimate: 1\nacceptance:\n  - 用例通过\n---\n", encoding="utf-8")
    (ws / ".skein" / "task" / tid / "design.md").write_text(
        f"# {tid} — 详细设计\n\n## 测试接缝 (seam)\n- [x] API 层\n")


def _sub(t: dict[str, Any], sid: str) -> dict[str, Any] | None:
    return next((x for x in t.get("subtasks", []) if x.get("sid") == sid), None)


# ---------- 1. task --name 改 ----------
def test_task_rename_name(skein_cli: SkeinCli, ws: Path) -> None:
    """task rename <tid> --name 新名: name 变、id 不变。"""
    skein_cli(ws, "create", "task-a", "--name", "旧名", "--desc", "d")
    skein_cli(ws, "task", "rename", "task-a", "--name", "新名")
    t = _task(ws, "task-a")
    assert t["name"] == "新名", f"name 未改: {t['name']!r}"
    assert t["id"] == "task-a", f"id 不应变: {t['id']!r}"


# ---------- 2. task --id 改 (pending) ----------
def test_task_rename_id_pending(skein_cli: SkeinCli, ws: Path) -> None:
    """task rename <old> --id <new>: 目录迁移 + task.json id/branch + 顶层索引同步。"""
    skein_cli(ws, "create", "task-old", "--name", "n", "--desc", "d")
    skein_cli(ws, "task", "rename", "task-old", "--id", "task-new")
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
    skein_cli(ws, "task", "rename", "task-a", "--id", "task-a2")
    deps = _task(ws, "task-b").get("deps") or []
    assert "task-a2" in deps and "task-a" not in deps, f"deps 未同步: {deps}"


# ---------- 4. 非 pending 改 --id 拒 ----------
def test_task_rename_id_non_pending_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """active task 改 --id → 拒 (returncode!=0, stderr 提示仅限 confirm 前 待处理/调研中)。"""
    skein_cli(ws, "create", "task-a", "--name", "a", "--desc", "d")
    skein_cli(ws, "subtask", "add", "task-a", "s1", "--name", "x", "--desc", "d", "--estimate", "1")
    _fill_prd(ws, "task-a")
    skein_cli(ws, "estimate", "task-a", "--set", "1")  # estimate 硬门: confirm 前须填实工时
    skein_cli(ws, "confirm", "task-a")  # 待处理→进行中 (confirm 吸收 start)
    r = skein_cli(ws, "task", "rename", "task-a", "--id", "task-x", check=False)
    assert r.returncode != 0 and "仅限 confirm 前" in r.stderr, f"非 pending 改 id 未拒: {r.stderr!r}"


# ---------- 6. 改到已占用 id 拒 ----------
def test_task_rename_id_occupied_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """task rename A --id B 当 B 已存在 → 拒 (returncode!=0)。"""
    skein_cli(ws, "create", "task-a", "--name", "a", "--desc", "d")
    skein_cli(ws, "create", "task-b", "--name", "b", "--desc", "d")
    r = skein_cli(ws, "task", "rename", "task-a", "--id", "task-b", check=False)
    assert r.returncode != 0, f"占用 id 未拒: rc={r.returncode}"


# ---------- 7. subtask --name 改 ----------
def test_subtask_rename_name(skein_cli: SkeinCli, ws: Path) -> None:
    """subtask rename <tid> s1 --name 新子名: subtasks 中 s1 的 name 变。"""
    skein_cli(ws, "create", "task-a", "--name", "a", "--desc", "d")
    skein_cli(ws, "subtask", "add", "task-a", "s1", "--name", "旧子名", "--desc", "d", "--estimate", "1")
    skein_cli(ws, "subtask", "rename", "task-a", "s1", "--name", "新子名")
    s = _sub(_task(ws, "task-a"), "s1")
    assert s is not None and s["name"] == "新子名", f"子任务 name 未改: {s}"


# ---------- 8. subtask --id 改 + 同步 depends_on ----------
def test_subtask_rename_id_sync_depends(skein_cli: SkeinCli, ws: Path) -> None:
    """s2 depends s1 → subtask rename <tid> s1 --id s1x: s1x 存在, s2.depends_on 含 s1x 不含 s1。"""
    skein_cli(ws, "create", "task-a", "--name", "a", "--desc", "d")
    skein_cli(ws, "subtask", "add", "task-a", "s1", "--name", "一", "--desc", "d", "--estimate", "1")
    skein_cli(ws, "subtask", "add", "task-a", "s2", "--name", "二", "--desc", "d", "--estimate", "1", "--deps", "s1")
    skein_cli(ws, "subtask", "rename", "task-a", "s1", "--id", "s1x")
    t = _task(ws, "task-a")
    assert _sub(t, "s1x") is not None and _sub(t, "s1") is None, "sid 未改名"
    s2 = _sub(t, "s2")
    assert s2 is not None
    dep = s2["depends_on"]
    assert "s1x" in dep and "s1" not in dep, f"depends_on 未同步: {dep}"


# ---------- 9. 无 --id 无 --name 拒 ----------
def test_rename_no_flags_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    """task rename <tid> 无 --id 无 --name → 拒 (returncode!=0)。"""
    skein_cli(ws, "create", "task-a", "--name", "a", "--desc", "d")
    r = skein_cli(ws, "task", "rename", "task-a", check=False)
    assert r.returncode != 0, f"无参数 rename 未拒: rc={r.returncode}"
