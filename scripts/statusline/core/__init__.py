"""
核心逻辑模块

提供主循环和向后兼容功能。
"""

from .loop import StatuslineLoop
from .compat import CompatLayer, migrate_config

__all__ = [
    "StatuslineLoop",
    "CompatLayer",
    "migrate_config",
]
