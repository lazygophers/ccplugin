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
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")

try:
    import tomllib  # py>=3.11
except Exception:  # pragma: no cover
    tomllib = None


class ToolVersionParser(ABC):
    """工具版本解析器抽象基类"""

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """工具名称，如 'go', 'node', 'python', 'rust'"""
        pass

    @property
    @abstractmethod
    def config_files(self) -> list[str]:
        """需要查找的配置文件列表"""
        pass

    @property
    def detection_files(self) -> list[str]:
        """用于检测工具是否存在的文件（默认使用config_files）"""
        return self.config_files

    @abstractmethod
    def parse(self, file_path: Path) -> Optional[str]:
        """解析配置文件，返回版本字符串或None"""
        pass

    def get_installed_version(self, cwd: str) -> Optional[str]:
        """获取已安装的工具版本（可被子类覆盖）"""
        return None


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


def git_files_marker(n: int) -> str:
    icon = os.environ.get("STATUSLINE_GIT_FILES_ICON", "◌").strip()
    if not emoji_enabled():
        icon = ""
    return f"{icon}{n}" if icon else str(n)


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


def compact_major_minor(version: str) -> str:
    s = (version or "").strip()
    if not s:
        return ""
    s = s.lstrip("vV").strip()
    m = re.search(r"([0-9]+)\.([0-9]+)", s)
    if not m:
        return s
    return f"{m.group(1)}.{m.group(2)}"


def compact_python_requirement(req: str) -> str:
    s = (req or "").strip()
    if not s:
        return ""
    s = s.replace(" ", "")
    m = re.match(r"^>=([0-9]+)\.([0-9]+)", s)
    if m:
        return f"{m.group(1)}.{m.group(2)}+"
    return compact_major_minor(s)


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

# 单位: $/M tokens (2026-05 最新定价); cache_read = 缓存命中折扣 (≈ input × 0.1)
MODEL_PRICING = {
    # ===== Claude =====
    "claude-opus-4-7": {"input": 5.0, "output": 25.0, "cache_read": 0.5},
    "claude-opus-4-5-20251101": {"input": 5.0, "output": 25.0, "cache_read": 0.5},
    "claude-opus-4-1-20250805": {"input": 5.0, "output": 25.0, "cache_read": 0.5},
    "claude-opus-4-0": {"input": 15.0, "output": 75.0, "cache_read": 1.5},
    "claude-opus-4-7-20250619": {"input": 15.0, "output": 75.0, "cache_read": 1.5},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0, "cache_read": 0.3},
    "claude-sonnet-4-5-20250929": {"input": 3.0, "output": 15.0, "cache_read": 0.3},
    "claude-sonnet-4-0": {"input": 3.0, "output": 15.0, "cache_read": 0.3},
    "claude-sonnet-4-7-20250619": {"input": 3.0, "output": 15.0, "cache_read": 0.3},
    "claude-haiku-4-5": {"input": 1.0, "output": 5.0, "cache_read": 0.1},
    "claude-3-7-sonnet-20250219": {"input": 3.0, "output": 15.0, "cache_read": 0.3},
    "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0, "cache_read": 0.3},
    "claude-3-5-haiku-20241022": {"input": 0.8, "output": 4.0, "cache_read": 0.08},
    "claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0, "cache_read": 0.3},
    "claude-3-opus-20240229": {"input": 15.0, "output": 75.0, "cache_read": 1.5},
    "claude-2.1": {"input": 8.0, "output": 24.0, "cache_read": 0.8},
    "claude-2.0": {"input": 8.0, "output": 24.0, "cache_read": 0.8},
    "claude-instant-1.2": {"input": 1.63, "output": 5.51, "cache_read": 0.163},
    "claude-1.3": {"input": 1.63, "output": 5.51, "cache_read": 0.163},

    # ===== OpenAI =====
    "gpt-5.5": {"input": 5.0, "output": 30.0, "cache_read": 0.5},
    "gpt-5.5-pro-2026-05-06": {"input": 2.5, "output": 15.0, "cache_read": 0.25},
    "gpt-5.5-pro": {"input": 2.5, "output": 15.0, "cache_read": 0.25},
    "gpt-5": {"input": 1.25, "output": 10.0, "cache_read": 0.125},
    "gpt-5-mini": {"input": 0.25, "output": 2.0, "cache_read": 0.025},
    "gpt-5-4": {"input": 2.5, "output": 15.0, "cache_read": 0.25},
    "gpt-5-4-mini": {"input": 0.75, "output": 4.5, "cache_read": 0.075},
    "gpt-5-4-nano": {"input": 0.2, "output": 1.25, "cache_read": 0.02},
    "o1": {"input": 15.0, "output": 60.0, "cache_read": 1.5},
    "o1-preview": {"input": 15.0, "output": 60.0, "cache_read": 1.5},
    "o1-mini": {"input": 1.1, "output": 4.4, "cache_read": 0.11},
    "o3": {"input": 2.0, "output": 8.0, "cache_read": 0.2},
    "o3-mini": {"input": 1.1, "output": 4.4, "cache_read": 0.11},
    "gpt-4o": {"input": 5.0, "output": 15.0, "cache_read": 0.5},
    "gpt-4o-2024-08-06": {"input": 5.0, "output": 15.0, "cache_read": 0.5},
    "chatgpt-4o-latest": {"input": 5.0, "output": 15.0, "cache_read": 0.5},
    "gpt-4o-mini": {"input": 0.15, "output": 0.6, "cache_read": 0.015},
    "gpt-4o-mini-2024-07-18": {"input": 0.15, "output": 0.6, "cache_read": 0.015},
    "gpt-4.1": {"input": 2.0, "output": 8.0, "cache_read": 0.2},
    "gpt-4-turbo": {"input": 10.0, "output": 30.0, "cache_read": 1.0},

    # ===== DeepSeek =====
    "deepseek-v4-pro": {"input": 2.2, "output": 2.2, "cache_read": 0.22},
    "deepseek-v4-flash": {"input": 1.0, "output": 2.0, "cache_read": 0.1},
    "deepseek-chat": {"input": 0.27, "output": 1.1, "cache_read": 0.027},
    "deepseek-reasoner": {"input": 0.55, "output": 2.19, "cache_read": 0.055},
    "deepseek-v3": {"input": 0.27, "output": 1.1, "cache_read": 0.027},
    "deepseek-v2": {"input": 0.14, "output": 0.28, "cache_read": 0.014},
    "deepseek-r1": {"input": 2.0, "output": 8.0, "cache_read": 0.2},
    "deepseek-coder-v2": {"input": 0.14, "output": 0.28, "cache_read": 0.014},

    # ===== Kimi / 月之暗面 =====
    "kimi-k2.6": {"input": 0.95, "output": 4.0, "cache_read": 0.16},
    "kimi-k2.6-turbo": {"input": 2.0, "output": 8.0, "cache_read": 0.3},
    "kimi-k2": {"input": 0.5, "output": 2.5, "cache_read": 0.08},
    "kimi-k1.5": {"input": 0.3, "output": 1.5, "cache_read": 0.05},
    "moonshot-v1": {"input": 0.12, "output": 0.6, "cache_read": 0.012},

    # ===== GLM / 智谱AI =====
    "glm-5.1": {"input": 1.4, "output": 4.4, "cache_read": 0.26},
    "glm-5": {"input": 0.9, "output": 3.0, "cache_read": 0.15},
    "glm-4.7": {"input": 0.6, "output": 2.0, "cache_read": 0.1},
    "glm-4.6": {"input": 0.5, "output": 1.8, "cache_read": 0.1},
    "glm-4-plus": {"input": 0.4, "output": 1.5, "cache_read": 0.08},
    "glm-4": {"input": 0.3, "output": 1.2, "cache_read": 0.06},

    # ===== MiniMax =====
    "minimax-2.7": {"input": 0.3, "output": 1.2, "cache_read": 0.06},

    # ===== Qwen / 通义千问 (闭源 API 版本) =====
    "qwen3.6-max": {"input": 0.5, "output": 2.0, "cache_read": 0.05},
    "qwen2.5-72b-instruct": {"input": 0.4, "output": 0.4, "cache_read": 0.04},

    # ===== Doubao / 字节火山引擎 =====
    "doubao-seed-2.0-pro": {"input": 0.44, "output": 2.2, "cache_read": 0.088},
    "doubao-seed-2.0-lite": {"input": 0.08, "output": 0.5, "cache_read": 0.016},
    "doubao-seed-1.8": {"input": 0.11, "output": 0.28, "cache_read": 0.022},
    "doubao-seed-1.6-flash": {"input": 0.02, "output": 0.21, "cache_read": 0.004},

    # ===== Google Gemini =====
    "gemini-3.1-pro": {"input": 4.5, "output": 4.5, "cache_read": 0.45},
    "gemini-2.5-pro": {"input": 1.25, "output": 10.0, "cache_read": 0.125},
    "gemini-2.5-flash": {"input": 0.3, "output": 2.5, "cache_read": 0.03},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.0, "cache_read": 0.125},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.3, "cache_read": 0.0075},

    # ===== Meta Llama (开源免费, API 端有 Fireworks 托管价) =====
    "llama-4-scout": {"input": 0.08, "output": 0.3, "cache_read": 0.008},
    "llama-4-maverick": {"input": 0.15, "output": 0.6, "cache_read": 0.015},
    "llama-4-behemoth": {"input": 0.0, "output": 0.0, "cache_read": 0.0},

    # ===== 其他 =====
    "grok-3": {"input": 1.25, "output": 2.5, "cache_read": 0.2},
    "grok-2": {"input": 0.5, "output": 1.0, "cache_read": 0.1},
    "sonar-pro": {"input": 3.0, "output": 15.0, "cache_read": 0.3},
    "yi-lightning": {"input": 0.3, "output": 0.3, "cache_read": 0.03},
}

# 前缀匹配: model_id 前缀 → 精确 key
MODEL_PRICING_PREFIX = {
    "claude-opus-4-7": "claude-opus-4-7",
    "claude-opus-4-5": "claude-opus-4-5-20251101",
    "claude-opus-4-1": "claude-opus-4-1-20250805",
    "claude-opus-4-0": "claude-opus-4-0",
    "claude-sonnet-4-6": "claude-sonnet-4-6",
    "claude-sonnet-4-5": "claude-sonnet-4-5-20250929",
    "claude-sonnet-4-0": "claude-sonnet-4-0",
    "claude-haiku-4-5": "claude-haiku-4-5",
    "claude-3-7-sonnet": "claude-3-7-sonnet-20250219",
    "claude-3-5-sonnet": "claude-3-5-sonnet-20241022",
    "claude-3-5-haiku": "claude-3-5-haiku-20241022",
    "claude-3-sonnet": "claude-3-sonnet-20240229",
    "claude-3-opus": "claude-3-opus-20240229",
    "claude-2.1": "claude-2.1",
    "claude-2.0": "claude-2.0",
    "claude-instant": "claude-instant-1.2",
    "claude-1.3": "claude-1.3",
    "gpt-5.5": "gpt-5.5",
    "gpt-5": "gpt-5",
    "o1": "o1",
    "o3": "o3",
    "gpt-4o": "gpt-4o",
    "gpt-4o-mini": "gpt-4o-mini",
    "gpt-4-turbo": "gpt-4-turbo",
    "gpt-4.1": "gpt-4.1",
    "chatgpt-4o": "chatgpt-4o-latest",
    "deepseek-v4": "deepseek-v4-pro",
    "deepseek-v4-flash": "deepseek-v4-flash",
    "deepseek-chat": "deepseek-chat",
    "deepseek-reasoner": "deepseek-reasoner",
    "deepseek-v3": "deepseek-v3",
    "deepseek-v2": "deepseek-v2",
    "deepseek-r1": "deepseek-r1",
    "deepseek-coder": "deepseek-coder-v2",
    "kimi-k2.6": "kimi-k2.6",
    "kimi-k2": "kimi-k2",
    "kimi-k1": "kimi-k1.5",
    "moonshot": "moonshot-v1",
    "glm-5.1": "glm-5.1",
    "glm-5": "glm-5",
    "glm-4.7": "glm-4.7",
    "glm-4.6": "glm-4.6",
    "glm-4-plus": "glm-4-plus",
    "glm-4": "glm-4",
    "minimax-2": "minimax-2.7",
    "minimax": "minimax-2.7",
    "qwen3.6-max": "qwen3.6-max",
    "qwen3.5": "qwen3.6-max",
    "qwen2.5": "qwen2.5-72b-instruct",
    "doubao-seed-2.0": "doubao-seed-2.0-pro",
    "doubao-seed-1.8": "doubao-seed-1.8",
    "doubao-seed-1.6-flash": "doubao-seed-1.6-flash",
    "doubao-seed-1.6": "doubao-seed-1.8",
    "gemini-3.1-pro": "gemini-3.1-pro",
    "gemini-2.5-pro": "gemini-2.5-pro",
    "gemini-2.5-flash": "gemini-2.5-flash",
    "gemini-1.5-pro": "gemini-1.5-pro",
    "gemini-1.5-flash": "gemini-1.5-flash",
    "llama-4": "llama-4-scout",
    "llama-3": "llama-4-scout",
    "grok-3": "grok-3",
    "grok-2": "grok-2",
    "sonar": "sonar-pro",
    "yi-lightning": "yi-lightning",
}


def calc_model_cost(model_id: str, input_tokens: int, output_tokens: int, cache_read_tokens: int) -> float | None:
    key = MODEL_PRICING.get(model_id)
    if not key:
        for prefix, resolved in MODEL_PRICING_PREFIX.items():
            if model_id.startswith(prefix):
                key = MODEL_PRICING.get(resolved)
                break
    if not key:
        return None
    if key["input"] == 0 and key["output"] == 0:
        return 0.0
    return (
        input_tokens / 1_000_000 * key["input"]
        + output_tokens / 1_000_000 * key["output"]
        + cache_read_tokens / 1_000_000 * key["cache_read"]
    )


    if context_pct_f > 0:
        ctx_col = ctx_color(context_pct_f)
        line1_parts.append(style(f"{context_pct_f:.0f}%", fg=ctx_col, bold=True))

    cache_denom = cur_in + cur_cc + cur_cr
    if cache_denom > 0:
        cache_pct = cur_cr / cache_denom * 100.0
        cache_str = f"{cache_pct:.4f}".rstrip("0").rstrip(".")
        line1_parts.append(style(f"缓存 {cache_str}%", fg=CATPPUCCIN["green"], bold=True))

    line1 = fit_segments(line1_parts, sep=major_sep, max_width=cols)

    # 第 2 行：git（含 worktree / 文件数 / 行变更） | 路径
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

    # 第 3 行：环境 + 其他信息（上下文/版本/代理）
    env_parts: list[str] = []

    meta_parts: list[str] = []
    has_rate_limit = False
    for _k in ("five_hour", "seven_day"):
        _p = get_path(payload, ["rate_limits", _k, "used_percentage"], None)
        try:
            if float(_p or 0.0) > 0:
                has_rate_limit = True
                break
        except Exception:
            pass
    needs_third_line = bool(env_parts) or has_rate_limit or bool(agent_name)

    now_ts = time.time()
    for label, key, window_s in (("5h", "five_hour", 5 * 3600), ("7d", "seven_day", 7 * 86400)):
        pct = get_path(payload, ["rate_limits", key, "used_percentage"], None)
        try:
            pct_f = float(pct or 0.0)
        except Exception:
            pct_f = 0.0
        if pct_f <= 0:
            continue
        reset_ts = get_path(payload, ["rate_limits", key, "resets_at"], None)
        elapsed_pct = 0.0
        try:
            if reset_ts:
                window_start = int(reset_ts) - window_s
                elapsed = now_ts - window_start
                elapsed_pct = max(0.0, min(100.0, elapsed / window_s * 100.0))
        except Exception:
            elapsed_pct = 0.0
        # 用量 vs 时间进度: 超出 5pp red; 未超但 ≥95% yellow; 否则 green
        overage = pct_f - elapsed_pct
        if overage > 5:
            col = CATPPUCCIN["red"]
        elif pct_f > 85:
            col = CATPPUCCIN["yellow"]
        else:
            col = CATPPUCCIN["green"]
        reset_str = ""
        if col is not CATPPUCCIN["green"]:
            try:
                if reset_ts:
                    reset_str = time.strftime("%m-%d %H:%M", time.localtime(int(reset_ts)))
            except Exception:
                reset_str = ""
        seg = style(f"{label} {pct_f:.0f}%", fg=col, bold=True)
        if reset_str:
            seg += style(f"→{reset_str}", fg=CATPPUCCIN["subtle"], dim=True)
        meta_parts.append(seg)
    if agent_name:
        meta_parts.append(style(f"代理:{agent_name}", fg=CATPPUCCIN["pink"], dim=True))
    if needs_third_line and version:
        meta_parts.append(style(f"v{version.lstrip('vV')}", fg=CATPPUCCIN["subtle"], dim=True))

    line3_parts = env_parts + meta_parts
    line3 = fit_segments(line3_parts, sep=sep_dot, max_width=cols) if line3_parts else ""

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
