"""工具函数模块"""
from pathlib import Path
from typing import Union

TASK_DIR = Path(".lazygophers/tasks")


def format_duration(seconds: Union[int, float]) -> str:
    """将秒数转换为人类可读的时间格式

    Args:
        seconds: 秒数

    Returns:
        人类可读格式，如 "1h 30m 45s"、"5m 30s"、"45s"
    """
    if seconds < 60:
        return f"{seconds:.0f}s"

    minutes, remainder = divmod(int(seconds), 60)
    if minutes < 60:
        return f"{minutes}m {remainder}s"

    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m {remainder}s"


def get_task_dir() -> Path:
    """返回任务数据目录路径"""
    return TASK_DIR


# ── 以下自 lib/utils 内联 (lib/ 已删, scripts 自包含) ──────────────────────
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple


def get_project_dir() -> str:
    return os.getenv("CLAUDE_PROJECT_DIR", default=os.getcwd())


def parse_version(version_str: str) -> Tuple[int, int, int]:
    """版本串 → (major, minor, patch) 三元组, 缺位补 0, 非法回落 (0,0,0)。"""
    try:
        parts = version_str.split(".")
        if len(parts) >= 3:
            return (int(parts[0]), int(parts[1]), int(parts[2]))
        elif len(parts) == 2:
            return (int(parts[0]), int(parts[1]), 0)
        elif len(parts) == 1:
            return (int(parts[0]), 0, 0)
    except (ValueError, AttributeError):
        pass
    return (0, 0, 0)


def format_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


def format_timestamp(timestamp_str: Optional[str]) -> str:
    """ISO 时间戳 → 相对时间 (5m ago / 2h ago / 3d ago), 超一周回落绝对日期。"""
    if not timestamp_str:
        return "[dim]N/A[/dim]"
    try:
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        if delta.days < 1:
            hours = delta.seconds // 3600
            if hours < 1:
                return f"[cyan]{delta.seconds // 60}m ago[/cyan]"
            return f"[cyan]{hours}h ago[/cyan]"
        elif delta.days < 7:
            return f"[cyan]{delta.days}d ago[/cyan]"
        return dt.strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        return str(timestamp_str)


def safe_load_json(file_path: Path) -> Optional[Dict[str, Any]]:
    if not file_path.exists():
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError, OSError):
        return None


def print_help(parser: Any, console: Any = None) -> None:
    """argparse parser → rich 美化帮助输出 (面板 + 选项/位置参数表)。"""
    from rich import box
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    if console is None:
        from rich.console import Console
        console = Console()

    prog = parser.prog or "script"
    description = parser.description or ""
    console.print(Panel.fit(
        f"[bold cyan]{prog}[/bold cyan]\n[dim]{description}[/dim]"
        if description else f"[bold cyan]{prog}[/bold cyan]",
        border_style="blue", box=box.DOUBLE))
    console.print()

    usage = parser.format_usage().strip()
    if usage:
        usage_text = Text()
        usage_text.append("用法: ", style="bold yellow")
        usage_text.append(usage.replace("usage: ", "").strip(), style="white")
        console.print(usage_text)
        console.print()

    positionals = [a for a in parser._actions if a.dest != "help" and not a.option_strings]
    optionals = [a for a in parser._actions if a.option_strings]

    if optionals:
        console.print("[bold]选项:[/bold]")
        table = Table(show_header=False, box=box.ROUNDED, padding=(0, 2))
        table.add_column("Option", style="cyan", no_wrap=True, width=20)
        table.add_column("Description", style="white")
        for action in optionals:
            opts = ", ".join(action.option_strings)
            if action.metavar:
                opts += f" [yellow]{action.metavar}[/yellow]"
            elif action.nargs not in (None, 0):
                opts += f" [yellow]{action.dest.upper()}[/yellow]"
            table.add_row(opts, action.help or "")
        console.print(table)
        console.print()

    if positionals:
        console.print("[bold]位置参数:[/bold]")
        table = Table(show_header=False, box=box.ROUNDED, padding=(0, 2))
        table.add_column("Argument", style="cyan", no_wrap=True, width=20)
        table.add_column("Description", style="white")
        for action in positionals:
            table.add_row(action.metavar or action.dest, action.help or "")
        console.print(table)
        console.print()

    console.print("[dim]使用 --help 查看此帮助信息[/dim]")


# 进度动画常量 (原 lib.utils.constants)
LOADING_MESSAGES = [
    "🔍 正在搜索插件市场...",
    "📦 正在加载插件列表...",
    "🚀 正在获取最新数据...",
    "✨ 正在整理插件信息...",
    "🎯 正在匹配已安装插件...",
    "🌐 正在连接市场源...",
    "⚡ 正在加速数据传输...",
    "🔮 正在预测你的需求...",
    "🦄 正在召唤插件精灵...",
    "🌟 正在收集星光数据...",
    "🎭 正在准备精彩展示...",
    "🎪 正在搭建插件舞台...",
    "🔄 正在同步插件版本...",
    "💫 正在施展更新魔法...",
    "🎨 正在绘制更新蓝图...",
]
MESSAGE_CHANGE_PROBABILITY = 0.1
PROGRESS_THRESHOLD = 95
MIN_ADVANCE = 0.5
MAX_ADVANCE = 2.0
