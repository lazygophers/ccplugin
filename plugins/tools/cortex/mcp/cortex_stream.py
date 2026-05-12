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
_TEXT_CAP = 200
_TOOL_INPUT_CAP = 120


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="cortex-stream",
        description="rich-rendered wrapper for claude stream-json output",
    )
    parser.add_argument("--label", default="cortex", help="prefix label for status lines")
    parser.add_argument("cmd", nargs=argparse.REMAINDER, help="command to wrap (prefix with --)")
    return parser.parse_args(argv)


def _strip_separator(cmd: list[str]) -> list[str]:
    """argparse REMAINDER keeps a leading ``--``; drop it if present."""
    if cmd and cmd[0] == "--":
        return cmd[1:]
    return cmd


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
        return Text("[OK] done", style="bold green")
    return None


def _build_view(history: list[RenderableType], spinner: Spinner) -> RenderableType:
    items = history[-_HISTORY_MAX:]
    if not items:
        return spinner
    return Group(*items, spinner)


def run(cmd: list[str], label: str, tee_path: str | None,
        stderr: IO[str] | None = None) -> int:
    """Spawn ``cmd`` and render its stream-json output. Returns child exit code."""
    err_console = Console(
        file=stderr or sys.stderr,
        force_terminal=(stderr or sys.stderr).isatty(),
    )

    full_cmd = list(cmd) + ["--output-format", "stream-json", "--verbose"]

    err_console.print(f"[bold cyan][{label}][/] step 1/2: 启动 claude (stream-json 模式)")
    err_console.print(f"[bold cyan][{label}][/] step 2/2: 等待 claude 输出...")

    proc = subprocess.Popen(
        full_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    start = time.monotonic()
    tee_fp = open(tee_path, "w", encoding="utf-8") if tee_path else None
    history: list[RenderableType] = []

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
    return run(cmd, label=args.label, tee_path=tee_path)


if __name__ == "__main__":
    sys.exit(main())
