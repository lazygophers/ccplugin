"""
日志设置工具 - 帮助脚本快速集成日志系统。
"""

import sys
from pathlib import Path
from typing import Optional


def setup_sys_path(script_file: Optional[str] = None, max_levels: int = 5) -> Path:
    """
    设置 sys.path 以支持导入根目录的 lib 模块。

    Args:
        script_file: 脚本文件路径（通常是 __file__）。如果为 None，使用调用者的 __file__
        max_levels: 最多向上查找的目录级数

    Returns:
        找到的项目根目录

    Example:
        ```python
        from lib.logging import setup_sys_path, setup_logger

        project_root = setup_sys_path(__file__)
        logger = setup_logger("my-plugin")
        ```
    """
    if script_file is None:
        # 获取调用者的文件路径
        import inspect
        frame = inspect.currentframe()
        if frame and frame.f_back:
            script_file = frame.f_back.f_globals.get('__file__')

    if script_file is None:
        raise ValueError("无法确定脚本文件路径")

    script_dir = Path(script_file).resolve().parent
    project_root = script_dir.parent.parent.parent

    # 检查是否存在 lib 目录
    if not (project_root / "lib").exists():
        # 向上查找直到找到 lib 目录
        current = script_dir
        for _ in range(max_levels):
            if (current / "lib").exists():
                project_root = current
                break
            parent = current.parent
            if parent == current:  # 到达根目录
                break
            current = parent

    # 将项目根目录添加到 sys.path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    return project_root


def setup_logger(plugin_name: str, enable_console: bool = True):
    """
    快速设置日志管理器。

    Args:
        plugin_name: 插件名称
        enable_console: 是否输出到控制台

    Returns:
        LogManager 实例

    Example:
        ```python
        from lib.logging import setup_sys_path, setup_logger

        setup_sys_path(__file__)
        logger = setup_logger("my-plugin")
        logger.info("Plugin started")
        ```
    """
    from .logger import get_logger

    return get_logger(plugin_name, enable_console)
