#!/usr/bin/env python3
"""Sub-agent status line — render per-task rows for Claude Code agent panel.

Spec: https://code.claude.com/docs/zh-CN/statusline#子代理状态行

stdin: JSON {columns, tasks: [{id, name, type, status, description, label,
                              startTime, tokenCount, tokenSamples, cwd}]}
stdout: one JSON line per task to override:
        {"id": "<task id>", "content": "<row body>"}
        omit id → default row; empty content → hide row.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")

CATPPUCCIN = {
	"text": (205, 214, 244),
	"subtle": (108, 112, 134),
	"cyan": (137, 220, 235),
	"blue": (137, 180, 250),
	"mauve": (203, 166, 247),
	"green": (166, 227, 161),
	"yellow": (249, 226, 175),
	"red": (243, 139, 168),
	"pink": (245, 194, 231),
}


def _colors_enabled() -> bool:
	if os.environ.get("STATUSLINE_NO_COLOR"):
		return False
	if os.environ.get("NO_COLOR") is not None:
		return False
	if os.environ.get("TERM", "").lower() == "dumb":
		return False
	return True


def _emoji_enabled() -> bool:
	if os.environ.get("STATUSLINE_NO_EMOJI"):
		return False
	if os.environ.get("NO_EMOJI") is not None:
		return False
	if os.environ.get("TERM", "").lower() == "dumb":
		return False
	return True


def _style(text: str, *, fg=None, bold=False, dim=False) -> str:
	if not _colors_enabled():
		return text
	seq = ""
	if bold:
		seq += "\x1b[1m"
	if dim:
		seq += "\x1b[2m"
	if fg is not None:
		r, g, b = fg
		seq += f"\x1b[38;2;{r};{g};{b}m"
	return f"{seq}{text}\x1b[0m"


def _strip_ansi(s: str) -> str:
	return ANSI_ESCAPE_RE.sub("", s or "")


def _visible_len(s: str) -> int:
	return len(_strip_ansi(s))


def _truncate(s: str, max_len: int) -> str:
	if max_len <= 0:
		return ""
	if _visible_len(s) <= max_len:
		return s
	if max_len <= 1:
		return "…"
	plain = _strip_ansi(s)
	return plain[: max_len - 1] + "…"


def _format_compact_int(n) -> str:
	try:
		n = int(n)
	except Exception:
		return "0"
	if n >= 1_000_000:
		return f"{n / 1_000_000:.2f}M"
	if n >= 10_000:
		return f"{n / 1_000:.0f}K"
	if n >= 1_000:
		return f"{n / 1_000:.1f}K"
	return str(n)


def _format_duration(seconds: float) -> str:
	try:
		s = max(0, int(seconds))
	except Exception:
		return ""
	if s >= 3600:
		return f"·{s // 3600}h{(s % 3600) // 60:02d}m"
	if s >= 60:
		return f"·{s // 60}m{s % 60:02d}s"
	return f"·{s}s"


# status → (symbol, color) — 纯几何符号, 非 emoji
_STATUS_MAP = {
	"running": ("●", CATPPUCCIN["yellow"]),
	"in_progress": ("●", CATPPUCCIN["yellow"]),
	"pending": ("○", CATPPUCCIN["subtle"]),
	"queued": ("○", CATPPUCCIN["subtle"]),
	"completed": ("●", CATPPUCCIN["green"]),
	"succeeded": ("●", CATPPUCCIN["green"]),
	"success": ("●", CATPPUCCIN["green"]),
	"failed": ("●", CATPPUCCIN["red"]),
	"error": ("●", CATPPUCCIN["red"]),
	"cancelled": ("◌", CATPPUCCIN["subtle"]),
	"canceled": ("◌", CATPPUCCIN["subtle"]),
}


def _status_seg(status: str) -> str:
	s = (status or "").strip().lower()
	symbol, color = _STATUS_MAP.get(s, ("◆", CATPPUCCIN["blue"]))
	return _style(f"·{symbol}", fg=color, bold=True)


def _parse_start_time(raw) -> float | None:
	if raw is None:
		return None
	try:
		# epoch seconds (float / int) or ms
		v = float(raw)
		if v > 10_000_000_000:  # ms
			v /= 1000.0
		return v
	except Exception:
		pass
	try:
		# ISO 8601
		s = str(raw).strip().rstrip("Z")
		if "T" in s or "-" in s:
			import datetime as _dt

			return _dt.datetime.fromisoformat(s).timestamp()
	except Exception:
		pass
	return None


def _token_rate(samples) -> float | None:
	"""Estimate tokens/sec from samples if available."""
	if not isinstance(samples, list) or len(samples) < 2:
		return None
	try:
		first, last = samples[0], samples[-1]
		t0 = float(first.get("time") or first.get("t") or first.get("timestamp") or 0)
		t1 = float(last.get("time") or last.get("t") or last.get("timestamp") or 0)
		c0 = float(first.get("tokens") or first.get("count") or 0)
		c1 = float(last.get("tokens") or last.get("count") or 0)
		if t0 > 10_000_000_000:
			t0 /= 1000.0
		if t1 > 10_000_000_000:
			t1 /= 1000.0
		dt = t1 - t0
		dc = c1 - c0
		if dt > 0 and dc > 0:
			return dc / dt
	except Exception:
		return None
	return None


def _ctx_color(pct: float):
	try:
		p = float(pct)
	except Exception:
		p = 0.0
	if p > 90:
		return CATPPUCCIN["red"]
	if p > 75:
		return CATPPUCCIN["yellow"]
	return CATPPUCCIN["green"]


def _extract_ctx_pct(task: dict, top_ctx: dict | None) -> float | None:
	"""优先级:
	1. task.context_window.used_percentage
	2. top-level context_window.used_percentage
	3. 由 task.tokenCount / (top_ctx.context_window_size or 200000) 估算
	"""
	for src in (task.get("context_window"), top_ctx):
		if isinstance(src, dict):
			v = src.get("used_percentage")
			if v is None:
				try:
					used = float(src.get("total_input_tokens") or 0)
					size = float(src.get("context_window_size") or 0)
					if size > 0:
						v = used / size * 100.0
				except Exception:
					v = None
			if v is not None:
				try:
					return float(v)
				except Exception:
					pass
	# fallback: tokenCount / context_window_size
	try:
		tok = float(task.get("tokenCount") or 0)
		size = 0.0
		if isinstance(top_ctx, dict):
			size = float(top_ctx.get("context_window_size") or 0)
		if size <= 0:
			size = 200000.0
		if tok > 0:
			return tok / size * 100.0
	except Exception:
		pass
	return None


def render_row(task: dict, *, max_width: int, now: float, model: str = "",
               top_ctx: dict | None = None) -> str:
	name = str(task.get("label") or task.get("name") or task.get("id") or "?").strip()
	type_ = str(task.get("type") or "").strip()
	description = str(task.get("description") or "").strip()
	tokens = task.get("tokenCount")
	samples = task.get("tokenSamples")
	start = _parse_start_time(task.get("startTime"))
	status = task.get("status", "")
	elapsed = (now - start) if start else None
	# task-level model override > top-level model
	task_model = ""
	tm = task.get("model")
	if isinstance(tm, dict):
		task_model = str(tm.get("display_name") or tm.get("id") or "").strip()
	elif isinstance(tm, str):
		task_model = tm.strip()
	model_label = task_model or model

	line = ""

	if type_:
		type_label = {"local_agent": "Agent"}.get(type_.lower(), type_)
		line += _style(f"[{type_label}", fg=CATPPUCCIN["mauve"])
		line += _status_seg(status)
		if model_label:
			line += _style(f"·{model_label}", fg=CATPPUCCIN["blue"])
		line += _style(f"]", fg=CATPPUCCIN["mauve"], bold=True)

	line += _style(name, fg=CATPPUCCIN["cyan"], bold=True)

	ctx_pct = _extract_ctx_pct(task, top_ctx)
	if ctx_pct is not None:
		line += _style(f"·{ctx_pct:.0f}%", fg=_ctx_color(ctx_pct), bold=True)

	if tokens is not None:
		try:
			tok_n = int(tokens)
			if tok_n > 0:
				tok_seg = _style(f"·{_format_compact_int(tok_n)}", fg=CATPPUCCIN["text"])
				rate = _token_rate(samples)
				if rate and rate > 0:
					tok_seg += _style(f"·({rate:.0f}/s)", fg=CATPPUCCIN["subtle"], dim=True)
				line += tok_seg
		except Exception:
			pass

	if elapsed is not None and elapsed > 0:
		line += _style(_format_duration(elapsed), fg=CATPPUCCIN["subtle"], dim=True)

	if description and description != name:
		line += _style(description, fg=CATPPUCCIN["subtle"])

	return _truncate(line, max_width) if max_width > 0 else line


def _read_payload() -> dict:
	if sys.stdin is None or sys.stdin.isatty():
		return {}
	try:
		raw = sys.stdin.read()
	except Exception:
		return {}
	raw = (raw or "").strip()
	if not raw:
		return {}
	try:
		data = json.loads(raw)
	except Exception:
		return {}
	return data if isinstance(data, dict) else {}


def main() -> None:
	payload = _read_payload()
	tasks = payload.get("tasks") or []
	try:
		cols = int(payload.get("columns") or 0)
	except Exception:
		cols = 0
	model_obj = payload.get("model") or {}
	if isinstance(model_obj, dict):
		top_model = str(model_obj.get("display_name") or model_obj.get("id") or "").strip()
	else:
		top_model = str(model_obj or "").strip()
	top_ctx = payload.get("context_window") if isinstance(payload.get("context_window"), dict) else None
	now = time.time()
	out = sys.stdout
	for task in tasks:
		if not isinstance(task, dict):
			continue
		tid = task.get("id")
		if not tid:
			continue
		content = render_row(task, max_width=cols, now=now, model=top_model, top_ctx=top_ctx)
		out.write(json.dumps({"id": tid, "content": content}, ensure_ascii=False))
		out.write("\n")


if __name__ == "__main__":
	main()
