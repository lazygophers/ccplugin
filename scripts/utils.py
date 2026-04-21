"""工具函数模块"""
from pathlib import Path

TASK_DIR = Path(".lazygophers/tasks")


def get_task_dir() -> Path:
    """返回任务数据目录路径"""
    return TASK_DIR
