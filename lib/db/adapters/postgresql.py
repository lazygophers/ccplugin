"""
PostgreSQL 数据库适配器

使用 asyncpg 实现异步 PostgreSQL 操作。
"""

from typing import Any, Dict, List, Optional

from lib.db.adapters.base import BaseAdapter
from lib.db.core import DatabaseConfig


class PostgreSQLAdapter(BaseAdapter):
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)

    async def connect(self) -> None:
        try:
            import asyncpg
        except ImportError:
            raise ImportError("请安装 asyncpg: pip install asyncpg")

        self._connection = await asyncpg.connect(
            host=self.config.host,
            port=self.config.port,
            user=self.config.username,
            password=self.config.password,
            database=self.config.database,
            **self.config.extra,
        )

    async def disconnect(self) -> None:
        if self._connection:
            await self._connection.close()
            self._connection = None

    async def execute(self, sql: str, params: Optional[tuple] = None) -> Any:
        if not self._connection:
            raise RuntimeError("数据库未连接")

        return await self._connection.execute(sql, *(params or ()))

    async def fetch_one(self, sql: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
        if not self._connection:
            raise RuntimeError("数据库未连接")

        row = await self._connection.fetchrow(sql, *(params or ()))
        return dict(row) if row else None

    async def fetch_all(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        if not self._connection:
            raise RuntimeError("数据库未连接")

        rows = await self._connection.fetch(sql, *(params or ()))
        return [dict(row) for row in rows] if rows else []

    def get_placeholder(self) -> str:
        return "$%d"

    def quote_identifier(self, name: str) -> str:
        return f'"{name}"'

    def _build_placeholder_sql(self, sql: str, param_count: int) -> str:
        for i in range(1, param_count + 1):
            sql = sql.replace("?", f"${i}", 1)
        return sql

    async def execute_with_params(self, sql: str, params: tuple) -> Any:
        if not self._connection:
            raise RuntimeError("数据库未连接")

        formatted_sql = self._build_placeholder_sql(sql, len(params))
        return await self._connection.execute(formatted_sql, *params)

    async def fetch_one_with_params(self, sql: str, params: tuple) -> Optional[Dict[str, Any]]:
        if not self._connection:
            raise RuntimeError("数据库未连接")

        formatted_sql = self._build_placeholder_sql(sql, len(params))
        row = await self._connection.fetchrow(formatted_sql, *params)
        return dict(row) if row else None

    async def fetch_all_with_params(self, sql: str, params: tuple) -> List[Dict[str, Any]]:
        if not self._connection:
            raise RuntimeError("数据库未连接")

        formatted_sql = self._build_placeholder_sql(sql, len(params))
        rows = await self._connection.fetch(formatted_sql, *params)
        return [dict(row) for row in rows] if rows else []

    async def table_exists(self, table_name: str) -> bool:
        sql = """
            SELECT COUNT(*) as count
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = $1
        """
        row = await self._connection.fetchrow(sql, table_name)
        return row["count"] > 0 if row else False

    async def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        sql = """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = $1
            ORDER BY ordinal_position
        """
        rows = await self._connection.fetch(sql, table_name)
        return [
            {
                "name": row["column_name"],
                "type": row["data_type"],
                "nullable": row["is_nullable"] == "YES",
                "default": row["column_default"],
                "primary_key": False,
                "auto_increment": False,
                "length": row["character_maximum_length"],
                "precision": row["numeric_precision"],
                "scale": row["numeric_scale"],
            }
            for row in rows
        ]

    async def get_table_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        sql = """
            SELECT
                i.relname as index_name,
                a.attname as column_name,
                ix.indisunique as is_unique
            FROM pg_class t
            JOIN pg_index ix ON t.oid = ix.indrelid
            JOIN pg_class i ON i.oid = ix.indexrelid
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
            WHERE t.relname = $1
        """
        rows = await self._connection.fetch(sql, table_name)
        indexes = {}
        for row in rows:
            idx_name = row["index_name"]
            if idx_name not in indexes:
                indexes[idx_name] = {
                    "name": idx_name,
                    "columns": [],
                    "unique": row["is_unique"],
                }
            indexes[idx_name]["columns"].append(row["column_name"])
        return list(indexes.values())
