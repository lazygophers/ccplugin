"""
MySQL 数据库适配器

使用 aiomysql 实现异步 MySQL 操作。
"""

from typing import Any, Dict, List, Optional

from lib.db.adapters.base import BaseAdapter
from lib.db.core import DatabaseConfig


class MySQLAdapter(BaseAdapter):
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self._cursor = None

    async def connect(self) -> None:
        try:
            import aiomysql
        except ImportError:
            raise ImportError("请安装 aiomysql: pip install aiomysql")

        self._connection = await aiomysql.connect(
            host=self.config.host,
            port=self.config.port,
            user=self.config.username,
            password=self.config.password,
            db=self.config.database,
            charset="utf8mb4",
            autocommit=True,
            **self.config.extra,
        )

    async def disconnect(self) -> None:
        if self._connection:
            self._connection.close()
            self._connection = None

    async def execute(self, sql: str, params: Optional[tuple] = None) -> Any:
        if not self._connection:
            raise RuntimeError("数据库未连接")

        async with self._connection.cursor() as cursor:
            await cursor.execute(sql, params)
            return cursor

    async def fetch_one(self, sql: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
        if not self._connection:
            raise RuntimeError("数据库未连接")

        async with self._connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(sql, params)
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def fetch_all(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        if not self._connection:
            raise RuntimeError("数据库未连接")

        async with self._connection.cursor(aiomysql.DictCursor) as cursor:
            await cursor.execute(sql, params)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows] if rows else []

    def get_placeholder(self) -> str:
        return "%s"

    def quote_identifier(self, name: str) -> str:
        return f"`{name}`"

    async def table_exists(self, table_name: str) -> bool:
        sql = """
            SELECT COUNT(*) as count
            FROM information_schema.tables
            WHERE table_schema = %s AND table_name = %s
        """
        row = await self.fetch_one(sql, (self.config.database, table_name))
        return row["count"] > 0 if row else False

    async def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        sql = """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default,
                column_key,
                extra,
                character_maximum_length,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """
        rows = await self.fetch_all(sql, (self.config.database, table_name))
        return [
            {
                "name": row["column_name"],
                "type": row["data_type"],
                "nullable": row["is_nullable"] == "YES",
                "default": row["column_default"],
                "primary_key": row["column_key"] == "PRI",
                "auto_increment": "auto_increment" in (row["extra"] or ""),
                "length": row["character_maximum_length"],
                "precision": row["numeric_precision"],
                "scale": row["numeric_scale"],
            }
            for row in rows
        ]

    async def get_table_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        sql = """
            SELECT
                index_name,
                column_name,
                non_unique
            FROM information_schema.statistics
            WHERE table_schema = %s AND table_name = %s
            ORDER by index_name, seq_in_index
        """
        rows = await self.fetch_all(sql, (self.config.database, table_name))
        indexes = {}
        for row in rows:
            idx_name = row["index_name"]
            if idx_name not in indexes:
                indexes[idx_name] = {
                    "name": idx_name,
                    "columns": [],
                    "unique": row["non_unique"] == 0,
                }
            indexes[idx_name]["columns"].append(row["column_name"])
        return list(indexes.values())
