# mypy: ignore-errors
"""workspace.py + task/store.py 覆盖 — _persist_bash_cwd_env / _workspace_lock / store 边界。
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

import conftest  # noqa: F401
from skeinlib.core.workspace import _persist_bash_cwd_env, _workspace_lock
from skeinlib.utils.errors import SkeinError


# ---- _persist_bash_cwd_env ----

def test_persist_bash_cwd_env_no_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_ENV_FILE", raising=False)
    _persist_bash_cwd_env()  # 不崩


def test_persist_bash_cwd_env_writes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / "env"
    monkeypatch.setenv("CLAUDE_ENV_FILE", str(env_file))
    _persist_bash_cwd_env()
    content = env_file.read_text()
    assert "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=0" in content


def test_persist_bash_cwd_env_idempotent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / "env"
    env_file.write_text("export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=0\n")
    monkeypatch.setenv("CLAUDE_ENV_FILE", str(env_file))
    _persist_bash_cwd_env()
    # 已有则不重复写
    content = env_file.read_text()
    assert content.count("AGENT_TEAMS") == 1


def test_persist_bash_cwd_env_oserror(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_ENV_FILE", "/nonexistent/dir/file")
    _persist_bash_cwd_env()  # OSError 吞掉不崩


# ---- _workspace_lock ----

def test_workspace_lock_normal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SKEIN_IN_HOOK", raising=False)
    lock = tmp_path / ".skein" / "write.lock"
    with _workspace_lock(lock):
        assert lock.exists()
    # 退出后锁文件关闭


def test_workspace_lock_in_hook(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """SKEIN_IN_HOOK 设位时跳过加锁。"""
    monkeypatch.setenv("SKEIN_IN_HOOK", "1")
    lock = tmp_path / "test.lock"
    with _workspace_lock(lock):
        pass  # no-op, 不创建文件


def test_workspace_lock_timeout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """锁被占 → 超时。"""
    import fcntl
    monkeypatch.delenv("SKEIN_IN_HOOK", raising=False)
    lock = tmp_path / ".skein" / "write.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.touch()
    # 先占住锁
    f = open(lock, "w")
    fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        with pytest.raises(SkeinError, match="超时"):
            with _workspace_lock(lock, timeout=0.1, poll=0.02):
                pass
    finally:
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        f.close()


# ---- task/store.py (via subprocess skein CLI — store 被间接覆盖) ----
# store 边界由已有 test_skein.py subprocess 测试覆盖, 不在此重复
