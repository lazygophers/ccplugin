"""
系统通知模块
支持跨平台系统通知、hooks 处理和 MCP 服务器
"""

from .notifier import Notifier, notify

__all__ = [
    "Notifier",
    "notify",
]
