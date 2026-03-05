"""
数据库适配器工厂

根据数据库类型创建对应的适配器实例。
"""

from lib.db.core import DatabaseAdapter, DatabaseConfig, DatabaseType


def create_adapter(config: DatabaseConfig) -> DatabaseAdapter:
    from lib.db.adapters.mysql import MySQLAdapter  # noqa: F401
    from lib.db.adapters.postgresql import PostgreSQLAdapter  # noqa: F401
    from lib.db.adapters.sqlite import SQLiteAdapter  # noqa: F401

    adapter_map = {
        DatabaseType.MYSQL: MySQLAdapter,
        DatabaseType.SQLITE: SQLiteAdapter,
        DatabaseType.POSTGRESQL: PostgreSQLAdapter,
    }

    adapter_class = adapter_map.get(config.database_type)
    if adapter_class is None:
        raise ValueError(f"不支持的数据库类型: {config.database_type}")

    return adapter_class(config)


# 导入适配器类供外部使用
from lib.db.adapters.base import BaseAdapter  # noqa: E402
from lib.db.adapters.mysql import MySQLAdapter  # noqa: E402
from lib.db.adapters.postgresql import PostgreSQLAdapter  # noqa: E402
from lib.db.adapters.sqlite import SQLiteAdapter  # noqa: E402

__all__ = [
    "create_adapter",
    "BaseAdapter",
    "MySQLAdapter",
    "SQLiteAdapter",
    "PostgreSQLAdapter",
]
