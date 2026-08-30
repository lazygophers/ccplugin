#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")



def run_cmd(cmd: list[str] | str, *, cwd: str | None = None, timeout: float = 0.35) -> str | None:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=isinstance(cmd, str),
            cwd=cwd,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def read_statusline_payload() -> dict:
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


def get_path(payload: dict, path: list[str], default=None):
    cur = payload
    for key in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
    return default if cur is None else cur


def colors_enabled() -> bool:
    if os.environ.get("STATUSLINE_NO_COLOR"):
        return False
    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("TERM", "").lower() == "dumb":
        return False
    return True


def emoji_enabled() -> bool:
    if os.environ.get("STATUSLINE_NO_EMOJI"):
        return False
    if os.environ.get("NO_EMOJI") is not None:
        return False
    if os.environ.get("TERM", "").lower() == "dumb":
        return False
    return True


def with_emoji(icon: str, text: str) -> str:
    if not icon or not emoji_enabled():
        return text
    return f"{icon} {text}"


def _ansi(code: str) -> str:
    return f"\x1b[{code}m" if colors_enabled() else ""


def _rgb_fg(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    return _ansi(f"38;2;{r};{g};{b}")


def _rgb_bg(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    return _ansi(f"48;2;{r};{g};{b}")


def style(
    text: str,
    *,
    fg: tuple[int, int, int] | None = None,
    bg: tuple[int, int, int] | None = None,
    bold: bool = False,
    dim: bool = False,
) -> str:
    if not colors_enabled():
        return text
    seq = ""
    if bold:
        seq += _ansi("1")
    if dim:
        seq += _ansi("2")
    if fg is not None:
        seq += _rgb_fg(fg)
    if bg is not None:
        seq += _rgb_bg(bg)
    reset = _ansi("0")
    return f"{seq}{text}{reset}"


def strip_ansi(s: str) -> str:
    return ANSI_ESCAPE_RE.sub("", s)


def join_parts(parts: list[str], *, sep: str) -> str:
    return sep.join([p for p in parts if p])


def terminal_size() -> tuple[int, int]:
    size = shutil.get_terminal_size(fallback=(120, 30))
    try:
        cols = int(size.columns)
    except Exception:
        cols = 120
    try:
        rows = int(size.lines)
    except Exception:
        rows = 30
    return max(20, cols), max(1, rows)


def visible_len(s: str) -> int:
    return len(strip_ansi(s or ""))


def truncate_end(s: str, max_len: int) -> str:
    if max_len <= 0:
        return ""
    plain = strip_ansi(s or "")
    if len(plain) <= max_len:
        return s
    if max_len <= 1:
        return "…"
    # 保留尾部更利于路径/版本等识别
    return "…" + plain[-(max_len - 1) :]


def fit_segments(segments: list[str], *, sep: str, max_width: int) -> str:
    parts = [p for p in segments if p]
    if not parts:
        return ""
    out = join_parts(parts, sep=sep)
    while parts and visible_len(out) > max_width:
        parts.pop()
        out = join_parts(parts, sep=sep)
    if visible_len(out) <= max_width:
        return out
    return truncate_end(out, max_width)


def shorten_path(path: str, *, max_len: int = 38) -> str:
    if not path:
        return "?"
    try:
        expanded = Path(path).expanduser()
        display = str(expanded)
        home = str(Path.home())
        if display.startswith(home):
            display = "~" + display[len(home) :]
    except Exception:
        display = path
    if len(display) <= max_len:
        return display
    parts = display.split(os.sep)
    if len(parts) <= 2:
        return display[-max_len:]
    keep_tail = 2
    head = parts[0] if parts[0] else ""
    tail = os.sep.join(parts[-keep_tail:])
    shortened = f"{head}{os.sep}…{os.sep}{tail}" if head else f"…{os.sep}{tail}"
    if len(shortened) <= max_len:
        return shortened
    return shortened[-max_len:]


def format_compact_int(value: int | None) -> str:
    if value is None:
        return "0"
    try:
        n = int(value)
    except Exception:
        return "0"
    if n >= 1_000_000:
        return f"{n/1_000_000:.2f}M"
    if n >= 10_000:
        return f"{n/1_000:.0f}K"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def format_duration_ms(ms: int | None) -> str:
    if not ms:
        return "0s"
    try:
        total_s = max(0, int(ms) // 1000)
    except Exception:
        return "0s"
    s = total_s % 60
    m = (total_s // 60) % 60
    h = total_s // 3600
    if h > 0:
        return f"{h}h{m:02d}m"
    if m > 0:
        return f"{m}m{s:02d}s"
    return f"{s}s"


def progress_bar(pct: float, *, width: int = 16) -> str:
    try:
        p = max(0.0, min(100.0, float(pct)))
    except Exception:
        p = 0.0
    filled = int(round(width * (p / 100.0)))
    filled = max(0, min(width, filled))
    return "█" * filled + "░" * (width - filled)


def progress_bar_colored(pct: float, *, width: int, filled_fg: tuple[int, int, int]) -> str:
    try:
        p = max(0.0, min(100.0, float(pct)))
    except Exception:
        p = 0.0
    filled = int(round(width * (p / 100.0)))
    filled = max(0, min(width, filled))
    full = "█" * filled
    empty = "░" * (width - filled)
    # 空白部分用更弱的颜色，整体更柔和
    return style(full, fg=filled_fg, bold=True) + style(empty, fg=CATPPUCCIN["subtle"], dim=True)

def get_model():
    model = os.environ.get("ANTHROPIC_MODEL", "")
    if model:
        return model
    return os.environ.get("ANTHROPIC_DEFAULT_SONNET_MODEL", "unknown")

def get_agent_name():
    return os.environ.get("CLAUDE_CODE_AGENT_NAME", "Claude")

def get_thinking_level():
    level = os.environ.get("ANTHROPIC_THINKING_LEVEL", "")
    if level:
        return f"思考: {level}"
    return "思考: auto"


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


def cache_path_for_git(root: str) -> Path:
    digest = hashlib.sha1(root.encode("utf-8", errors="ignore")).hexdigest()[:12]
    return Path("/tmp") / f"claude-statusline-git-{digest}.json"


def get_git_root(cwd: str) -> str | None:
    root = run_cmd(["git", "rev-parse", "--show-toplevel"], cwd=cwd)
    return root or None


def get_worktree_name(repo_root: str) -> str:
    dotgit = Path(repo_root) / ".git"
    try:
        if dotgit.is_file():
            first = _read_first_nonempty_line(dotgit) or ""
            if first.startswith("gitdir:"):
                gitdir = first.split(":", 1)[1].strip()
                # 在 worktree 中，gitdir 通常包含 ".../worktrees/<name>"
                m = re.search(r"[\\\\/]+worktrees[\\\\/]+([^\\\\/]+)", gitdir)
                if m:
                    return m.group(1)
                return "worktree"
    except Exception:
        return ""
    return ""


def get_git_info(cwd: str, *, ttl_s: float = 1.0) -> dict | None:
    root = get_git_root(cwd)
    if not root:
        return None

    cache_file = cache_path_for_git(root)
    now = time.time()
    try:
        if cache_file.exists():
            age = now - cache_file.stat().st_mtime
            if age <= ttl_s:
                cached = json.loads(cache_file.read_text(encoding="utf-8"))
                if isinstance(cached, dict):
                    return cached
    except Exception:
        pass

    branch = run_cmd(["git", "branch", "--show-current"], cwd=cwd) or ""
    if not branch:
        branch = run_cmd(["git", "rev-parse", "--short", "HEAD"], cwd=cwd) or ""

    # 只判断有无改动（决定分支名颜色），不统计文件数和行数
    status = run_cmd(["git", "status", "--porcelain"], cwd=cwd) or ""
    dirty = any(line.strip() for line in status.splitlines())

    info = {
        "root": root,
        "branch": branch or "detached",
        "dirty": dirty,
        "worktree": get_worktree_name(root),
    }
    try:
        cache_file.write_text(json.dumps(info, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass
    return info



def _read_first_nonempty_line(path: Path) -> str | None:
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or s.startswith("//"):
                continue
            return s
    except Exception:
        return None
    return None



def format_reset_delta(resets_at, *, now: float | None = None) -> str:
    """把额度重置时间戳转成剩余时长，如 3h12m / 45m / 2d3h。"""
    try:
        target = float(resets_at)
    except Exception:
        return ""
    if target <= 0:
        return ""
    remain = int(target - (time.time() if now is None else now))
    if remain <= 0:
        return "0m"
    d = remain // 86400
    h = (remain % 86400) // 3600
    m = (remain % 3600) // 60
    if d > 0:
        return f"{d}d{h}h"
    if h > 0:
        return f"{h}h{m:02d}m"
    return f"{max(1, m)}m"


RATE_LIMIT_WINDOWS = (("five_hour", "5h"), ("seven_day", "7d"))


def rate_limit_segments(payload: dict, *, cols: int) -> list[str]:
    """订阅额度（5 小时会话窗口 / 7 天窗口）。仅订阅用户且首次响应后才有数据。"""
    limits = get_path(payload, ["rate_limits"], None)
    if not isinstance(limits, dict):
        return []

    bar_width = 6 if cols >= 110 else 0
    segments: list[str] = []
    for key, label in RATE_LIMIT_WINDOWS:
        window = limits.get(key)
        if not isinstance(window, dict):
            continue
        try:
            pct = float(window.get("used_percentage"))
        except Exception:
            continue
        col = ctx_color(pct)
        seg = style(f"{label}", fg=CATPPUCCIN["subtle"], dim=True) + " "
        if bar_width:
            seg += progress_bar_colored(pct, width=bar_width, filled_fg=col) + " "
        seg += style(f"{pct:.0f}%", fg=col, bold=True)
        reset = format_reset_delta(window.get("resets_at"))
        if reset:
            seg += style(f" →{reset}", fg=CATPPUCCIN["subtle"], dim=True)
        segments.append(seg)
    return segments


def ctx_color(pct: float) -> tuple[int, int, int]:
    try:
        p = float(pct)
    except Exception:
        p = 0.0
    if p >= 90:
        return CATPPUCCIN["red"]
    if p >= 75:
        return CATPPUCCIN["yellow"]
    return CATPPUCCIN["green"]


def render_statusline(payload: dict) -> str:
    model = (
        get_path(payload, ["model", "id"], None)
        or get_path(payload, ["model", "display_name"], None)
        or get_model()
    )

    current_dir = (
        get_path(payload, ["workspace", "current_dir"], None)
        or get_path(payload, ["cwd"], None)
        or os.getcwd()
    )
    cols, rows = terminal_size()

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

    cost_usd = get_path(payload, ["cost", "total_cost_usd"], None)

    total_in = get_path(payload, ["context_window", "total_input_tokens"], None)
    total_out = get_path(payload, ["context_window", "total_output_tokens"], None)

    version = str(get_path(payload, ["version"], "") or "").strip()
    agent_name = str(get_path(payload, ["agent", "name"], "") or "").strip()

    git = get_git_info(str(current_dir), ttl_s=0.0)

    sep_dot = style(" · ", fg=CATPPUCCIN["subtle"], dim=True)
    sep_pipe = style(" | ", fg=CATPPUCCIN["subtle"], dim=True)
    major_sep = sep_dot

    # 第 1 行：model / token（总）与花费 / 上下文占用
    line1_parts: list[str] = [style(str(model), fg=CATPPUCCIN["cyan"], bold=True)]

    tokens_seg = ""
    total_tokens = None
    if total_in is not None or total_out is not None:
        try:
            total_tokens = int(total_in or 0) + int(total_out or 0)
        except Exception:
            total_tokens = None
    if total_tokens is None:
        try:
            total_tokens = int(os.environ.get("CLAUDE_CODE_TOTAL_TOKENS", "0"))
        except Exception:
            total_tokens = None
    if total_tokens is None:
        total_tokens = 0
    token_value = f"{format_compact_int(total_tokens)}"
    # Token 后面始终带（$...），优先用 stdin 的真实成本
    try:
        c = float(cost_usd) if cost_usd is not None else 0.0
        token_cost = f"（${c:.2f}）"
    except Exception:
        token_cost = "（$0.00）"
    tokens_seg = style(token_value, fg=CATPPUCCIN["text"], bold=True) + style(
        token_cost, fg=CATPPUCCIN["subtle"], dim=True
    )
    if tokens_seg:
        line1_parts.append(tokens_seg)

    if context_pct_f > 0:
        bar_width = 18 if cols >= 100 else (14 if cols >= 80 else 10)
        bar_col = ctx_color(context_pct_f)
        line1_parts.append(
            progress_bar_colored(context_pct_f, width=bar_width, filled_fg=bar_col)
            + style(f" {context_pct_f:.0f}%", fg=bar_col, bold=True)
        )

    line1 = fit_segments(line1_parts, sep=major_sep, max_width=cols)

    # 第 2 行：git（分支 / worktree） | 路径
    line2_left_parts: list[str] = []
    if git:
        branch = str(git.get("branch", "") or "").strip()
        dirty = bool(git.get("dirty"))
        git_fg = CATPPUCCIN["mauve"] if not dirty else CATPPUCCIN["yellow"]

        if branch:
            line2_left_parts.append(style(f"⎇ {branch}", fg=git_fg, bold=True))

        wt_name = get_path(payload, ["worktree", "name"], None)
        if isinstance(wt_name, str) and wt_name.strip():
            line2_left_parts.append(style(f"WT:{wt_name.strip()}", fg=CATPPUCCIN["subtle"], dim=True))
        else:
            worktree = str(git.get("worktree", "") or "").strip()
            if worktree:
                line2_left_parts.append(style(f"WT:{worktree}", fg=CATPPUCCIN["subtle"], dim=True))

    left = join_parts(line2_left_parts, sep=" ")
    # 路径根据当前宽度动态截断；极窄窗口时优先保留 git 信息
    if left:
        budget = cols - visible_len(left) - visible_len(sep_pipe)
        if budget <= 0:
            line2 = truncate_end(left, cols)
        else:
            path = shorten_path(str(current_dir), max_len=max(4, budget))
            path_seg = style(path, fg=CATPPUCCIN["subtle"], dim=True)
            line2 = left + sep_pipe + path_seg
            if visible_len(line2) > cols:
                # 再保险：必要时截断尾部（通常是路径）
                line2 = truncate_end(line2, cols)
    else:
        path_seg = style(shorten_path(str(current_dir), max_len=min(64, cols)), fg=CATPPUCCIN["subtle"], dim=True)
        line2 = fit_segments([path_seg], sep=major_sep, max_width=cols)

    # 第 3 行：订阅额度 / 代理 / 版本
    limit_parts = rate_limit_segments(payload, cols=cols)

    meta_parts: list[str] = []
    needs_third_line = bool(agent_name) or bool(limit_parts)

    # 额度排在代理名/版本之前：窄终端截断时优先保住它
    meta_parts.extend(limit_parts)
    if agent_name:
        meta_parts.append(style(f"代理:{agent_name}", fg=CATPPUCCIN["pink"], dim=True))
    if needs_third_line and version:
        meta_parts.append(style(f"v{version.lstrip('vV')}", fg=CATPPUCCIN["subtle"], dim=True))

    line3 = fit_segments(meta_parts, sep=sep_dot, max_width=cols) if meta_parts else ""

    # 没有第 3 行内容：两行输出，但依然展示 version
    if not needs_third_line:
        tail: list[str] = []
        if version:
            tail.append(style(f"v{version.lstrip('vV')}", fg=CATPPUCCIN["subtle"], dim=True))
        if tail:
            line2 = fit_segments([line2] + tail, sep=sep_dot, max_width=cols)
        return f"{line1}\n{line2}".rstrip()
    if rows < 3:
        folded = fit_segments([line2] + meta_parts + ([style(f"v{version.lstrip('vV')}", fg=CATPPUCCIN["subtle"], dim=True)] if version and "v" not in strip_ansi("".join(meta_parts)) else []), sep=sep_dot, max_width=cols)
        return f"{line1}\n{folded}".rstrip()
    return f"{line1}\n{line2}\n{line3}".rstrip()


def main() -> None:
    payload = read_statusline_payload()
    print(render_statusline(payload))

if __name__ == "__main__":
    main()
