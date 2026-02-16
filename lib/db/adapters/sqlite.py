"""
SQLite 数据库适配器

使用 aiosqlite 实现异步 SQLite 操作。
"""

import os
from typing import Any, Dict, List, Optional

from lib.db.adapters.base import BaseAdapter
from lib.db.core import DatabaseConfig


class SQLiteAdapter(BaseAdapter):
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)

    async def connect(self) -> None:
        try:
            import aiosqlite
        except ImportError:
            raise ImportError("请安装 aiosqlite: pip install aiosqlite")

        db_path = self.config.path
        if db_path:
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self._connection = await aiosqlite.connect(db_path or ":memory:")
        self._connection.row_factory = aiosqlite.Row

    async def disconnect(self) -> None:
        if self._connection:
            await self._connection.close()
            self._connection = None

    async def execute(self, sql: str, params: Optional[tuple] = None) -> Any:
        if not self._connection:
            raise RuntimeError("数据库未连接")

        cursor = await self._connection.execute(sql, params or ())
        if not self._in_transaction:
            await self._connection.commit()
        return cursor

    async def fetch_one(self, sql: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
        if not self._connection:
            raise RuntimeError("数据库未连接")

        cursor = await self._connection.execute(sql, params or ())
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def fetch_all(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        if not self._connection:
            raise RuntimeError("数据库未连接")

        cursor = await self._connection.execute(sql, params or ())
        rows = await cursor.fetchall()
        return [dict(row) for row in rows] if rows else []

    def get_placeholder(self) -> str:
        return "?"

    def quote_identifier(self, name: str) -> str:
        return f'"{name}"'

    async def table_exists(self, table_name: str) -> bool:
        sql = """
            SELECT COUNT(*) as count
            FROM sqlite_master
            WHERE type = 'table' AND name = ?
        """
        row = await self.fetch_one(sql, (table_name,))
        return row["count"] > 0 if row else False

    async def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        sql = f"PRAGMA table_info({self.quote_identifier(table_name)})"
        rows = await self.fetch_all(sql)
        return [
            {
                "name": row["name"],
                "type": row["type"],
                "nullable": row["notnull"] == 0,
                "default": row["dflt_value"],
                "primary_key": row["pk"] == 1,
                "auto_increment": False,
            }
            for row in rows
        ]

    async def get_table_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        sql = f"PRAGMA index_list({self.quote_identifier(table_name)})"
        indexes = await self.fetch_all(sql)

        result = []
        for idx in indexes:
            idx_sql = f"PRAGMA index_info({self.quote_identifier(idx['name'])})"
            columns = await self.fetch_all(idx_sql)
            result.append(
                {
                    "name": idx["name"],
                    "columns": [col["name"] for col in columns],
                    "unique": idx["unique"] == 1,
                }
            )
        return result
