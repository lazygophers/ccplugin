"""worktree 进入硬阻 — EnterWorktree 工具与 `git worktree add` 一律 deny (exit 2),
其余含 worktree 字样的只读命令放行。cmd_guard 直接调, 沿用 conftest 的 git repo fixture 风格。"""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from contextlib import redirect_stderr

from skeinlib.hooks.pre_tool_use import cmd_guard


def _guard(tool: str, **tool_input: object) -> int:
    return cmd_guard({"tool_name": tool, "tool_input": tool_input, "cwd": str(Path.cwd())})


def test_enter_worktree_tool_denied() -> None:
    with redirect_stderr(io.StringIO()) as err:
        assert _guard("EnterWorktree", path="some-wt") == 2
    assert "worktree" in err.getvalue()


def test_git_worktree_add_denied() -> None:
    with redirect_stderr(io.StringIO()):
        assert _guard("Bash", command="git worktree add ../wt1 main") == 2


def test_readonly_worktree_commands_pass() -> None:
    with redirect_stderr(io.StringIO()):
        assert _guard("Bash", command="git worktree list") == 0
        assert _guard("Bash", command="ls .worktrees") == 0
