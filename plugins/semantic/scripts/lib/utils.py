"""
Semantic Plugin Utilities Module
语义搜索插件的工具函数
"""

from pathlib import Path
from typing import Optional

from .config import get_data_path, get_config_path

# 常量定义
LANCEDB_DIR = "lancedb"


def check_and_auto_init(silent: bool = False) -> bool:
    """检查 Semantic 初始化状态

    在 MCP 服务器中，这个函数只检查目录结构，
    不执行实际的初始化流程。MCP 服务器可以在未初始化的情况下运行，
    只是索引会为空。

    Args:
        silent: 是否静默模式（保持接口兼容）

    Returns:
        始终返回 True，表示检查完成且服务器可以运行
    """
    # 在 MCP 服务器环境中，我们允许在未初始化的情况下运行
    # 实际的索引检查会在搜索时进行
    return True


__all__ = ["check_and_auto_init"]
