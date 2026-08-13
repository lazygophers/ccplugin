"""hooks/cli.py + hooks/__init__.py 覆盖。
"""
from __future__ import annotations

import io
import json
import sys
from typing import Any

import pytest

from skeinlib.hooks import cli as hooks_cli
from skeinlib.hooks import _run_hooks, _prefix_lines, DISPATCH, _ARGV_DISPATCH
from skeinlib.hooks.cli import _resolve, main, self_check


# ---- hooks/cli.py ----

def test_resolve_guard() -> None:
    fn = _resolve("guard")
    assert callable(fn)


def test_resolve_fmt() -> None:
    fn = _resolve("fmt")
    assert callable(fn)


def test_main_no_args(capsys: pytest.CaptureFixture[str],
                      monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["hooks.py"])
    assert main() == 2
    assert "用法" in capsys.readouterr().err


def test_main_unknown_command(capsys: pytest.CaptureFixture[str],
                              monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["hooks.py", "bogus"])
    assert main() == 2


def test_main_argv_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    """agent-start/agent-stop 走 _ARGV_DISPATCH 路径。"""
    monkeypatch.setattr("sys.argv", ["hooks.py", "agent-start"])
    # agent-start 需要 import agent module — mock 它
    import skeinlib.hooks.agent as agent_mod
    called: list[str] = []
    def _hook(agent_type: str) -> int:
        called.append(agent_type)
        return 0
    monkeypatch.setattr(agent_mod, "cmd_agent_hook", _hook)
    result = main()
    assert result == 0
    assert called == ["start"]


def test_main_stdin_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    """stdin payload 命令走正常路径。"""
    monkeypatch.setattr("sys.argv", ["hooks.py", "guard"])
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}})))
    result = main()
    assert result in (0, 2)  # cmd_guard 可能返回 0 或 2


def test_main_stdin_bad_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["hooks.py", "guard"])
    monkeypatch.setattr("sys.stdin", io.StringIO("not json"))
    # bad json → load_stdin returns None → main returns 0
    assert main() == 0


def test_self_check() -> None:
    """self_check 跑 judge_signal 测试用例，返回 0 或 1。"""
    result = self_check()
    assert result in (0, 1)


# ---- hooks/__init__.py ----

def test_prefix_lines_function() -> None:
    from skeinlib.hooks import prefix_lines as pl
    assert pl(">>", "a\nb") == ">> a\n>> b\n"


def test_prefix_lines_internal() -> None:
    assert _prefix_lines("X", "hello") == "X hello\n"


def test_run_hooks_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    _run_hooks("create", "before", {"hooks": []})


def test_run_hooks_skein_in_hook_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKEIN_IN_HOOK", "1")
    _run_hooks("create", "before", {"hooks": [{"command": "echo hi"}]})  # 应跳过


def test_run_hooks_executes_command(monkeypatch: pytest.MonkeyPatch,
                                    capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.delenv("SKEIN_IN_HOOK", raising=False)
    _run_hooks("create", "after", {"hooks": [{"command": "echo hello-world"}]})
    out = capsys.readouterr().out
    assert "hello-world" in out


def test_run_hooks_blocking_before_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    from skeinlib.hooks import HookBlocked
    monkeypatch.delenv("SKEIN_IN_HOOK", raising=False)
    with pytest.raises(HookBlocked, match="失败"):
        _run_hooks("create", "before", {"hooks": [{"command": "exit 1"}]})


def test_run_hooks_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    import subprocess as sp_module
    monkeypatch.delenv("SKEIN_IN_HOOK", raising=False)

    def fake_run(cmd: str, **kw: Any) -> Any:
        raise sp_module.TimeoutExpired(cmd, 1)

    monkeypatch.setattr(sp_module, "run", fake_run)
    _run_hooks("create", "after", {"hooks": [{"command": "sleep 999", "timeout": 1}]})


def test_getattr_load_stdin() -> None:
    """__getattr__ 懒加载 load_stdin。"""
    from skeinlib.hooks import load_stdin
    assert callable(load_stdin)


def test_getattr_git_root() -> None:
    from skeinlib.hooks import git_root
    assert callable(git_root)
