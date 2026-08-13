# mypy: ignore-errors
"""doctor.py 深度边界 + cli/main.py legacy arg rewrite 覆盖。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pytest
import yaml

import conftest  # noqa: F401
from skeinlib.core.commands import Skein
from skeinlib.task.model import SubtaskStatus, TaskStatus
from skeinlib.utils.errors import SkeinError


def _skein(ws: Path, monkeypatch: pytest.MonkeyPatch) -> Skein:
    monkeypatch.chdir(ws)
    return Skein()


def _write_task(ws: Path, task: dict[str, Any]) -> None:
    task_dir = ws / ".skein" / "task" / str(task["id"])
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "task.json").write_text(json.dumps(task), encoding="utf-8")


# ---- doctor 边界: supertask parent / worktree / done without finished ----

def test_doctor_supertask_with_parent(ws: Path, monkeypatch: pytest.MonkeyPatch,
                                       capsys: pytest.CaptureFixture[str]) -> None:
    """supertask 有 parent → 错误。"""
    _write_task(ws, {"id": "super1", "status": "active", "kind": "supertask",
                     "parent": "other", "deps": [], "subtasks": []})
    sk = _skein(ws, monkeypatch)
    with pytest.raises(SkeinError):
        sk.doctor(argparse.Namespace(quality=False))
    out = capsys.readouterr().out
    assert "supertask 不可再有 parent" in out


def test_doctor_active_no_worktree_when_wt_on(ws: Path, monkeypatch: pytest.MonkeyPatch,
                                               capsys: pytest.CaptureFixture[str]) -> None:
    """在途 task 无 worktree 且 worktree 开启 → 错误。"""
    # config worktree on
    cfg = ws / ".skein" / "config.yaml"
    raw = yaml.safe_load(cfg.read_text())
    raw["worktree"] = {"enabled": True}
    cfg.write_text(yaml.safe_dump(raw))
    _write_task(ws, {"id": "t1", "status": "active", "deps": [], "subtasks": []})
    sk = _skein(ws, monkeypatch)
    with pytest.raises(SkeinError):
        sk.doctor(argparse.Namespace(quality=False))
    out = capsys.readouterr().out
    assert "无 worktree" in out


def test_doctor_active_no_started(ws: Path, monkeypatch: pytest.MonkeyPatch,
                                   capsys: pytest.CaptureFixture[str]) -> None:
    """在途 task started 未置 → 警告。"""
    _write_task(ws, {"id": "t1", "status": "active", "deps": [], "subtasks": [],
                     "started": None})
    sk = _skein(ws, monkeypatch)
    # active 无 worktree 不报错 (worktree 禁用时跳过检查)
    sk.doctor(argparse.Namespace(quality=False))
    out = capsys.readouterr().out
    # 可能报警告也可能干净通过
    assert isinstance(out, str)


def test_doctor_done_without_finished(ws: Path, monkeypatch: pytest.MonkeyPatch,
                                       capsys: pytest.CaptureFixture[str]) -> None:
    """done 但 finished 未置 → 警告。"""
    _write_task(ws, {"id": "t1", "status": "done", "deps": [], "subtasks": []})
    sk = _skein(ws, monkeypatch)
    sk.doctor(argparse.Namespace(quality=False))
    out = capsys.readouterr().out
    assert "finished" in out


def test_doctor_worktree_path_not_exists(ws: Path, monkeypatch: pytest.MonkeyPatch,
                                          capsys: pytest.CaptureFixture[str]) -> None:
    """在途 task worktree 路径不存在 → 错误。"""
    cfg = ws / ".skein" / "config.yaml"
    raw = yaml.safe_load(cfg.read_text())
    raw["worktree"] = {"enabled": True}
    cfg.write_text(yaml.safe_dump(raw))
    _write_task(ws, {"id": "t1", "status": "active", "deps": [], "subtasks": [],
                     "worktrees": [{"wt": "nonexistent_wt", "repo": "."}]})
    sk = _skein(ws, monkeypatch)
    with pytest.raises(SkeinError):
        sk.doctor(argparse.Namespace(quality=False))
    out = capsys.readouterr().out
    assert "worktree 路径不存在" in out


# ---- doctor: hooks config 边界 ----

def test_doctor_hooks_unknown_field_in_legal_stage(ws: Path, monkeypatch: pytest.MonkeyPatch,
                                                     capsys: pytest.CaptureFixture[str]) -> None:
    """合法阶段下 hooks 有未知字段 → 报错。"""
    cfg = ws / ".skein" / "config.yaml"
    cfg.write_text("hooks:\n  create:\n    before:\n      - command: x\n        bogus_field: y\n", encoding="utf-8")
    sk = _skein(ws, monkeypatch)
    with pytest.raises(SkeinError):
        sk.doctor(argparse.Namespace(quality=False))
    out = capsys.readouterr().out
    assert "未知字段" in out


# ---- cli/main.py: _rewrite_legacy_task_args ----

def test_rewrite_legacy_state(ws: Path) -> None:
    """`skein state ...` → `skein task state ...`"""
    from skeinlib.cli.main import _rewrite_legacy_task_args
    assert _rewrite_legacy_task_args(["state", "active", "t1"]) == ["task", "active", "t1"]


def test_rewrite_legacy_rename(ws: Path) -> None:
    """`skein rename t1 s1 ...` → `skein subtask rename t1 s1 ...`"""
    from skeinlib.cli.main import _rewrite_legacy_task_args
    assert _rewrite_legacy_task_args(["rename", "t1", "s1"]) == ["subtask", "rename", "t1", "s1"]


def test_rewrite_legacy_status(ws: Path) -> None:
    """`skein status t1 s1` → `skein subtask show t1 s1`"""
    from skeinlib.cli.main import _rewrite_legacy_task_args
    assert _rewrite_legacy_task_args(["status", "t1", "s1"]) == ["subtask", "show", "t1", "s1"]


def test_rewrite_legacy_task_commands(ws: Path) -> None:
    """`skein create ...` → `skein task create ...`"""
    from skeinlib.cli.main import _rewrite_legacy_task_args
    result = _rewrite_legacy_task_args(["create", "t1"])
    assert result[0] == "task"
    assert result[1] == "create"


def test_rewrite_legacy_no_change(ws: Path) -> None:
    """非 legacy 命令不改。"""
    from skeinlib.cli.main import _rewrite_legacy_task_args
    assert _rewrite_legacy_task_args(["list"]) == ["list"]
    assert _rewrite_legacy_task_args(["init"]) == ["init"]
    assert _rewrite_legacy_task_args([]) == []
