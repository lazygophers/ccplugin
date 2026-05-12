#!/usr/bin/env python3
"""cortex_stream — rich-rendered wrapper for `claude -p` stream-json.

Sequential stderr rendering (no Live region, no height cap, no refresh
throttling) — each parsed event is printed in order as it streams in.

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
from rich.panel import Panel
from rich.text import Text

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


def _render_raw(evt: dict) -> RenderableType:
    """未适配 event 显原 JSON 1 行 (cap 250 chars)."""
    raw = json.dumps(evt, ensure_ascii=False)
    if len(raw) > 250:
        raw = raw[:247] + "..."
    return Text(f"[raw] {raw}", style="dim white")


def _render_system_event(evt: dict) -> RenderableType | None:
    """Render claude stream-json `system` events (init/hook/task/api_retry/plugin_install).

    Unknown subtypes return None — caller (_render_event) fallbacks to raw JSON.
    """
    sub = evt.get("subtype")
    if sub == "init":
        model = evt.get("model", "?")
        tools = len(evt.get("tools", []) or [])
        mcp_n = sum(
            1 for s in (evt.get("mcp_servers", []) or [])
            if s.get("status") == "connected"
        )
        plugins_n = len(evt.get("plugins", []) or [])
        return Panel(
            Text(
                f"model={model} · tools={tools} · mcp={mcp_n} · plugins={plugins_n}",
                style="dim",
            ),
            title="▸ claude 启动",
            border_style="dim",
            padding=(0, 1),
        )
    if sub == "hook_started":
        name = evt.get("hook_name", "?")
        event_name = evt.get("hook_event", "")
        suffix = f" ({event_name})" if event_name else ""
        return Text(f"  ▸ hook {name}{suffix}", style="dim")
    if sub == "hook_response":
        name = evt.get("hook_name", "?")
        exit_code = evt.get("exit_code", 0)
        outcome = evt.get("outcome", "")
        if exit_code == 0 and outcome in ("", "success"):
            return Text(f"  ✓ hook {name}", style="dim green")
        suffix = f" (exit={exit_code}{', ' + outcome if outcome else ''})"
        return Text(f"  ✗ hook {name}{suffix}", style="red")
    if sub == "task_started":
        desc = evt.get("description") or evt.get("task") or "?"
        return Text(f"  ▸ task {desc}", style="dim cyan")
    if sub == "task_notification":
        desc = evt.get("description") or evt.get("task") or "?"
        status = evt.get("status", "")
        suffix = f" ({status})" if status else ""
        return Text(f"  ✓ task {desc}{suffix}", style="dim green")
    if sub == "api_retry":
        attempt = evt.get("attempt", "?")
        max_retries = evt.get("max_retries", "?")
        delay = evt.get("retry_delay_ms", "?")
        err = evt.get("error", "")
        suffix = f": {err}" if err else ""
        return Text(
            f"  ⟳ api retry {attempt}/{max_retries}, in {delay}ms{suffix}",
            style="yellow",
        )
    if sub == "plugin_install":
        status = evt.get("status", "")
        name = evt.get("name", "?")
        err = evt.get("error", "")
        style = "red" if err else "dim"
        suffix = f" — {err}" if err else ""
        return Text(f"  ▸ plugin {name} {status}{suffix}", style=style)
    if sub == "compact_boundary":
        trigger = evt.get("trigger") or evt.get("compact_metadata", {}).get("trigger", "")
        suffix = f" ({trigger})" if trigger else ""
        return Text(f"  ⊟ compact_boundary{suffix}", style="dim magenta")
    if sub == "error":
        msg = evt.get("error") or evt.get("message") or "?"
        return Text(f"  ✗ system error: {msg}"[:300], style="red")
    if sub in {
        "tool_permission_request",
        "tool_permission_response",
        "tool_use_started",
        "tool_use_completed",
        "subagent_started",
        "subagent_stopped",
        "session_resumed",
        "session_compacted",
    }:
        name = evt.get("tool_name") or evt.get("subagent_type") or evt.get("name") or ""
        status = evt.get("status") or evt.get("decision") or ""
        bits = " ".join(b for b in (name, status) if b)
        return Text(f"  · {sub} {bits}".rstrip(), style="dim")
    return None


def _render_user_event(evt: dict) -> RenderableType | None:
    """Render `user` event tool_result blocks (truncated). Other shapes → None."""
    msg = evt.get("message", {}) or {}
    content = msg.get("content", []) or []
    for item in content:
        itype = item.get("type")
        if itype == "tool_use":
            name = item.get("name", "?")
            return Text(f"  ▸ user tool_use: {name}", style="dim yellow")
        if itype != "tool_result":
            continue
        raw = item.get("content", "")
        # tool_result.content can be string OR list of {type:text, text:...} blocks.
        if isinstance(raw, list):
            parts: list[str] = []
            for blk in raw:
                if isinstance(blk, dict) and blk.get("type") == "text":
                    parts.append(str(blk.get("text", "")))
                else:
                    parts.append(str(blk))
            text = "\n".join(parts)
        else:
            text = str(raw)
        is_error = bool(item.get("is_error", False))
        cap = 500
        truncated = len(text) > cap
        preview = text[:cap] + ("...(truncated)" if truncated else "")
        style = "red" if is_error else "dim"
        title = "↩ tool_result (error)" if is_error else "↩ tool_result"
        return Panel(
            Text(preview, style=style),
            title=title,
            border_style=style,
            padding=(0, 1),
        )
    return None


def _render_event(evt: dict) -> RenderableType | None:
    """Map one stream-json event to a rich renderable.

    Policy (PRD): 已适配 type 渲染 rich, 未适配 type/subtype 默认显原 JSON 1 行.
    仅 stream_event 静默 (主流 assistant.text 已渲, 避免重复).
    """
    etype = evt.get("type")
    if etype == "system":
        rendered = _render_system_event(evt)
        return rendered if rendered is not None else _render_raw(evt)
    if etype == "user":
        rendered = _render_user_event(evt)
        return rendered if rendered is not None else _render_raw(evt)
    if etype == "stream_event":
        # 增量 text_delta 等 — 主流由 assistant.text 渲, 此处静默避重复.
        return None
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
            elif btype == "server_tool_use":
                name = blk.get("name", "?")
                inp = json.dumps(blk.get("input", {}), ensure_ascii=False)[:_TOOL_INPUT_CAP]
                renderables.append(
                    Panel(
                        Text(inp, style="cyan"),
                        title=f"server_tool: {name}",
                        border_style="cyan",
                        padding=(0, 1),
                    )
                )
            elif btype == "web_search_tool_result":
                tu_id = blk.get("tool_use_id", "?")
                content = blk.get("content", [])
                n = len(content) if isinstance(content, list) else 1
                renderables.append(
                    Text(f"  ↩ web_search_result ({n} hits) tool_use_id={tu_id[:12]}", style="dim cyan")
                )
            elif btype == "redacted_thinking":
                renderables.append(Text("[thinking redacted]", style="dim italic"))
        if not renderables:
            return None
        if len(renderables) == 1:
            return renderables[0]
        return Group(*renderables)
    if etype == "result":
        sub = evt.get("subtype", "")
        if evt.get("is_error") or sub in {"error_max_turns", "error_during_execution"}:
            msg = (evt.get("result") or evt.get("error") or f"unknown error ({sub})")[:_TEXT_CAP]
            return Text(f"[FAILED:{sub or 'error'}] {msg}", style="bold red")
        msg = (evt.get("result") or "").strip()
        if msg:
            return Text(f"[OK] {msg[:_TEXT_CAP]}", style="bold green")
        return Text("[OK] done", style="bold green")
    # 完全未知 type — 显原 JSON 1 行.
    return _render_raw(evt)


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
    timed_out = False

    try:
        assert proc.stdout is not None
        for raw in proc.stdout:
            if deadline is not None and time.monotonic() > deadline:
                timed_out = True
                break
            line = raw.rstrip("\n")
            if not line:
                continue

            # Tee raw NDJSON to file (if requested) — raw NEVER hits stdout
            # to prevent terminal leakage. Stdout receives only final result.text.
            if tee_fp:
                tee_fp.write(line + "\n")
                tee_fp.flush()

            try:
                evt = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Final result.text → stdout (single line, no NDJSON wrapper).
            # Caller (run.sh / lint.sh / etc.) consumes plain text directly.
            if evt.get("type") == "result" and not evt.get("is_error"):
                txt = (evt.get("result") or "").rstrip()
                if txt:
                    sys.stdout.write(txt + "\n")
                    sys.stdout.flush()

            # Sequential render to stderr — no Live region, no height cap, no refresh.
            rendered = _render_event(evt)
            if rendered is not None:
                err_console.print(rendered)
    finally:
        if tee_fp:
            tee_fp.close()

    if timed_out:
        # SIGKILL + reap to avoid zombies.
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
