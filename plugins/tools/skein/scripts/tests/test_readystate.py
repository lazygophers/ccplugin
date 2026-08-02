"""存量「就绪」status 一次性迁移。

覆盖: 迁到待处理 / 备份可回滚 / 幂等 / 非就绪跳过 / CLI 后 doctor 通过。
设计见 .skein/task/concurrency-pools/design.md「s9 存量就绪态迁移」。
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Callable

import conftest  # noqa: F401  模块体把 scripts/ 塞进 sys.path
from skeinlib.readystate import migrate_ready_status  # noqa: E402

SkeinCli = Callable[..., subprocess.CompletedProcess[str]]


def _mk_task(tasks_dir: Path, tid: str, status: str) -> Path:
    d = tasks_dir / tid
    d.mkdir(parents=True)
    f = d / "task.json"
    f.write_text(json.dumps({"id": tid, "status": status}, ensure_ascii=False))
    return f


def test_migrate_ready_status_rewrites_to_pending_and_backs_up(tmp_path: Path) -> None:
    root = tmp_path
    tasks_dir = root / ".skein" / "task"
    archive_dir = tasks_dir / "archive"
    f_ready = _mk_task(tasks_dir, "task-ready", "就绪")
    f_active = _mk_task(tasks_dir, "task-active", "进行中")
    original_ready = f_ready.read_text()
    original_active = f_active.read_text()

    result = migrate_ready_status(root, tasks_dir, archive_dir)

    # 所有中文 status 都被迁移到英文枚举
    assert str(f_ready.relative_to(root)) in result["migrated"]
    assert str(f_active.relative_to(root)) in result["migrated"]
    assert json.loads(f_ready.read_text())["status"] == "pending"
    assert json.loads(f_active.read_text())["status"] == "active"  # 进行中→active

    # 快照可回滚: 备份目录里的原文件内容与迁移前逐字相同
    backup_dir = root / result["backup_dir"]
    backup_ready = backup_dir / f_ready.relative_to(root)
    assert backup_ready.read_text() == original_ready
    backup_active = backup_dir / f_active.relative_to(root)
    assert backup_active.read_text() == original_active


def test_migrate_ready_status_idempotent(tmp_path: Path) -> None:
    root = tmp_path
    tasks_dir = root / ".skein" / "task"
    archive_dir = tasks_dir / "archive"
    _mk_task(tasks_dir, "task-a", "就绪")

    first = migrate_ready_status(root, tasks_dir, archive_dir)
    assert len(first["migrated"]) == 1
    second = migrate_ready_status(root, tasks_dir, archive_dir)
    assert second["migrated"] == []
    assert second["backup_dir"] is None


def test_migrate_ready_status_skips_non_ready_and_missing_field(tmp_path: Path) -> None:
    root = tmp_path
    tasks_dir = root / ".skein" / "task"
    archive_dir = tasks_dir / "archive"
    _mk_task(tasks_dir, "task-pending", "pending")  # 已是英文枚举
    d = tasks_dir / "task-none"
    d.mkdir(parents=True)
    (d / "task.json").write_text(json.dumps({"id": "task-none"}))

    result = migrate_ready_status(root, tasks_dir, archive_dir)
    assert result["migrated"] == []


def test_migrate_ready_cli_then_doctor_passes(ws: Path, skein_cli: SkeinCli) -> None:
    skein_cli(ws, "create", "feat-x", "--name", "feat-x", "--desc", "d")
    tj = ws / ".skein" / "task" / "feat-x" / "task.json"
    t = json.loads(tj.read_text())
    t["status"] = "就绪"  # 模拟存量就绪态
    tj.write_text(json.dumps(t, ensure_ascii=False))

    r = skein_cli(ws, "migrate-ready")
    data = json.loads(r.stdout)
    assert len(data["migrated"]) == 1
    assert json.loads(tj.read_text())["status"] == "pending"

    skein_cli(ws, "doctor")  # check=True 默认, 非 0 退出即抛


def test_migrate_ready_cli_noop_when_nothing_to_migrate(ws: Path, skein_cli: SkeinCli) -> None:
    skein_cli(ws, "create", "feat-y", "--name", "feat-y", "--desc", "d")
    r = skein_cli(ws, "migrate-ready")
    data = json.loads(r.stdout)
    assert data["migrated"] == []
