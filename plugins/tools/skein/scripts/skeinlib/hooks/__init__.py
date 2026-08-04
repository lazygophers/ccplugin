from __future__ import annotations

import fnmatch
import importlib
import json
import os
import sys
from typing import Any, Callable, Optional, cast

DISPATCH: dict[str, str] = {
    "permission": "permission_request:cmd_permission",
    "guard": "pre_tool_use:cmd_guard",
    "batch": "post_tool_batch:cmd_batch",
    "report": "post_tool_use_failure:cmd_report",
    "fmt": "post_tool_use:cmd_fmt",
    "spec-meta": "post_tool_use:cmd_spec_meta",
    "flow-gate": "post_tool_use:cmd_flow_gate",
    "stop-check": "stop:cmd_stop_check",
    "user-prompt": "user_prompt_submit:cmd_user_prompt",
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


def debug_enabled(args: Any = None) -> bool:
    if args is not None and getattr(args, "debug", False):
        return True
    return os.environ.get("SKEIN_DEBUG", "").strip().lower() not in ("", "0", "false", "no")


class Debug:
    def __init__(self, enabled: bool) -> None:
        self.enabled = False
        self.c: Optional[Any] = None
        self.enable(enabled)

    def enable(self, on: bool) -> None:
        self.enabled = on
        if on and self.c is None:
            try:
                from rich.console import Console
                self.c = Console(stderr=True)
            except Exception:
                self.c = None

    def log(self, message: str, style: Optional[str] = None) -> None:
        if self.enabled:
            self._emit(message, style)

    def warn(self, message: str) -> None:
        self._emit(message, "yellow")

    def error(self, message: str) -> None:
        self._emit(message, "red")

    def _emit(self, message: str, style: Optional[str] = None) -> None:
        if self.c is None:
            try:
                from rich.console import Console
                self.c = Console(stderr=True)
            except Exception:
                pass
        if self.c:
            self.c.print(message, style=style, markup=False, highlight=False)
        else:
            sys.stderr.write(f"{message}\n")

    def rule(self, title: str) -> None:
        if not self.enabled:
            return
        if self.c:
            self.c.rule(f"[bold cyan]{title}")
        else:
            sys.stderr.write(f"\n──── {title} ────\n")

    def kv(self, mapping: dict[str, Any], title: Optional[str] = None) -> None:
        if not self.enabled or not mapping:
            return
        if self.c:
            from rich.table import Table
            table = Table(show_header=False, box=None, title=title, title_justify="left", title_style="dim")
            table.add_column(style="cyan", no_wrap=True)
            table.add_column(overflow="fold")
            for key, value in mapping.items():
                table.add_row(str(key), str(value))
            self.c.print(table)
        else:
            if title:
                sys.stderr.write(f"{title}\n")
            for key, value in mapping.items():
                sys.stderr.write(f"  {key}: {value}\n")


DBG = Debug(False)


def est_tokens(text: str) -> int:
    return len(text) // 4


def budget_guard(text: str, budget_tokens: int, label: str) -> str:
    tokens = est_tokens(text)
    if tokens <= budget_tokens:
        return text
    sys.stderr.write(
        f"[skein hook:{label}] 注入内容 ~{tokens} token > 预算 {budget_tokens} — "
        f"请简化 (core 规则降级 recall / 精简正文), 已硬截断到 {budget_tokens} token\n")
    return text[:budget_tokens * 4] + "\n\n… (超预算已截断, 见 stderr)"


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
