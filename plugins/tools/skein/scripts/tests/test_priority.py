"""task 优先级四档枚举 + 存量 0-10 数字迁移。

覆盖: 映射表四区间(含边界 3/4、5/6、7/8) / 未指定落中档 / 非法档位列出四个合法值 / 迁移前快照
可回滚 / 迁移幂等 / 迁移后 doctor 通过。设计见 .skein/task/task-priority/design.md。
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Callable

import pytest

import conftest  # noqa: F401  模块体把 scripts/ 塞进 sys.path
from skeinlib.utils.errors import SkeinError  # noqa: E402
from skeinlib.task.priority import (migrate_priority_values, priority_from_legacy,  # noqa: E402
                               validate_priority)

SkeinCli = Callable[..., subprocess.CompletedProcess[str]]


# ---------- priority_from_legacy: 映射表四区间 + 边界 ----------

@pytest.mark.parametrize("n,expected", [
    (0, "low"), (3, "low"),          # 0-3 低
    (4, "normal"), (5, "normal"),    # 4-5 中 (默认 5 落这)
    (6, "high"), (7, "high"),        # 6-7 高
    (8, "urgent"), (10, "urgent"),   # 8-10 紧急
])
def test_priority_from_legacy_boundaries(n: int, expected: str) -> None:
    assert priority_from_legacy(n) == expected


# ---------- validate_priority: 默认档 + 非法档位 ----------

def test_validate_priority_unspecified_defaults_to_normal() -> None:
    assert validate_priority(None) == "normal"


@pytest.mark.parametrize("v", ["urgent", "high", "normal", "low"])
def test_validate_priority_accepts_four_tiers(v: str) -> None:
    assert validate_priority(v) == v


def test_validate_priority_rejects_illegal_and_lists_four_values() -> None:
    with pytest.raises(SkeinError) as exc:
        validate_priority("5")
    msg = str(exc.value)
    for v in ("urgent", "high", "normal", "low"):
        assert v in msg


# ---------- 迁移: 快照可回滚 + 幂等 ----------

def _mk_legacy_task(tasks_dir: Path, tid: str, priority: int) -> Path:
    d = tasks_dir / tid
    d.mkdir(parents=True)
    f = d / "task.json"
    f.write_text(json.dumps({"id": tid, "status": "待处理", "priority": priority}, ensure_ascii=False))
    return f


def test_migrate_priority_values_rewrites_and_backs_up(tmp_path: Path) -> None:
    root = tmp_path
    tasks_dir = root / ".skein" / "task"
    archive_dir = tasks_dir / "archive"
    f_low = _mk_legacy_task(tasks_dir, "task-low", 2)
    f_urgent = _mk_legacy_task(tasks_dir, "task-urgent", 9)
    original_low = f_low.read_text()

    result = migrate_priority_values(root, tasks_dir, archive_dir)

    assert sorted(result["migrated"]) == sorted([
        str(f_low.relative_to(root)), str(f_urgent.relative_to(root))])
    assert json.loads(f_low.read_text())["priority"] == "low"
    assert json.loads(f_urgent.read_text())["priority"] == "urgent"

    # 快照可回滚: 备份目录里的原文件内容与迁移前逐字相同
    backup_dir = root / result["backup_dir"]
    backup_low = backup_dir / f_low.relative_to(root)
    assert backup_low.read_text() == original_low


def test_migrate_priority_values_idempotent(tmp_path: Path) -> None:
    root = tmp_path
    tasks_dir = root / ".skein" / "task"
    archive_dir = tasks_dir / "archive"
    _mk_legacy_task(tasks_dir, "task-a", 5)

    first = migrate_priority_values(root, tasks_dir, archive_dir)
    assert len(first["migrated"]) == 1
    second = migrate_priority_values(root, tasks_dir, archive_dir)
    assert second["migrated"] == []
    assert second["backup_dir"] is None


def test_migrate_priority_values_skips_already_migrated_and_missing_field(tmp_path: Path) -> None:
    root = tmp_path
    tasks_dir = root / ".skein" / "task"
    archive_dir = tasks_dir / "archive"
    d1 = tasks_dir / "task-str"
    d1.mkdir(parents=True)
    (d1 / "task.json").write_text(json.dumps({"id": "task-str", "priority": "high"}))
    d2 = tasks_dir / "task-none"
    d2.mkdir(parents=True)
    (d2 / "task.json").write_text(json.dumps({"id": "task-none"}))

    result = migrate_priority_values(root, tasks_dir, archive_dir)
    assert result["migrated"] == []


# ---------- CLI: 未指定落中档 + doctor 通过 ----------

def test_create_defaults_priority_to_normal(ws: Path, skein_cli: SkeinCli) -> None:
    skein_cli(ws, "create", "feat-x", "--name", "feat-x", "--desc", "d")
    t = json.loads((ws / ".skein" / "task" / "feat-x" / "task.json").read_text())
    assert t["priority"] == "normal"


def test_doctor_rejects_illegal_priority_value(ws: Path, skein_cli: SkeinCli) -> None:
    """违规: task.json priority 非四档枚举值 (如未迁移的存量数字) → doctor exit 1。"""
    skein_cli(ws, "create", "feat-x", "--name", "feat-x", "--desc", "d")
    tj = ws / ".skein" / "task" / "feat-x" / "task.json"
    t = json.loads(tj.read_text())
    t["priority"] = 7
    tj.write_text(json.dumps(t, ensure_ascii=False))
    r = skein_cli(ws, "doctor", check=False)
    assert r.returncode == 1
    assert "非法 priority" in r.stdout


# ---------- CLI: create --priority + priority 改优先级命令 ----------

def test_create_with_priority_flag_persists(ws: Path, skein_cli: SkeinCli) -> None:
    skein_cli(ws, "create", "feat-y", "--name", "feat-y", "--desc", "d", "--priority", "urgent")
    t = json.loads((ws / ".skein" / "task" / "feat-y" / "task.json").read_text())
    assert t["priority"] == "urgent"


def test_create_with_illegal_priority_rejected_and_lists_four_values(ws: Path, skein_cli: SkeinCli) -> None:
    r = skein_cli(ws, "create", "feat-z", "--name", "feat-z", "--desc", "d",
                  "--priority", "nope", check=False)
    assert r.returncode != 0
    for v in ("urgent", "high", "normal", "low"):
        assert v in r.stderr


def test_priority_cmd_query_and_set(ws: Path, skein_cli: SkeinCli) -> None:
    skein_cli(ws, "create", "feat-q", "--name", "feat-q", "--desc", "d")
    r = skein_cli(ws, "priority", "feat-q")
    data = json.loads(r.stdout)
    assert data["priority"] == "normal"  # 未指定落中档
    r = skein_cli(ws, "priority", "feat-q", "--set", "high")
    data2 = json.loads(r.stdout)
    assert data2["priority"] == "high"
    t = json.loads((ws / ".skein" / "task" / "feat-q" / "task.json").read_text())
    assert t["priority"] == "high"


def test_priority_cmd_rejects_illegal_value(ws: Path, skein_cli: SkeinCli) -> None:
    skein_cli(ws, "create", "feat-r", "--name", "feat-r", "--desc", "d")
    r = skein_cli(ws, "priority", "feat-r", "--set", "urgentish", check=False)
    assert r.returncode != 0
    for v in ("urgent", "high", "normal", "low"):
        assert v in r.stderr


def test_priority_cmd_changes_active_task(ws: Path, skein_cli: SkeinCli) -> None:
    # 进行中态也能改 (调度旋钮, 不锁状态) —— 直接改盘面态模拟已 start, 免走完整 confirm/start 链路
    skein_cli(ws, "create", "feat-active", "--name", "feat-active", "--desc", "d")
    tj = ws / ".skein" / "task" / "feat-active" / "task.json"
    t = json.loads(tj.read_text())
    t["status"] = "进行中"
    tj.write_text(json.dumps(t, ensure_ascii=False))

    skein_cli(ws, "priority", "feat-active", "--set", "urgent")
    assert json.loads(tj.read_text())["priority"] == "urgent"


def test_status_and_list_show_priority(ws: Path, skein_cli: SkeinCli) -> None:
    skein_cli(ws, "create", "feat-s", "--name", "feat-s", "--desc", "d", "--priority", "high")
    r = skein_cli(ws, "status", "feat-s")
    assert "high" in r.stdout
    r = skein_cli(ws, "list")
    assert "high" in r.stdout
    data = json.loads(skein_cli(ws, "list", "--json").stdout)
    rows = data.get("tasks", data) if isinstance(data, dict) else data
    assert next(x for x in rows if x["id"] == "feat-s")["priority"] == "high"
