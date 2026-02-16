"""
数据库适配器基类

提供通用的数据库操作实现。
"""

import asyncio
from typing import Any, Dict, List, Optional

from lib.db.core import DatabaseAdapter, DatabaseConfig


class BaseAdapter(DatabaseAdapter):
    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self._transaction_level = 0
        self._in_transaction = False

    async def begin(self) -> None:
        if self._transaction_level == 0:
            await self.execute("BEGIN")
            self._in_transaction = True
        self._transaction_level += 1

    async def commit(self) -> None:
        if self._transaction_level > 0:
            self._transaction_level -= 1
        if self._transaction_level == 0 and self._in_transaction:
            await self.execute("COMMIT")
            self._in_transaction = False

    async def rollback(self) -> None:
        self._transaction_level = 0
        if self._in_transaction:
            try:
                await self.execute("ROLLBACK")
            except Exception:
                pass
            self._in_transaction = False

    async def table_exists(self, table_name: str) -> bool:
        raise NotImplementedError

    async def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

    async def get_table_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        raise NotImplementedError
