"""
SQLite 数据库适配器

使用 aiosqlite 实现异步 SQLite 操作，支持：
- WAL 模式（多进程并发读写）
- 连接池
- JSON 函数
- 向量搜索扩展
"""

import asyncio
import os
import threading
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from lib.db.adapters.base import BaseAdapter
from lib.db.core import DatabaseConfig


class SQLiteConnectionPool:
    _instance = None
    _lock = threading.Lock()

    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self._pool: List = []
        self._semaphore = asyncio.Semaphore(pool_size)
        self._lock = asyncio.Lock()
        self._initialized = False

    @classmethod
    def get_instance(cls, db_path: str, pool_size: int = 5) -> "SQLiteConnectionPool":
        with cls._lock:
            if cls._instance is None or cls._instance.db_path != db_path:
                cls._instance = cls(db_path, pool_size)
            return cls._instance

    async def initialize(self):
        if self._initialized:
            return

        async with self._lock:
            if self._initialized:
                return

            import aiosqlite

            for _ in range(self.pool_size):
                conn = await aiosqlite.connect(self.db_path)
                conn.row_factory = aiosqlite.Row
                await self._configure_connection(conn)
                self._pool.append(conn)

            self._initialized = True

    async def _configure_connection(self, conn):
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA synchronous=NORMAL")
        await conn.execute("PRAGMA cache_size=-64000")
        await conn.execute("PRAGMA temp_store=MEMORY")
        await conn.execute("PRAGMA mmap_size=268435456")
        await conn.execute("PRAGMA busy_timeout=30000")

    @asynccontextmanager
    async def acquire(self):
        await self._semaphore.acquire()
        try:
            async with self._lock:
                if self._pool:
                    conn = self._pool.pop()
                else:
                    import aiosqlite

                    conn = await aiosqlite.connect(self.db_path)
                    conn.row_factory = aiosqlite.Row
                    await self._configure_connection(conn)
            yield conn
        finally:
            async with self._lock:
                self._pool.append(conn)
            self._semaphore.release()

    async def close(self):
        async with self._lock:
            for conn in self._pool:
                await conn.close()
            self._pool.clear()
            self._initialized = False


class SQLiteAdapter(BaseAdapter):
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self._pool: Optional[SQLiteConnectionPool] = None
        self._connection = None
        self._json_enabled = False
        self._vector_enabled = False

    async def connect(self) -> None:
        try:
            import aiosqlite
        except ImportError:
            raise ImportError("请安装 aiosqlite: pip install aiosqlite")

        db_path = self.config.path
        if db_path and db_path != ":memory:":
            os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)

        if db_path == ":memory:":
            self._connection = await aiosqlite.connect(db_path)
            self._connection.row_factory = aiosqlite.Row
            await self._configure_connection(self._connection)
        else:
            pool_size = self.config.pool_size or 5
            self._pool = SQLiteConnectionPool.get_instance(db_path, pool_size)
            await self._pool.initialize()

        await self._check_features()

    async def _configure_connection(self, conn):
        await conn.execute("PRAGMA journal_mode=WAL")
        await conn.execute("PRAGMA synchronous=NORMAL")
        await conn.execute("PRAGMA cache_size=-64000")
        await conn.execute("PRAGMA temp_store=MEMORY")
        await conn.execute("PRAGMA mmap_size=268435456")
        await conn.execute("PRAGMA busy_timeout=30000")

    async def _check_features(self):
        try:
            await self.execute("SELECT json('{}')")
            self._json_enabled = True
        except Exception:
            self._json_enabled = False

        try:
            await self.execute("SELECT vec_version()")
            self._vector_enabled = True
        except Exception:
            self._vector_enabled = False

    @property
    def json_enabled(self) -> bool:
        return self._json_enabled

    @property
    def vector_enabled(self) -> bool:
        return self._vector_enabled

    async def load_vector_extension(self, extension_path: Optional[str] = None) -> bool:
        if self._vector_enabled:
            return True

        try:
            if self._pool:
                async with self._pool.acquire() as conn:
                    await conn.enable_load_extension(True)
                    if extension_path:
                        await conn.load_extension(extension_path)
                    else:
                        possible_paths = [
                            "vec0",
                            "sqlite_vec",
                            "/usr/local/lib/sqlite3/vec0",
                            "/usr/lib/sqlite3/vec0",
                        ]
                        for path in possible_paths:
                            try:
                                await conn.load_extension(path)
                                break
                            except Exception:
                                continue
                    await conn.enable_load_extension(False)
            elif self._connection:
                await self._connection.enable_load_extension(True)
                if extension_path:
                    await self._connection.load_extension(extension_path)
                else:
                    possible_paths = [
                        "vec0",
                        "sqlite_vec",
                        "/usr/local/lib/sqlite3/vec0",
                        "/usr/lib/sqlite3/vec0",
                    ]
                    for path in possible_paths:
                        try:
                            await self._connection.load_extension(path)
                            break
                        except Exception:
                            continue
                await self._connection.enable_load_extension(False)

            await self._check_features()
            return self._vector_enabled
        except Exception as e:
            self._vector_enabled = False
            return False

    @property
    def is_connected(self) -> bool:
        if self._pool is not None:
            return self._pool._initialized
        return self._connection is not None

    @asynccontextmanager
    async def _get_connection(self):
        if self._pool:
            async with self._pool.acquire() as conn:
                yield conn
        else:
            yield self._connection

    async def disconnect(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None
        if self._connection:
            await self._connection.close()
            self._connection = None

    async def execute(self, sql: str, params: Optional[tuple] = None) -> Any:
        async with self._get_connection() as conn:
            cursor = await conn.execute(sql, params or ())
            if not self._in_transaction:
                await conn.commit()
            return cursor

    async def fetch_one(self, sql: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
        async with self._get_connection() as conn:
            cursor = await conn.execute(sql, params or ())
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def fetch_all(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        async with self._get_connection() as conn:
            cursor = await conn.execute(sql, params or ())
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

    async def json_extract(self, column: str, path: str) -> str:
        if not self._json_enabled:
            raise RuntimeError("SQLite JSON 函数不可用，请升级 SQLite 到 3.38+ 版本")
        return f"json_extract({column}, '{path}')"

    async def json_array_length(self, column: str) -> str:
        if not self._json_enabled:
            raise RuntimeError("SQLite JSON 函数不可用，请升级 SQLite 到 3.38+ 版本")
        return f"json_array_length({column})"

    async def json_each(self, column: str) -> str:
        if not self._json_enabled:
            raise RuntimeError("SQLite JSON 函数不可用，请升级 SQLite 到 3.38+ 版本")
        return f"json_each({column})"

    async def create_vector_table(
        self,
        table_name: str,
        vector_column: str,
        dimensions: int,
        additional_columns: Optional[Dict[str, str]] = None,
    ) -> None:
        if not self._vector_enabled:
            raise RuntimeError("向量搜索扩展未加载，请先调用 load_vector_extension()")

        columns = []
        if additional_columns:
            for col_name, col_type in additional_columns.items():
                columns.append(f"{self.quote_identifier(col_name)} {col_type}")

        columns.append(f"{self.quote_identifier(vector_column)} BLOB")

        sql = f"CREATE TABLE IF NOT EXISTS {self.quote_identifier(table_name)} ({', '.join(columns)})"
        await self.execute(sql)

        index_sql = f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS {self.quote_identifier(f'{table_name}_vec_idx')}
            USING vec0(
                {self.quote_identifier(vector_column)} float[{dimensions}]
            )
        """
        await self.execute(index_sql)

    async def insert_vector(
        self,
        table_name: str,
        vector_column: str,
        vector: List[float],
        **kwargs,
    ) -> int:
        import struct

        vector_blob = struct.pack(f"{len(vector)}f", *vector)

        columns = [self.quote_identifier(vector_column)]
        placeholders = ["?"]
        values = [vector_blob]

        for key, value in kwargs.items():
            columns.append(self.quote_identifier(key))
            placeholders.append("?")
            values.append(value)

        sql = f"INSERT INTO {self.quote_identifier(table_name)} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        result = await self.execute(sql, tuple(values))
        return result.lastrowid

    async def vector_search(
        self,
        table_name: str,
        vector_column: str,
        query_vector: List[float],
        limit: int = 10,
        where: Optional[str] = None,
        params: Optional[tuple] = None,
    ) -> List[Dict[str, Any]]:
        if not self._vector_enabled:
            raise RuntimeError("向量搜索扩展未加载，请先调用 load_vector_extension()")

        import struct

        query_blob = struct.pack(f"{len(query_vector)}f", *query_vector)

        sql = f"""
            SELECT 
                t.*,
                v.distance
            FROM {self.quote_identifier(table_name)} t
            JOIN {self.quote_identifier(f'{table_name}_vec_idx')} v
                ON t.rowid = v.rowid
            WHERE v.{self.quote_identifier(vector_column)} MATCH ?
                AND v.k = ?
        """

        search_params = [query_blob, limit]

        if where:
            sql += f" AND {where}"
            if params:
                search_params.extend(params)

        sql += f" ORDER BY v.distance LIMIT {limit}"

        return await self.fetch_all(sql, tuple(search_params))

    async def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        if not self._vector_enabled:
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            norm1 = sum(a * a for a in vec1) ** 0.5
            norm2 = sum(b * b for b in vec2) ** 0.5
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return dot_product / (norm1 * norm2)

        import struct

        blob1 = struct.pack(f"{len(vec1)}f", *vec1)
        blob2 = struct.pack(f"{len(vec2)}f", *vec2)

        sql = "SELECT vec_distance_cosine(?, ?) as similarity"
        row = await self.fetch_one(sql, (blob1, blob2))
        return row["similarity"] if row else 0.0
