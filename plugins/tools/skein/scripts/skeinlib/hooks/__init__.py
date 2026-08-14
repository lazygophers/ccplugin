from __future__ import annotations

import fnmatch
import importlib
import json
import os
import sys
from typing import Any, Callable, Optional, cast

# debug 基础设施从本文件抽到 skeinlib/utils/debug.py (ADR 0003 S2)。
# 此处 re-export: hooks 子模块仍可 `from skeinlib.hooks import DBG`。
from skeinlib.utils.debug import DBG, Debug, budget_guard, debug_enabled, est_tokens

# 显式 re-export: 子模块 `from skeinlib.hooks import DBG` 要走这里 (mypy --strict 认 __all__)
__all__ = ["DBG", "Debug", "budget_guard", "debug_enabled", "est_tokens",
           "HookBlocked", "DISPATCH", "git_root", "_prefix_lines", "_run_hooks"]

DISPATCH: dict[str, str] = {
    "permission": "permission_request:cmd_permission",
    "guard": "pre_tool_use:cmd_guard",
    "report": "post_tool_use_failure:cmd_report",
    "fmt": "post_tool_use:cmd_fmt",
    "spec-meta": "post_tool_use:cmd_spec_meta",
    "stop-check": "stop:cmd_stop_check",
    "user-prompt": "user_prompt_submit:cmd_user_prompt",
    "session-start": "session_start:cmd_session_start",
    "agent-start": "agent:cmd_agent_hook",
    "agent-stop": "agent:cmd_agent_hook",
}
_ARGV_DISPATCH = {"agent-start", "agent-stop"}


def git_root(start: str) -> str:
    directory = os.path.abspath(start or ".")
    while True:
        if os.path.isdir(os.path.join(directory, ".git")):
            return directory
        parent = os.path.dirname(directory)
        if parent == directory:
            return os.path.abspath(start or ".")
        directory = parent


def load_stdin() -> Optional[dict[str, Any]]:
    try:
        return cast(dict[str, Any], json.load(sys.stdin))
    except (json.JSONDecodeError, ValueError):
        return None


class HookBlocked(RuntimeError):
    pass


def prefix_lines(tag: str, text: str) -> str:
    return "".join(f"{tag} {line}\n" for line in text.splitlines())


def _prefix_lines(tag: str, text: str) -> str:
    return prefix_lines(tag, text)


def _run_hooks(scope: str, when: str, context: dict[str, Any]) -> None:
    hooks = context.get("hooks") or []
    if not hooks or os.environ.get("SKEIN_IN_HOOK"):
        return
    blocking = scope != "agent" and when == "before"
    cwd_default = context.get("worktree") or context.get("repo_root") or "."
    env = dict(os.environ)
    env.update({
        "SKEIN_SCOPE": scope, "SKEIN_WHEN": when,
        "SKEIN_AGENT": context.get("agent", ""),
        "SKEIN_TID": context.get("tid", ""), "SKEIN_SID": context.get("sid", ""),
        "SKEIN_TASK_DIR": context.get("task_dir", ""),
        "SKEIN_WORKTREE": context.get("worktree", ""),
        "SKEIN_REPO_ROOT": context.get("repo_root", ""),
        "SKEIN_IN_HOOK": "1",
    })
    import subprocess
    for index, hook in enumerate(hooks, 1):
        tag = f"[hook {scope}.{when}#{index}]"
        timeout = hook.get("timeout", 60)
        continue_on_error = hook.get("continue_on_error", when != "before")
        try:
            result = subprocess.run(hook.get("command", ""), shell=True, cwd=hook.get("cwd") or cwd_default, env=env,
                                    capture_output=True, text=True, timeout=timeout)
            if result.stdout:
                sys.stdout.write(prefix_lines(tag, result.stdout))
            if result.stderr:
                sys.stderr.write(prefix_lines(tag, result.stderr))
            ok, detail = result.returncode == 0, f"exit {result.returncode}"
        except subprocess.TimeoutExpired:
            ok, detail = False, f"超时(>{timeout}s)"
            sys.stderr.write(f"{tag} {detail}\n")
        if ok:
            continue
        if continue_on_error:
            sys.stderr.write(f"{tag} 失败({detail}), continue_on_error=true, 继续\n")
            continue
        message = f"{tag} 失败({detail}), 串行执行终止"
        if blocking:
            raise HookBlocked(message)
        sys.stderr.write(f"{message} (仅告警, 不阻断)\n")
        return


def __getattr__(name: str) -> Any:
    if name == "MAINTAIN_POLICY":
        return importlib.import_module("skeinlib.spec.model").MAINTAIN_POLICY
    raise AttributeError(name)
