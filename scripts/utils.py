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
