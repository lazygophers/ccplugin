"""
日志管理模块。

提供统一的日志记录功能，支持：
- 按小时自动分片
- 日志轮转和保留策略
- 控制台和文件双输出
- 软连接管理
"""

from .logger import get_logger, LogManager
from .setup_utils import setup_sys_path, setup_logger

__all__ = ["get_logger", "LogManager", "setup_sys_path", "setup_logger"]
