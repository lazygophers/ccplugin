#!/usr/bin/env python3
"""cortex_stream — rich-rendered wrapper for `claude --bare -p` stream-json.

Phase A of cortex stream-progress upgrade: replaces jq filter + bash
heartbeat with a Python+rich Live region. Designed as a pipx console-script
(`cortex-stream`) so the rich dependency resolves through the cortex-mcp venv.

CLI:
    cortex-stream --label <label> -- <claude cmd...>

The script appends `--output-format stream-json --verbose` to the inner
command, spawns it line-buffered, and renders each NDJSON event into a
rolling history of rich renderables under a spinner heartbeat. Raw NDJSON
is teed to stdout (so callers like run.sh can still grep the result line),
and optionally mirrored to ``$CORTEX_STREAM_TEE_FILE``.

Non-tty stderr (cron / pipe) auto-degrades thanks to rich.Console's
force_terminal detection — heartbeat updates collapse into plain lines.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from typing import IO

from rich.console import Console, Group, RenderableType
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.text import Text

# Rolling history window — keeps Live region bounded so long runs don't scroll
# off useful context. Full NDJSON still lands in the tee file for post-mortem.
_HISTORY_MAX = 5
# Caps放宽: 用户要看完整 thinking/text/tool input, 仅留防爆上限.
_TEXT_CAP = 2000
_TOOL_INPUT_CAP = 800
_THINK_CAP = 4000

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="cortex-stream",
        description="rich-rendered wrapper for claude stream-json output",
    )
    parser.add_argument("--label", default="cortex", help="prefix label for status lines")
    parser.add_argument(
        "--timeout",
        type=int,
        default=0,
        help="seconds; 0 disables (default). On expiry SIGKILL child + return 124.",
    )
    parser.add_argument("cmd", nargs=argparse.REMAINDER, help="command to wrap (prefix with --)")
    return parser.parse_args(argv)


def _strip_separator(cmd: list[str]) -> list[str]:
    """argparse REMAINDER keeps a leading ``--``; drop it if present."""
    if cmd and cmd[0] == "--":
        return cmd[1:]
    return cmd


# 已知 boolean flags (不带 value), 用于 _extract_prompts 区分 flag VALUE vs flag positional.
_BOOL_FLAGS = frozenset({
    "--bare", "--verbose", "--debug", "--help", "-h", "--version",
})
# 已知带 value 的长 flag — 显式列出避免误判.
_VALUE_FLAGS = frozenset({
    "--append-system-prompt", "--system-prompt", "--output-format",
    "--model", "--max-turns", "--allowed-tools", "--disallowed-tools",
    "--input-format", "--mcp-config", "--permission-mode",
    "--add-dir", "--resume", "--session-id",
})


def _extract_prompts(cmd: list[str]) -> tuple[str | None, str | None]:
    """Return (system_prompt, user_prompt) parsed from claude CLI args.

    Heuristics:
    - --append-system-prompt VALUE / --system-prompt VALUE → system_prompt
    - 末尾非 flag 的 positional 参数 → user_prompt (跳过 cmd[0] 可执行)
    - 已知 boolean flag (--bare/--verbose 等) 不吞下一参数; 已知 value flag 吞下一参数.
    - 未知长 flag 默认按 boolean 处理 (保守, 避免误吞 user prompt).
    - 短 flag (-p) 视为 boolean.
    """
    system_prompt: str | None = None
    positionals: list[str] = []
    i = 0
    n = len(cmd)
    while i < n:
        arg = cmd[i]
        if arg in ("--append-system-prompt", "--system-prompt"):
            if i + 1 < n:
                system_prompt = cmd[i + 1]
                i += 2
                continue
            i += 1
            continue
        if arg in _VALUE_FLAGS:
            # consume next as value
            i += 2 if i + 1 < n else 1
            continue
        if arg in _BOOL_FLAGS:
            i += 1
            continue
        if arg.startswith("--") or (arg.startswith("-") and len(arg) > 1):
            # 未知 flag → 保守按 boolean 处理.
            i += 1
            continue
        positionals.append(arg)
        i += 1
    # cmd[0] (claude 可执行) 是首个 positional, 不算 user prompt; 末尾为 user prompt.
    if len(positionals) >= 2:
        return system_prompt, positionals[-1]
    if len(positionals) == 1:
        first = positionals[0]
        # 单一 positional 若看起来像可执行路径, 不当 user prompt.
        if first == "claude" or "/" in first:
            return system_prompt, None
        return system_prompt, first
    return system_prompt, None


def _extract_skill_name(system_prompt: str | None) -> str | None:
    """Parse YAML frontmatter from system prompt, return `name:` value."""
    if not system_prompt:
        return None
    m = _FRONTMATTER_RE.match(system_prompt.lstrip())
    if not m:
        return None
    for line in m.group(1).splitlines():
        line = line.strip()
        if line.startswith("name:"):
            val = line.split(":", 1)[1].strip()
            return val.strip("\"'") or None
    return None


def _render_event(evt: dict) -> RenderableType | None:
    """Map one stream-json event to a rich renderable. Unknown → None."""
    etype = evt.get("type")
    if etype == "assistant":
        msg = evt.get("message", {}) or {}
        renderables: list[RenderableType] = []
        for blk in msg.get("content", []) or []:
            btype = blk.get("type")
            if btype == "text":
                txt = (blk.get("text") or "").lstrip("\n")[:_TEXT_CAP]
                if txt:
                    renderables.append(Text(f"[text] {txt}", style="green"))
            elif btype == "thinking":
                th = (blk.get("thinking") or "").strip()[:_THINK_CAP]
                if th:
                    renderables.append(Text(f"[thinking] {th}", style="dim italic"))
            elif btype == "tool_use":
                name = blk.get("name", "?")
                inp = json.dumps(blk.get("input", {}), ensure_ascii=False)[:_TOOL_INPUT_CAP]
                renderables.append(
                    Panel(
                        Text(inp, style="yellow"),
                        title=f"tool: {name}",
                        border_style="yellow",
                        padding=(0, 1),
                    )
                )
        if not renderables:
            return None
        if len(renderables) == 1:
            return renderables[0]
        return Group(*renderables)
    if etype == "result":
        if evt.get("is_error"):
            msg = (evt.get("result") or "unknown error")[:_TEXT_CAP]
            return Text(f"[FAILED] {msg}", style="bold red")
        msg = (evt.get("result") or "").strip()
        if msg:
            return Text(f"[OK] {msg[:_TEXT_CAP]}", style="bold green")
        return Text("[OK] done", style="bold green")
    return None


def _build_view(history: list[RenderableType], spinner: Spinner) -> RenderableType:
    items = history[-_HISTORY_MAX:]
    if not items:
        return spinner
    return Group(*items, spinner)


def _print_prompts(console: Console, cmd: list[str]) -> None:
    """Render system + user prompts (if extractable) before streaming starts."""
    sys_p, user_p = _extract_prompts(cmd)
    if sys_p:
        skill_name = _extract_skill_name(sys_p)
        title = f"system prompt [skill: {skill_name}]" if skill_name else "system prompt"
        head = sys_p.strip().split("\n", 1)[0][:200]
        suffix = "..." if len(sys_p) > 200 else ""
        body = Text(f"{head}{suffix}\n[{len(sys_p)} chars]", style="cyan")
        console.print(Panel(body, title=title, border_style="cyan", padding=(0, 1)))
    if user_p:
        console.print(Panel(
            Text(user_p[:_TEXT_CAP], style="white"),
            title="prompt", border_style="magenta", padding=(0, 1),
        ))


def run(cmd: list[str], label: str, tee_path: str | None,
        stderr: IO[str] | None = None, timeout: int = 0) -> int:
    """Spawn ``cmd`` and render its stream-json output. Returns child exit code.

    If ``timeout`` > 0, the child is SIGKILLed after the deadline elapses and
    124 is returned (matching GNU ``timeout(1)``). ``timeout`` is enforced via
    per-line deadline checks during the stdout read loop; precision is bounded
    by claude --verbose output cadence (sub-second in practice).
    """
    err_console = Console(
        file=stderr or sys.stderr,
        force_terminal=(stderr or sys.stderr).isatty(),
    )

    full_cmd = list(cmd) + ["--output-format", "stream-json", "--verbose"]

    err_console.print(f"[bold cyan][{label}][/] step 1/2: 启动 claude (stream-json 模式)")
    err_console.print(f"[bold cyan][{label}][/] step 2/2: 等待 claude 输出...")

    _print_prompts(err_console, full_cmd)

    proc = subprocess.Popen(
        full_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    start = time.monotonic()
    deadline = start + timeout if timeout > 0 else None
    tee_fp = open(tee_path, "w", encoding="utf-8") if tee_path else None
    history: list[RenderableType] = []
    timed_out = False

    def make_spinner() -> Spinner:
        elapsed = int(time.monotonic() - start)
        return Spinner("dots", text=Text(f"still working... ({elapsed}s elapsed)", style="dim"))

    try:
        with Live(
            _build_view(history, make_spinner()),
            console=err_console,
            refresh_per_second=4,
            transient=False,
        ) as live:
            assert proc.stdout is not None
            for raw in proc.stdout:
                if deadline is not None and time.monotonic() > deadline:
                    timed_out = True
                    break
                line = raw.rstrip("\n")
                if not line:
                    continue

                # Tee raw NDJSON to file (if requested) + stdout passthrough so
                # downstream (run.sh) can still parse the trailing result line.
                if tee_fp:
                    tee_fp.write(line + "\n")
                    tee_fp.flush()
                sys.stdout.write(line + "\n")
                sys.stdout.flush()

                try:
                    evt = json.loads(line)
                except json.JSONDecodeError:
                    continue

                rendered = _render_event(evt)
                if rendered is not None:
                    history.append(rendered)

                live.update(_build_view(history, make_spinner()))
    finally:
        if tee_fp:
            tee_fp.close()

    if timed_out:
        # SIGKILL + reap to avoid zombies. Live region already exited via `with`.
        proc.kill()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        err_console.print(f"[bold red][{label}] TIMEOUT after {timeout}s[/]")
        return 124

    rc = proc.wait()
    if rc == 0:
        err_console.print(f"[bold green][{label}] OK[/]")
    else:
        err_console.print(f"[bold red][{label}] FAILED: exit code {rc}[/]")
    return rc


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cmd = _strip_separator(list(args.cmd or []))
    if not cmd:
        print("cortex-stream: missing command (use `-- <cmd...>`)", file=sys.stderr)
        return 4

    tee_path = os.environ.get("CORTEX_STREAM_TEE_FILE") or None
    return run(cmd, label=args.label, tee_path=tee_path, timeout=args.timeout)


if __name__ == "__main__":
    sys.exit(main())
