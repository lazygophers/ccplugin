"""
Configuration Management Module
项目配置和路径管理

提供通用的配置加载、路径查找等功能
"""

from .path_manager import (
    get_data_path,
    get_config_path,
    load_config,
    DEFAULT_CONFIG,
)

__all__ = [
    "get_data_path",
    "get_config_path",
    "load_config",
    "DEFAULT_CONFIG",
]
