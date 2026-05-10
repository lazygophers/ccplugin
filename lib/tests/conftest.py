"""
共享 pytest fixtures for lib/tests.

- 容器 fixtures (MySQL 8 / Postgres 16) 受 RUN_DB_INTEGRATION 环境变量控制；
  默认跳过，避免本地无 Docker 环境时阻塞单测运行。
- 单元测试用的 mock helpers 也集中在此。
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import pytest


def _integration_enabled() -> bool:
    return os.getenv("RUN_DB_INTEGRATION") == "1"


@pytest.fixture(scope="session")
def mysql_container():
    if not _integration_enabled():
        pytest.skip("integration tests gated by RUN_DB_INTEGRATION=1")
    try:
        from testcontainers.mysql import MySqlContainer
    except ImportError:
        pytest.skip("testcontainers[mysql] 未安装")

    container = MySqlContainer("mysql:8.0")
    container.start()
    try:
        yield {
            "host": container.get_container_host_ip(),
            "port": int(container.get_exposed_port(3306)),
            "username": container.username,
            "password": container.password,
            "database": container.dbname,
        }
    finally:
        container.stop()


@pytest.fixture(scope="session")
def postgres_container():
    if not _integration_enabled():
        pytest.skip("integration tests gated by RUN_DB_INTEGRATION=1")
    try:
        from testcontainers.postgres import PostgresContainer
    except ImportError:
        pytest.skip("testcontainers[postgres] 未安装")

    container = PostgresContainer("postgres:16-alpine")
    container.start()
    try:
        yield {
            "host": container.get_container_host_ip(),
            "port": int(container.get_exposed_port(5432)),
            "username": container.username,
            "password": container.password,
            "database": container.dbname,
        }
    finally:
        container.stop()


# ----------------------------- mock helpers --------------------------------


class FakeCursor:
    """Mimic aiomysql cursor's async-context-manager + execute/fetch interface."""

    def __init__(self, store: "FakeMySQLStore", dict_mode: bool = False):
        self._store = store
        self._dict_mode = dict_mode
        self.lastrowid: Optional[int] = None
        self.rowcount: int = 0
        self._last_rows: List[Dict[str, Any]] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def execute(self, sql: str, params: Optional[tuple] = None):
        self._store.executed.append((sql, params))
        # produce a deterministic response based on the SQL keyword.
        head = sql.strip().split(None, 1)[0].upper()
        if head == "SELECT":
            self._last_rows = self._store.next_rows()
            self.rowcount = len(self._last_rows)
        else:
            self._last_rows = []
            self.rowcount = 1
            self.lastrowid = self._store.next_lastrowid()
        return None

    async def fetchone(self):
        return self._last_rows[0] if self._last_rows else None

    async def fetchall(self):
        return list(self._last_rows)


class FakeMySQLStore:
    """Driver-level fake for aiomysql.connect()."""

    def __init__(self):
        self.executed: List[tuple] = []
        self._row_queue: List[List[Dict[str, Any]]] = []
        self._lastrowid_seq = 0
        self.closed = False

    def queue_rows(self, rows: List[Dict[str, Any]]):
        self._row_queue.append(rows)

    def next_rows(self) -> List[Dict[str, Any]]:
        return self._row_queue.pop(0) if self._row_queue else []

    def next_lastrowid(self) -> int:
        self._lastrowid_seq += 1
        return self._lastrowid_seq

    # aiomysql.Connection surface ------------------------------------------------
    def cursor(self, cursor_cls=None):
        return FakeCursor(self, dict_mode=cursor_cls is not None)

    def close(self):
        self.closed = True


class FakePGConn:
    """Driver-level fake for asyncpg.connect()."""

    def __init__(self):
        self.executed: List[tuple] = []
        self._row_queue: List[List[Dict[str, Any]]] = []
        self.closed = False

    def queue_rows(self, rows: List[Dict[str, Any]]):
        self._row_queue.append(rows)

    async def execute(self, sql: str, *params):
        self.executed.append((sql, params))
        return "OK"

    async def fetchrow(self, sql: str, *params):
        self.executed.append((sql, params))
        rows = self._row_queue.pop(0) if self._row_queue else []
        return rows[0] if rows else None

    async def fetch(self, sql: str, *params):
        self.executed.append((sql, params))
        return self._row_queue.pop(0) if self._row_queue else []

    async def close(self):
        self.closed = True
