"""
系统通知模块
支持跨平台系统通知、语音播报、hooks 处理和 MCP 服务器
"""

from .notifier import Notifier, notify, speak
from .init_config import init_notify_config, get_effective_config

__all__ = [
    "Notifier",
    "notify",
    "speak",
    "init_notify_config",
    "get_effective_config",
]
