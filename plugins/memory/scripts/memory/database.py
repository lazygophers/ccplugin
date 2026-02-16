"""
数据库管理模块

提供数据库初始化和连接管理功能。
"""

import hashlib
import os

from lib import logging
from lib.db import DatabaseConfig, DatabaseConnection
from lib.utils import get_project_plugins_dir, get_project_dir
from lib.utils.gitignore import add_gitignore_rule

from .models import (
    Memory,
    MemoryPath,
    MemoryVersion,
    MemoryRelation,
    Session,
    ErrorSolution,
)


_db_initialized = False


def get_db_path() -> str:
    """
    获取数据库文件路径

    数据库存储在项目根目录下的 .lazygophers/ccplugin/memory/memory.db，
    遵循项目约定的插件数据存储规范。

    Returns:
        str: 数据库文件的绝对路径
    """
    return os.path.join(get_project_plugins_dir(), "memory", "memory.db")


def compute_hash(content: str) -> str:
    """
    计算内容的 SHA256 哈希值

    用于快速比较内容是否变化，避免不必要的版本记录。

    Args:
        content: 需要计算哈希的内容字符串

    Returns:
        str: 64 位十六进制哈希字符串
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


async def init_db() -> None:
    """
    初始化数据库连接和表结构

    创建数据库文件目录（如不存在），初始化数据库连接，
    并创建所有必要的表结构。此函数是幂等的，多次调用不会重复创建。

    注意:
        必须在使用任何数据库操作前调用此函数。
    """
    global _db_initialized

    if _db_initialized:
        return

    db_path = get_db_path()
    project_dir = get_project_dir()
    if project_dir:
        gitignore_path = os.path.join(project_dir, ".gitignore")
        add_gitignore_rule(gitignore_path, "/.lazygophers/ccplugin/memory/")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    config = DatabaseConfig.sqlite(path=db_path)
    await DatabaseConnection.initialize(config)

    await Memory.create_table(if_not_exists=True)
    await MemoryPath.create_table(if_not_exists=True)
    await MemoryVersion.create_table(if_not_exists=True)
    await MemoryRelation.create_table(if_not_exists=True)
    await Session.create_table(if_not_exists=True)
    await ErrorSolution.create_table(if_not_exists=True)

    _db_initialized = True
    logging.info(f"数据库初始化完成: {db_path}")


async def close_db() -> None:
    """
    关闭数据库连接

    释放数据库资源，重置初始化状态。
    通常在程序退出前调用。
    """
    global _db_initialized
    if _db_initialized:
        await DatabaseConnection.close()
        _db_initialized = False