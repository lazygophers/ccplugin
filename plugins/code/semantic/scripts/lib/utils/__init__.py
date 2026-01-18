"""
Utilities Module
通用工具函数库

提供跨插件使用的通用工具函数，包括：
- 初始化检查
- 目录操作
- 数据验证
- 格式转换
"""

from .helpers import check_and_auto_init

__all__ = [
    "check_and_auto_init",
]
