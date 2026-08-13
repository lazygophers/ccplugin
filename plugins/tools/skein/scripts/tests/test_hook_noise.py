from __future__ import annotations

import json
from typing import Any

import pytest

from skeinlib.hooks.post_tool_use_failure import cmd_report


def _payload(command: str, error: str) -> dict[str, Any]:
    return {"tool_name": "Bash", "tool_input": {"command": command}, "tool_error": error}


@pytest.mark.parametrize("command", [
    "jq . f | grep skein | wc -l",
    "rg skein plugins/",
    "ls skein",
    "echo skein",
])
def test_skein_as_search_term_is_silent(command: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert cmd_report(_payload(command, "x")) == 0
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("command", [
    "skein task create foo",
    "cd /x && skein flow run",
    "cd /x; skein-spec check",
    "make build\nskein flow run",
])
def test_real_skein_command_still_reported(command: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert cmd_report(_payload(command, "Error: Missing option --name")) == 0
    context = json.loads(capsys.readouterr().out)["hookSpecificOutput"]["additionalContext"]
    assert "SKEIN 命令被拒" in context


def test_empty_error_is_silent(capsys: pytest.CaptureFixture[str]) -> None:
    assert cmd_report(_payload("skein flow run", "")) == 0
    assert capsys.readouterr().out == ""


def test_traceback_escalates_to_issue(capsys: pytest.CaptureFixture[str]) -> None:
    error = 'Traceback (most recent call last)\n  File "x"\nValueError: boom'
    assert cmd_report(_payload("skein flow run", error)) == 0
    output = json.loads(capsys.readouterr().out)
    assert "SKEIN 脚本崩溃" in output["hookSpecificOutput"]["additionalContext"]
    assert "issues/new" in output["systemMessage"]
