"""
Statusline 模块

提供模块化、可扩展的状态栏显示功能。
"""

__version__ = "2.0.0"
__author__ = "Claude Code Plugin"

from .config.manager import ConfigManager, Config, get_default_config

__all__ = [
    "ConfigManager",
    "Config",
    "get_default_config",
]
