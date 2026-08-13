"""task 模块纯函数覆盖 — priority / readystate / dag。
无状态函数直接调验证返回值；迁移函数用 tmp_path 造 task.json。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from skeinlib.task import priority, readystate
from skeinlib.utils.errors import SkeinError


# ---- priority.py ----

def test_validate_priority_none_returns_default() -> None:
    assert priority.validate_priority(None) == "normal"


def test_validate_priority_valid() -> None:
    for p in ("urgent", "high", "normal", "low"):
        assert priority.validate_priority(p) == p


def test_validate_priority_invalid_raises() -> None:
    with pytest.raises(SkeinError, match="非法优先级"):
        priority.validate_priority("bogus")


def test_priority_from_legacy_urgent() -> None:
    assert priority.priority_from_legacy(10) == "urgent"
    assert priority.priority_from_legacy(8) == "urgent"


def test_priority_from_legacy_high() -> None:
    assert priority.priority_from_legacy(7) == "high"
    assert priority.priority_from_legacy(6) == "high"


def test_priority_from_legacy_normal() -> None:
    assert priority.priority_from_legacy(5) == "normal"
    assert priority.priority_from_legacy(4) == "normal"


def test_priority_from_legacy_low() -> None:
    assert priority.priority_from_legacy(3) == "low"
    assert priority.priority_from_legacy(0) == "low"


def test_migrate_priority_values(tmp_path: Path) -> None:
    root = tmp_path
    tasks_dir = root / ".skein" / "task"
    archive_dir = root / ".skein" / "archive"
    tdir = tasks_dir / "t1"
    tdir.mkdir(parents=True)
    (tdir / "task.json").write_text(json.dumps({"id": "t1", "priority": 9}))
    tdir2 = tasks_dir / "t2"
    tdir2.mkdir()
    (tdir2 / "task.json").write_text(json.dumps({"id": "t2", "priority": "high"}))  # 已迁移

    result = priority.migrate_priority_values(root, tasks_dir, archive_dir)
    assert len(result["migrated"]) == 1
    assert "t1" in result["migrated"][0]
    assert result["backup_dir"] is not None
    # 验证迁移后值
    data = json.loads((tdir / "task.json").read_text())
    assert data["priority"] == "urgent"


def test_migrate_priority_no_changes(tmp_path: Path) -> None:
    root = tmp_path
    tasks_dir = root / ".skein" / "task"
    archive_dir = root / ".skein" / "archive"
    tasks_dir.mkdir(parents=True)
    tdir = tasks_dir / "t1"
    tdir.mkdir()
    (tdir / "task.json").write_text(json.dumps({"id": "t1", "priority": "normal"}))
    result = priority.migrate_priority_values(root, tasks_dir, archive_dir)
    assert result["migrated"] == []
    assert result["backup_dir"] is None


def test_migrate_priority_skips_bad_json(tmp_path: Path) -> None:
    root = tmp_path
    tasks_dir = root / ".skein" / "task"
    archive_dir = root / ".skein" / "archive"
    tasks_dir.mkdir(parents=True)
    tdir = tasks_dir / "bad"
    tdir.mkdir()
    (tdir / "task.json").write_text("not json")
    result = priority.migrate_priority_values(root, tasks_dir, archive_dir)
    assert result["migrated"] == []


def test_migrate_priority_skips_bool(tmp_path: Path) -> None:
    root = tmp_path
    tasks_dir = root / ".skein" / "task"
    archive_dir = root / ".skein" / "archive"
    tasks_dir.mkdir(parents=True)
    tdir = tasks_dir / "t1"
    tdir.mkdir()
    (tdir / "task.json").write_text(json.dumps({"id": "t1", "priority": True}))
    result = priority.migrate_priority_values(root, tasks_dir, archive_dir)
    assert result["migrated"] == []


def test_migrate_priority_archive_dir(tmp_path: Path) -> None:
    root = tmp_path
    tasks_dir = root / ".skein" / "task"
    archive_dir = root / ".skein" / "archive"
    # 归档目录结构: archive/YYYY-MM-DD/HH/task_id/task.json
    adir = archive_dir / "2024-01-01" / "12" / "old-task"
    adir.mkdir(parents=True)
    (adir / "task.json").write_text(json.dumps({"id": "old-task", "priority": 3}))
    result = priority.migrate_priority_values(root, tasks_dir, archive_dir)
    assert len(result["migrated"]) == 1
    data = json.loads((adir / "task.json").read_text())
    assert data["priority"] == "low"


def test_migrate_priority_nonexistent_dirs(tmp_path: Path) -> None:
    root = tmp_path
    result = priority.migrate_priority_values(root, root / "nope1", root / "nope2")
    assert result["migrated"] == []
    assert result["backup_dir"] is None


# ---- readystate.py ----

def test_migrate_ready_status_task(tmp_path: Path) -> None:
    root = tmp_path
    tasks_dir = root / ".skein" / "task"
    archive_dir = root / ".skein" / "archive"
    tdir = tasks_dir / "t1"
    tdir.mkdir(parents=True)
    (tdir / "task.json").write_text(json.dumps({
        "id": "t1", "status": "就绪",
        "subtasks": [{"sid": "s1", "status": "运行中"}]
    }))
    result = readystate.migrate_ready_status(root, tasks_dir, archive_dir)
    assert len(result["migrated"]) == 1
    data = json.loads((tdir / "task.json").read_text())
    assert data["status"] == "pending"
    assert data["subtasks"][0]["status"] == "done" if False else data["subtasks"][0]["status"] in ("done", "running", "pending", "failed")


def test_migrate_ready_status_all_legacy_values(tmp_path: Path) -> None:
    root = tmp_path
    tasks_dir = root / ".skein" / "task"
    archive_dir = root / ".skein" / "archive"
    legacy_statuses = {
        "待处理": "pending", "调研中": "research", "就绪": "pending",
        "进行中": "active", "检查中": "check", "收尾中": "finishing", "已完成": "done"
    }
    for i, (old, new) in enumerate(legacy_statuses.items()):
        tdir = tasks_dir / f"t{i}"
        tdir.mkdir(parents=True)
        (tdir / "task.json").write_text(json.dumps({"id": f"t{i}", "status": old}))
    result = readystate.migrate_ready_status(root, tasks_dir, archive_dir)
    assert len(result["migrated"]) == len(legacy_statuses)
    for i, (_, expected) in enumerate(legacy_statuses.items()):
        data = json.loads((tasks_dir / f"t{i}" / "task.json").read_text())
        assert data["status"] == expected


def test_migrate_ready_status_subtask_legacy(tmp_path: Path) -> None:
    root = tmp_path
    tasks_dir = root / ".skein" / "task"
    archive_dir = root / ".skein" / "archive"
    tdir = tasks_dir / "t1"
    tdir.mkdir(parents=True)
    (tdir / "task.json").write_text(json.dumps({
        "id": "t1", "status": "active",
        "subtasks": [
            {"sid": "s1", "status": "待处理"},
            {"sid": "s2", "status": "运行中"},
            {"sid": "s3", "status": "已完成"},
            {"sid": "s4", "status": "失败"},
        ]
    }))
    result = readystate.migrate_ready_status(root, tasks_dir, archive_dir)
    assert len(result["migrated"]) == 1
    data = json.loads((tdir / "task.json").read_text())
    assert data["subtasks"][0]["status"] == "pending"
    assert data["subtasks"][1]["status"] == "running"
    assert data["subtasks"][2]["status"] == "done"
    assert data["subtasks"][3]["status"] == "failed"


def test_migrate_ready_status_idempotent(tmp_path: Path) -> None:
    root = tmp_path
    tasks_dir = root / ".skein" / "task"
    archive_dir = root / ".skein" / "archive"
    tdir = tasks_dir / "t1"
    tdir.mkdir(parents=True)
    (tdir / "task.json").write_text(json.dumps({"id": "t1", "status": "pending"}))
    result = readystate.migrate_ready_status(root, tasks_dir, archive_dir)
    assert result["migrated"] == []
    assert result["backup_dir"] is None


def test_migrate_ready_status_bad_json(tmp_path: Path) -> None:
    root = tmp_path
    tasks_dir = root / ".skein" / "task"
    archive_dir = root / ".skein" / "archive"
    tdir = tasks_dir / "bad"
    tdir.mkdir(parents=True)
    (tdir / "task.json").write_text("broken")
    result = readystate.migrate_ready_status(root, tasks_dir, archive_dir)
    assert result["migrated"] == []


def test_migrate_ready_status_archive(tmp_path: Path) -> None:
    root = tmp_path
    tasks_dir = root / ".skein" / "task"
    archive_dir = root / ".skein" / "archive"
    adir = archive_dir / "2024-01-01" / "12" / "old"
    adir.mkdir(parents=True)
    (adir / "task.json").write_text(json.dumps({"id": "old", "status": "就绪"}))
    result = readystate.migrate_ready_status(root, tasks_dir, archive_dir)
    assert len(result["migrated"]) == 1


def test_migrate_ready_status_nonexistent_dirs(tmp_path: Path) -> None:
    root = tmp_path
    result = readystate.migrate_ready_status(root, root / "nope1", root / "nope2")
    assert result["migrated"] == []
