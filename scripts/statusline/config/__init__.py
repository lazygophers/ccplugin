"""
配置管理模块

提供配置管理、验证和默认值功能。
"""

from .manager import ConfigManager, Config, get_default_config

__all__ = [
    "ConfigManager",
    "Config",
    "get_default_config",
]
