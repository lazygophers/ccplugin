"""
格式化工具函数

提供各种格式化功能，包括时间、数字、文本等。
"""

import re
from typing import Optional


def format_duration(ms: Optional[int]) -> str:
    """
    格式化时间间隔

    Args:
        ms: 毫秒数

    Returns:
        格式化后的时间字符串，如 "1:23" 或 "45.6s"
    """
    if ms is None:
        return "0s"

    if ms < 1000:
        return f"{ms}ms"
    elif ms < 60000:
        return f"{ms / 1000:.1f}s"
    else:
        minutes = ms // 60000
        seconds = (ms % 60000) / 1000
        return f"{minutes}:{seconds:04.1f}"


def format_duration_ms(ms: Optional[int]) -> str:
    """
    格式化时间间隔（毫秒）- 向后兼容原始实现

    Args:
        ms: 毫秒数

    Returns:
        格式化后的时间字符串，如 "1m23s" 或 "45s"
    """
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


def format_token_count(count: Optional[int]) -> str:
    """
    格式化 token 计数

    Args:
        count: token 数量

    Returns:
        格式化后的 token 字符串，如 "12.5K"
    """
    if count is None:
        return "0"

    if count < 1000:
        return str(count)
    elif count < 1_000_000:
        return f"{count / 1000:.1f}K"
    else:
        return f"{count / 1_000_000:.1f}M"


def format_percentage(value: float, *, decimals: int = 0) -> str:
    """
    格式化百分比

    Args:
        value: 百分比值 (0-100)
        decimals: 小数位数

    Returns:
        格式化后的百分比字符串，如 "80%"
    """
    if decimals == 0:
        return f"{int(value)}%"
    else:
        return f"{value:.{decimals}f}%"


def format_compact_int(value: Optional[int]) -> str:
    """
    格式化整数为紧凑形式

    Args:
        value: 整数值

    Returns:
        紧凑格式的字符串，如 "1.2K", "3.4M"
    """
    if value is None:
        return "0"

    if value < 1000:
        return str(value)
    elif value < 1_000_000:
        return f"{value / 1000:.1f}K"
    elif value < 1_000_000_000:
        return f"{value / 1_000_000:.1f}M"
    else:
        return f"{value / 1_000_000_000:.1f}B"


def truncate_text(text: str, max_len: int, suffix: str = "...") -> str:
    """
    截断文本到指定长度

    Args:
        text: 原始文本
        max_len: 最大长度
        suffix: 截断后缀

    Returns:
        截断后的文本
    """
    if len(text) <= max_len:
        return text

    if max_len <= len(suffix):
        return suffix[:max_len]

    return text[: max_len - len(suffix)] + suffix


def shorten_path(path: str, *, max_len: int = 38) -> str:
    """
    缩短文件路径

    Args:
        path: 文件路径
        max_len: 最大长度

    Returns:
        缩短后的路径
    """
    if len(path) <= max_len:
        return path

    # 保留开头和结尾
    parts = path.split("/")
    if len(parts) <= 2:
        return path

    # 缩短中间部分
    result = parts[0]  # 保留第一部分
    remaining_len = max_len - len(parts[-1]) - 4  # -4 for "..." and "/"

    for part in parts[1:-1]:
        if remaining_len <= 0:
            break
        if len(part) > remaining_len:
            result += "/..."
            break
        result += "/" + part
        remaining_len -= len(part) + 1

    result += "/" + parts[-1]
    return result


def progress_bar(pct: float, *, width: int = 16) -> str:
    """
    生成文本进度条

    Args:
        pct: 百分比 (0-100)
        width: 进度条宽度

    Returns:
        进度条字符串，如 "[████░░░░]"
    """
    filled = int(pct * width / 100)
    empty = width - filled
    return "[" + "█" * filled + "░" * empty + "]"


def strip_ansi(text: str) -> str:
    """
    移除 ANSI 转义码

    Args:
        text: 包含 ANSI 码的文本

    Returns:
        移除 ANSI 码后的纯文本
    """
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


def visible_len(text: str) -> int:
    """
    计算文本的可见长度（不计入 ANSI 码）

    Args:
        text: 文本

    Returns:
        可见长度
    """
    return len(strip_ansi(text))


def join_parts(parts: list[str], *, sep: str = " ") -> str:
    """
    连接文本部分，过滤空字符串

    Args:
        parts: 文本部分列表
        sep: 分隔符

    Returns:
        连接后的文本
    """
    return sep.join(p for p in parts if p)
