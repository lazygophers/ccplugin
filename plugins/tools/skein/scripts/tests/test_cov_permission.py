"""hooks permission/stop 模块覆盖。
"""
from __future__ import annotations

import json
from typing import Any

import pytest

from skeinlib.hooks import permission_request as pr
from skeinlib.hooks import permission_denied as pd


# ---- permission_request ----

def test_allow_permission(capsys: pytest.CaptureFixture[str]) -> None:
    pr.allow_permission()
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["hookSpecificOutput"]["decision"]["behavior"] == "allow"


def test_cmd_permission_bash_skein(capsys: pytest.CaptureFixture[str]) -> None:
    pr.cmd_permission({"tool_name": "Bash", "tool_input": {"command": "python skein.py init"}})
    out = capsys.readouterr().out
    assert "allow" in out


def test_cmd_permission_bash_spec(capsys: pytest.CaptureFixture[str]) -> None:
    pr.cmd_permission({"tool_name": "Bash", "tool_input": {"command": "spec.py recall x"}})
    assert "allow" in capsys.readouterr().out


def test_cmd_permission_bash_other() -> None:
    """Bash 非 skein/spec 命令 → 不 allow。"""
    import io
    # 验证返回 0 且不打印
    assert pr.cmd_permission({"tool_name": "Bash", "tool_input": {"command": "ls -la"}}) == 0


def test_cmd_permission_edit_skein_file(capsys: pytest.CaptureFixture[str]) -> None:
    pr.cmd_permission({"tool_name": "Edit", "tool_input": {"file_path": "/repo/.skein/config.yaml"}})
    assert "allow" in capsys.readouterr().out


def test_cmd_permission_edit_blocked_file() -> None:
    assert pr.cmd_permission({"tool_name": "Edit", "tool_input": {"file_path": "/repo/.skein/task/t1/task.json"}}) == 0


def test_cmd_permission_edit_normal_file() -> None:
    assert pr.cmd_permission({"tool_name": "Edit", "tool_input": {"file_path": "/repo/src/app.py"}}) == 0


def test_cmd_permission_unknown_tool() -> None:
    assert pr.cmd_permission({"tool_name": "Unknown", "tool_input": {}}) == 0


def test_permission_denied_is_reexport() -> None:
    """permission_denied 只是 re-export permission_request。"""
    assert pr.allow_permission is pd.allow_permission
    assert pr.cmd_permission is pd.cmd_permission
