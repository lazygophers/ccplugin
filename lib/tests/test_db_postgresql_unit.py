"""
PostgreSQL 适配器单元测试 (mock asyncpg, 无需 Docker)。

覆盖目标：
- DatabaseConfig.postgresql() 工厂
- connect / disconnect / execute / fetch_*
- 占位符与双引号标识符
- $N 占位符替换 (_build_placeholder_sql)
- pg_catalog 索引内省、information_schema 列内省
- BaseAdapter 嵌套事务
- 注入安全 smoke
"""

from __future__ import annotations

import sys
import types

import pytest

from lib.db.adapters.postgresql import PostgreSQLAdapter
from lib.db.core import DatabaseConfig, DatabaseType


def test_postgres_config_factory_defaults():
    cfg = DatabaseConfig.postgresql(database="app")
    assert cfg.database_type == DatabaseType.POSTGRESQL
    assert cfg.port == 5432
    assert cfg.username == "postgres"


def test_placeholder_and_quote_identifier():
    adapter = PostgreSQLAdapter(DatabaseConfig.postgresql(database="t"))
    assert adapter.get_placeholder() == "$%d"
    assert adapter.quote_identifier("Users") == '"Users"'


def test_build_placeholder_sql_replaces_question_marks():
    adapter = PostgreSQLAdapter(DatabaseConfig.postgresql(database="t"))
    sql = "SELECT * FROM t WHERE a = ? AND b = ? AND c = ?"
    out = adapter._build_placeholder_sql(sql, 3)
    assert out == "SELECT * FROM t WHERE a = $1 AND b = $2 AND c = $3"


@pytest.fixture
def patched_asyncpg(monkeypatch):
    """Inject a fake `asyncpg` module so the local `import asyncpg` inside connect succeeds."""
    from lib.tests.conftest import FakePGConn

    conn = FakePGConn()
    fake = types.ModuleType("asyncpg")

    async def _connect(**kwargs):
        conn.connect_kwargs = kwargs
        return conn

    fake.connect = _connect
    monkeypatch.setitem(sys.modules, "asyncpg", fake)
    return conn


async def test_connect_passes_basic_args(patched_asyncpg):
    adapter = PostgreSQLAdapter(DatabaseConfig.postgresql(
        host="db", port=5433, username="u", password="p", database="x"))
    await adapter.connect()
    kw = patched_asyncpg.connect_kwargs
    assert kw["host"] == "db"
    assert kw["port"] == 5433
    assert kw["user"] == "u"
    assert kw["database"] == "x"


async def test_connect_raises_when_driver_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "asyncpg", None)
    adapter = PostgreSQLAdapter(DatabaseConfig.postgresql(database="x"))
    with pytest.raises(ImportError):
        await adapter.connect()


async def test_disconnect_closes(patched_asyncpg):
    adapter = PostgreSQLAdapter(DatabaseConfig.postgresql(database="x"))
    await adapter.connect()
    await adapter.disconnect()
    assert patched_asyncpg.closed is True
    assert adapter._connection is None


async def test_execute_unpacks_params_to_positional(patched_asyncpg):
    adapter = PostgreSQLAdapter(DatabaseConfig.postgresql(database="x"))
    await adapter.connect()
    await adapter.execute("INSERT INTO t VALUES ($1, $2)", ("a", 1))
    sql, params = patched_asyncpg.executed[-1]
    assert sql.startswith("INSERT")
    assert params == ("a", 1)


async def test_fetch_one_returns_dict(patched_asyncpg):
    adapter = PostgreSQLAdapter(DatabaseConfig.postgresql(database="x"))
    await adapter.connect()
    patched_asyncpg.queue_rows([{"id": 1, "name": "a"}])
    row = await adapter.fetch_one("SELECT id, name FROM t WHERE id = $1", (1,))
    assert row == {"id": 1, "name": "a"}


async def test_fetch_all_returns_list(patched_asyncpg):
    adapter = PostgreSQLAdapter(DatabaseConfig.postgresql(database="x"))
    await adapter.connect()
    patched_asyncpg.queue_rows([{"id": 1}, {"id": 2}])
    rows = await adapter.fetch_all("SELECT id FROM t")
    assert rows == [{"id": 1}, {"id": 2}]


async def test_execute_without_connection_raises():
    adapter = PostgreSQLAdapter(DatabaseConfig.postgresql(database="x"))
    with pytest.raises(RuntimeError):
        await adapter.execute("SELECT 1")


async def test_table_exists(patched_asyncpg):
    adapter = PostgreSQLAdapter(DatabaseConfig.postgresql(database="x"))
    await adapter.connect()
    patched_asyncpg.queue_rows([{"count": 1}])
    assert await adapter.table_exists("users") is True
    last_sql, last_params = patched_asyncpg.executed[-1]
    assert "information_schema.tables" in last_sql
    assert last_params == ("users",)


async def test_get_table_columns(patched_asyncpg):
    adapter = PostgreSQLAdapter(DatabaseConfig.postgresql(database="x"))
    await adapter.connect()
    patched_asyncpg.queue_rows([
        {
            "column_name": "id", "data_type": "integer", "is_nullable": "NO",
            "column_default": "nextval('users_id_seq')",
            "character_maximum_length": None,
            "numeric_precision": 32, "numeric_scale": 0,
        },
        {
            "column_name": "email", "data_type": "character varying", "is_nullable": "YES",
            "column_default": None, "character_maximum_length": 255,
            "numeric_precision": None, "numeric_scale": None,
        },
    ])
    cols = await adapter.get_table_columns("users")
    assert cols[0]["name"] == "id"
    assert cols[0]["nullable"] is False
    assert cols[1]["length"] == 255


async def test_get_table_indexes_uses_pg_catalog(patched_asyncpg):
    adapter = PostgreSQLAdapter(DatabaseConfig.postgresql(database="x"))
    await adapter.connect()
    patched_asyncpg.queue_rows([
        {"index_name": "users_pkey", "column_name": "id", "is_unique": True},
        {"index_name": "users_name_idx", "column_name": "name", "is_unique": False},
        {"index_name": "users_name_idx", "column_name": "email", "is_unique": False},
    ])
    indexes = await adapter.get_table_indexes("users")
    last_sql, _ = patched_asyncpg.executed[-1]
    assert "pg_class" in last_sql and "pg_index" in last_sql
    by_name = {i["name"]: i for i in indexes}
    assert by_name["users_pkey"]["unique"] is True
    assert by_name["users_name_idx"]["columns"] == ["name", "email"]


# ---- with_params helpers --------------------------------------------------


async def test_execute_with_params_rewrites_question_marks(patched_asyncpg):
    adapter = PostgreSQLAdapter(DatabaseConfig.postgresql(database="x"))
    await adapter.connect()
    await adapter.execute_with_params("SELECT * FROM t WHERE a = ? AND b = ?", ("x", "y"))
    sql, params = patched_asyncpg.executed[-1]
    assert "$1" in sql and "$2" in sql and "?" not in sql
    assert params == ("x", "y")


async def test_fetch_one_with_params(patched_asyncpg):
    adapter = PostgreSQLAdapter(DatabaseConfig.postgresql(database="x"))
    await adapter.connect()
    patched_asyncpg.queue_rows([{"id": 7}])
    row = await adapter.fetch_one_with_params("SELECT * FROM t WHERE id = ?", (7,))
    assert row == {"id": 7}


async def test_fetch_all_with_params(patched_asyncpg):
    adapter = PostgreSQLAdapter(DatabaseConfig.postgresql(database="x"))
    await adapter.connect()
    patched_asyncpg.queue_rows([{"id": 1}, {"id": 2}])
    rows = await adapter.fetch_all_with_params("SELECT * FROM t WHERE x = ?", ("v",))
    assert len(rows) == 2


# ---- 嵌套事务 -------------------------------------------------------------


async def test_transaction_nesting_depth_two(patched_asyncpg):
    adapter = PostgreSQLAdapter(DatabaseConfig.postgresql(database="x"))
    await adapter.connect()
    await adapter.begin()
    await adapter.begin()
    await adapter.commit()
    await adapter.commit()
    issued = [sql for sql, _ in patched_asyncpg.executed]
    assert issued.count("BEGIN") == 1
    assert issued.count("COMMIT") == 1


async def test_transaction_rollback_clears_depth(patched_asyncpg):
    adapter = PostgreSQLAdapter(DatabaseConfig.postgresql(database="x"))
    await adapter.connect()
    await adapter.begin()
    await adapter.begin()
    await adapter.begin()
    await adapter.rollback()
    await adapter.commit()  # no-op
    issued = [sql for sql, _ in patched_asyncpg.executed]
    assert issued.count("BEGIN") == 1
    assert issued.count("ROLLBACK") == 1
    assert "COMMIT" not in issued


# ---- 注入安全 smoke -------------------------------------------------------


async def test_parameterized_query_keeps_payload_separate(patched_asyncpg):
    adapter = PostgreSQLAdapter(DatabaseConfig.postgresql(database="x"))
    await adapter.connect()
    payload = "'; DROP TABLE users;--"
    await adapter.execute("SELECT * FROM users WHERE name = $1", (payload,))
    sql, params = patched_asyncpg.executed[-1]
    assert payload not in sql
    assert params == (payload,)
