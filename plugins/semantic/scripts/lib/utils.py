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
    """检查并自动初始化 Semantic

    在 MCP 服务器中，这个函数只检查是否已初始化，
    不执行完整的初始化流程。如果未初始化，只返回 False。

    Args:
        silent: 是否静默模式（目前未使用，保持接口兼容）

    Returns:
        是否已初始化且准备就绪（配置文件存在）
    """
    config_path = get_config_path()

    # 检查是否已初始化（config.yaml 存在）
    if not config_path.exists():
        return False  # 未初始化

    # 检查数据目录
    data_path = get_data_path()
    if not data_path.exists():
        return False

    return True  # 已初始化


__all__ = ["check_and_auto_init"]
