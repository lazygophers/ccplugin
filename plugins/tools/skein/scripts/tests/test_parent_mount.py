"""挂载命令测试 — `skein parent <id> --set <parent>` 给既有 task 补/改/摘 parent。

经 conftest 的 skein_cli/ws fixture 跑真实 skein.py CLI 子进程 (tmp_path 隔离)。
校验复用 create 那条 parent 链检查 (父存在/非自引用/父自身非 child), 不另写一套 —— 见
skeinlib/lifecycle.py Lifecycle.parent()。覆盖 (对应 d1 验收 7 条):
  1. 合法挂载: task.json parent 字段正确落盘。
  2. 自引用被拒。
  3. 父不存在被拒。
  4. 使父子链超 2 层被拒 (父自身是 child)。
  5. 成环被拒 (本 task 已有 child, 再挂父会让 child 超 2 层)。
  6. 摘除 (--set 空串) 后 parent 置空。
  7. doctor 全程通过。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from conftest import SkeinCli


def _task(ws: Path, tid: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((ws / ".skein" / "task" / tid / "task.json").read_text()))


# ---------- 1. 合法挂载 ----------
def test_mount_existing_task_to_supertask(skein_cli: SkeinCli, ws: Path) -> None:
    skein_cli(ws, "create", "epic-1", "--name", "e", "--desc", "d", "--kind", "supertask")
    skein_cli(ws, "create", "orphan-a", "--name", "o", "--desc", "d")
    assert _task(ws, "orphan-a")["parent"] is None
    r = skein_cli(ws, "parent", "orphan-a", "--set", "epic-1")
    assert r.returncode == 0, f"合法挂载应成功: {r.stderr!r}"
    assert _task(ws, "orphan-a")["parent"] == "epic-1", "parent 字段未落盘"
    # 顶层索引同步
    top = json.loads((ws / ".skein" / "task.json").read_text())
    row = next(x for x in top["tasks"] if x["id"] == "orphan-a")
    assert row["parent"] == "epic-1", row
    skein_cli(ws, "doctor")


# ---------- 2. 自引用被拒 ----------
def test_mount_self_reference_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    skein_cli(ws, "create", "a", "--name", "a", "--desc", "d")
    r = skein_cli(ws, "parent", "a", "--set", "a", check=False)
    assert r.returncode != 0 and "自引用" in r.stderr, f"自引用未拒: {r.stderr!r}"


# ---------- 3. 父不存在被拒 ----------
def test_mount_parent_not_found_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    skein_cli(ws, "create", "a", "--name", "a", "--desc", "d")
    r = skein_cli(ws, "parent", "a", "--set", "no-such-task", check=False)
    assert r.returncode != 0 and "不存在" in r.stderr, f"父不存在未拒: {r.stderr!r}"


# ---------- 4. 超 2 层被拒 (父自身是 child) ----------
def test_mount_depth_guard_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    skein_cli(ws, "create", "epic-1", "--name", "e", "--desc", "d", "--kind", "supertask")
    skein_cli(ws, "create", "child-a", "--name", "c", "--desc", "d", "--parent", "epic-1")
    skein_cli(ws, "create", "orphan-b", "--name", "o", "--desc", "d")
    r = skein_cli(ws, "parent", "orphan-b", "--set", "child-a", check=False)
    assert r.returncode != 0 and "深度超限" in r.stderr, f"超 2 层未拒: {r.stderr!r}"


# ---------- 5. 成环被拒 (本 task 已有 child) ----------
def test_mount_cycle_rejected(skein_cli: SkeinCli, ws: Path) -> None:
    skein_cli(ws, "create", "epic-1", "--name", "e", "--desc", "d", "--kind", "supertask")
    skein_cli(ws, "create", "child-a", "--name", "c", "--desc", "d", "--parent", "epic-1")
    # epic-1 已是 child-a 的父, 反过来给 epic-1 挂父 child-a → 成环, 拒
    r = skein_cli(ws, "parent", "epic-1", "--set", "child-a", check=False)
    assert r.returncode != 0 and "child" in r.stderr, f"成环未拒: {r.stderr!r}"
    assert _task(ws, "epic-1")["parent"] is None, "拒绝后不应落盘"


# ---------- 6. 摘除 ----------
def test_unmount_clears_parent(skein_cli: SkeinCli, ws: Path) -> None:
    skein_cli(ws, "create", "epic-1", "--name", "e", "--desc", "d", "--kind", "supertask")
    skein_cli(ws, "create", "child-a", "--name", "c", "--desc", "d", "--parent", "epic-1")
    assert _task(ws, "child-a")["parent"] == "epic-1"
    r = skein_cli(ws, "parent", "child-a", "--set", "")
    assert r.returncode == 0, f"摘除应成功: {r.stderr!r}"
    assert _task(ws, "child-a")["parent"] is None, "摘除后 parent 应置空"
    top = json.loads((ws / ".skein" / "task.json").read_text())
    row = next(x for x in top["tasks"] if x["id"] == "child-a")
    assert row["parent"] is None, row
    skein_cli(ws, "doctor")


# ---------- 7. 查询 (无 --set) ----------
def test_parent_query_no_set(skein_cli: SkeinCli, ws: Path) -> None:
    skein_cli(ws, "create", "epic-1", "--name", "e", "--desc", "d", "--kind", "supertask")
    skein_cli(ws, "create", "child-a", "--name", "c", "--desc", "d", "--parent", "epic-1")
    r = skein_cli(ws, "parent", "child-a")
    data = json.loads(r.stdout)
    assert r.returncode == 0 and data.get("parent") == "epic-1", f"查询未回显 parent: {r.stdout!r}"
    skein_cli(ws, "create", "orphan-a", "--name", "o", "--desc", "d")
    r2 = skein_cli(ws, "parent", "orphan-a")
    data2 = json.loads(r2.stdout)
    assert r2.returncode == 0 and data2.get("parent") is None, f"无父查询应显式提示: {r2.stdout!r}"


# ---------- deps 不受影响 (parent 与 deps 正交) ----------
def test_parent_mount_does_not_touch_deps(skein_cli: SkeinCli, ws: Path) -> None:
    skein_cli(ws, "create", "epic-1", "--name", "e", "--desc", "d", "--kind", "supertask")
    skein_cli(ws, "create", "dep-src", "--name", "s", "--desc", "d")
    skein_cli(ws, "create", "orphan-a", "--name", "o", "--desc", "d", "--deps", "dep-src")
    assert _task(ws, "orphan-a")["deps"] == ["dep-src"]
    skein_cli(ws, "parent", "orphan-a", "--set", "epic-1")
    assert _task(ws, "orphan-a")["deps"] == ["dep-src"], "挂父不该动 deps"
