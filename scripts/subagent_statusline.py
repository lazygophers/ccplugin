#!/usr/bin/env python3
"""Subagent 状态栏：只展示模型、代理名、上下文占用、额度、耗时。

与主状态栏（statusline.py）刻意不同：subagent 刷新频繁，这里不跑 git 和
工具版本探测，避免每次刷新都 fork 子进程。
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

# 同目录下的 statusline/ 包会遮蔽 statusline.py，所以按文件路径直接加载
_spec = importlib.util.spec_from_file_location(
    "_statusline_main", Path(__file__).resolve().parent / "statusline.py"
)
_sl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_sl)

CATPPUCCIN = _sl.CATPPUCCIN
ctx_color = _sl.ctx_color
fit_segments = _sl.fit_segments
format_compact_int = _sl.format_compact_int
format_duration_ms = _sl.format_duration_ms
get_model = _sl.get_model
get_path = _sl.get_path
progress_bar_colored = _sl.progress_bar_colored
rate_limit_segments = _sl.rate_limit_segments
read_statusline_payload = _sl.read_statusline_payload
style = _sl.style
terminal_size = _sl.terminal_size


def render_subagent_statusline(payload: dict) -> str:
    model = (
        get_path(payload, ["model", "display_name"], None)
        or get_path(payload, ["model", "id"], None)
        or get_model()
    )
    cols, _ = terminal_size()

    parts: list[str] = [style(str(model), fg=CATPPUCCIN["cyan"], bold=True)]

    agent_name = str(get_path(payload, ["agent", "name"], "") or "").strip()
    if agent_name:
        parts.append(style(agent_name, fg=CATPPUCCIN["pink"], bold=True))

    context_pct = get_path(payload, ["context_window", "used_percentage"], None)
    if context_pct is None:
        used = get_path(payload, ["context_window", "used_tokens"], 0) or 0
        max_tokens = get_path(payload, ["context_window", "max_tokens"], 0) or 0
        try:
            context_pct = (float(used) / float(max_tokens) * 100.0) if float(max_tokens) > 0 else 0.0
        except Exception:
            context_pct = 0.0
    try:
        context_pct_f = float(context_pct or 0.0)
    except Exception:
        context_pct_f = 0.0
    if context_pct_f > 0:
        bar_width = 12 if cols >= 100 else (8 if cols >= 80 else 6)
        bar_col = ctx_color(context_pct_f)
        parts.append(
            progress_bar_colored(context_pct_f, width=bar_width, filled_fg=bar_col)
            + style(f" {context_pct_f:.0f}%", fg=bar_col, bold=True)
        )

    total_in = get_path(payload, ["context_window", "total_input_tokens"], None)
    total_out = get_path(payload, ["context_window", "total_output_tokens"], None)
    if total_in is not None or total_out is not None:
        try:
            total_tokens = int(total_in or 0) + int(total_out or 0)
        except Exception:
            total_tokens = 0
        if total_tokens > 0:
            parts.append(style(format_compact_int(total_tokens), fg=CATPPUCCIN["text"], bold=False))

    parts.extend(rate_limit_segments(payload, cols=cols))

    duration_ms = get_path(payload, ["cost", "total_duration_ms"], None)
    if duration_ms is not None:
        parts.append(style(format_duration_ms(duration_ms), fg=CATPPUCCIN["subtle"], dim=True))

    sep = style(" · ", fg=CATPPUCCIN["subtle"], dim=True)
    return fit_segments(parts, sep=sep, max_width=cols)


def main() -> None:
    payload = read_statusline_payload()
    print(render_subagent_statusline(payload))


if __name__ == "__main__":
    main()
