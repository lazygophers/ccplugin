"""
MySQL 适配器单元测试 (mock 驱动层，无需 Docker)。

覆盖目标：
- DatabaseConfig.mysql() 工厂
- MySQLAdapter.connect / disconnect
- execute / fetch_one / fetch_all 调用 aiomysql 的方式
- 占位符与标识符引号
- table_exists / get_table_columns / get_table_indexes 的 SQL 形态
- BaseAdapter 嵌套事务在不同深度的行为
"""

from __future__ import annotations

import pytest

from lib.db.adapters.mysql import MySQLAdapter
from lib.db.core import DatabaseConfig, DatabaseType


# ---- 工厂与配置 -----------------------------------------------------------


def test_mysql_config_factory_defaults():
    cfg = DatabaseConfig.mysql(database="app")
    assert cfg.database_type == DatabaseType.MYSQL
    assert cfg.host == "localhost"
    assert cfg.port == 3306
    assert cfg.username == "root"
    assert cfg.database == "app"


def test_mysql_config_factory_extras_pass_through():
    cfg = DatabaseConfig.mysql(host="db", port=3307, username="u", password="p",
                               database="d", connect_timeout=5)
    assert cfg.extra == {"connect_timeout": 5}


# ---- 适配器表面 -----------------------------------------------------------


def test_placeholder_and_quote_identifier():
    adapter = MySQLAdapter(DatabaseConfig.mysql(database="t"))
    assert adapter.get_placeholder() == "%s"
    assert adapter.quote_identifier("users") == "`users`"


# ---- connect / execute / fetch (mock aiomysql) ----------------------------


@pytest.fixture
def patched_aiomysql(monkeypatch):
    """Patch aiomysql in the adapter module with a recorder."""
    from lib.tests.conftest import FakeMySQLStore
    import lib.db.adapters.mysql as mysql_mod

    store = FakeMySQLStore()

    class _FakeMod:
        # cursor classes are passed by identity — DictCursor is just a sentinel
        DictCursor = object()

        @staticmethod
        async def connect(**kwargs):
            store.connect_kwargs = kwargs
            return store

    monkeypatch.setattr(mysql_mod, "aiomysql", _FakeMod)
    return store


async def test_connect_passes_charset_and_autocommit(patched_aiomysql):
    adapter = MySQLAdapter(DatabaseConfig.mysql(database="x"))
    await adapter.connect()
    kw = patched_aiomysql.connect_kwargs
    assert kw["charset"] == "utf8mb4"
    assert kw["autocommit"] is True
    assert kw["db"] == "x"
    assert adapter.is_connected


async def test_connect_raises_when_driver_missing(monkeypatch):
    import lib.db.adapters.mysql as mysql_mod
    monkeypatch.setattr(mysql_mod, "aiomysql", None)
    adapter = MySQLAdapter(DatabaseConfig.mysql(database="x"))
    with pytest.raises(ImportError):
        await adapter.connect()


async def test_disconnect_closes_connection(patched_aiomysql):
    adapter = MySQLAdapter(DatabaseConfig.mysql(database="x"))
    await adapter.connect()
    await adapter.disconnect()
    assert patched_aiomysql.closed is True
    assert adapter._connection is None


async def test_execute_sends_sql_and_params(patched_aiomysql):
    adapter = MySQLAdapter(DatabaseConfig.mysql(database="x"))
    await adapter.connect()
    await adapter.execute("INSERT INTO t VALUES (%s)", ("v",))
    assert patched_aiomysql.executed[-1] == ("INSERT INTO t VALUES (%s)", ("v",))


async def test_fetch_one_returns_dict(patched_aiomysql):
    adapter = MySQLAdapter(DatabaseConfig.mysql(database="x"))
    await adapter.connect()
    patched_aiomysql.queue_rows([{"id": 1, "name": "a"}])
    row = await adapter.fetch_one("SELECT id, name FROM t WHERE id = %s", (1,))
    assert row == {"id": 1, "name": "a"}


async def test_fetch_one_returns_none_when_empty(patched_aiomysql):
    adapter = MySQLAdapter(DatabaseConfig.mysql(database="x"))
    await adapter.connect()
    row = await adapter.fetch_one("SELECT 1")
    assert row is None


async def test_fetch_all_returns_list_of_dicts(patched_aiomysql):
    adapter = MySQLAdapter(DatabaseConfig.mysql(database="x"))
    await adapter.connect()
    patched_aiomysql.queue_rows([{"id": 1}, {"id": 2}])
    rows = await adapter.fetch_all("SELECT id FROM t")
    assert rows == [{"id": 1}, {"id": 2}]


async def test_execute_without_connection_raises():
    adapter = MySQLAdapter(DatabaseConfig.mysql(database="x"))
    with pytest.raises(RuntimeError):
        await adapter.execute("SELECT 1")


# ---- introspection: SQL 形态校验 ------------------------------------------


async def test_table_exists_uses_information_schema(patched_aiomysql):
    adapter = MySQLAdapter(DatabaseConfig.mysql(database="app"))
    await adapter.connect()
    patched_aiomysql.queue_rows([{"count": 1}])
    assert await adapter.table_exists("users") is True
    last_sql, last_params = patched_aiomysql.executed[-1]
    assert "information_schema.tables" in last_sql
    assert last_params == ("app", "users")


async def test_table_exists_false_when_zero(patched_aiomysql):
    adapter = MySQLAdapter(DatabaseConfig.mysql(database="app"))
    await adapter.connect()
    patched_aiomysql.queue_rows([{"count": 0}])
    assert await adapter.table_exists("users") is False


async def test_get_table_columns_maps_extra_to_auto_increment(patched_aiomysql):
    adapter = MySQLAdapter(DatabaseConfig.mysql(database="app"))
    await adapter.connect()
    patched_aiomysql.queue_rows([
        {
            "column_name": "id", "data_type": "int", "is_nullable": "NO",
            "column_default": None, "column_key": "PRI", "extra": "auto_increment",
            "character_maximum_length": None, "numeric_precision": 10, "numeric_scale": 0,
        },
        {
            "column_name": "name", "data_type": "varchar", "is_nullable": "YES",
            "column_default": None, "column_key": "", "extra": "",
            "character_maximum_length": 100, "numeric_precision": None, "numeric_scale": None,
        },
    ])
    cols = await adapter.get_table_columns("users")
    assert cols[0]["name"] == "id"
    assert cols[0]["primary_key"] is True
    assert cols[0]["auto_increment"] is True
    assert cols[1]["nullable"] is True
    assert cols[1]["length"] == 100


async def test_get_table_indexes_groups_by_index_name(patched_aiomysql):
    adapter = MySQLAdapter(DatabaseConfig.mysql(database="app"))
    await adapter.connect()
    patched_aiomysql.queue_rows([
        {"index_name": "PRIMARY", "column_name": "id", "non_unique": 0},
        {"index_name": "idx_name_email", "column_name": "name", "non_unique": 1},
        {"index_name": "idx_name_email", "column_name": "email", "non_unique": 1},
    ])
    indexes = await adapter.get_table_indexes("users")
    by_name = {idx["name"]: idx for idx in indexes}
    assert by_name["PRIMARY"]["unique"] is True
    assert by_name["idx_name_email"]["columns"] == ["name", "email"]
    assert by_name["idx_name_email"]["unique"] is False


# ---- 嵌套事务 (BaseAdapter 行为) ------------------------------------------


async def test_transaction_nesting_depth_one(patched_aiomysql):
    adapter = MySQLAdapter(DatabaseConfig.mysql(database="app"))
    await adapter.connect()

    await adapter.begin()
    await adapter.commit()

    issued = [sql for sql, _ in patched_aiomysql.executed]
    assert issued.count("BEGIN") == 1
    assert issued.count("COMMIT") == 1


async def test_transaction_nesting_depth_three_commits_once(patched_aiomysql):
    adapter = MySQLAdapter(DatabaseConfig.mysql(database="app"))
    await adapter.connect()

    await adapter.begin()
    await adapter.begin()
    await adapter.begin()
    await adapter.commit()
    await adapter.commit()
    await adapter.commit()

    issued = [sql for sql, _ in patched_aiomysql.executed]
    assert issued.count("BEGIN") == 1
    assert issued.count("COMMIT") == 1


async def test_transaction_rollback_at_depth_two_aborts_outer(patched_aiomysql):
    adapter = MySQLAdapter(DatabaseConfig.mysql(database="app"))
    await adapter.connect()

    await adapter.begin()
    await adapter.begin()
    await adapter.rollback()
    # Subsequent commits should be no-ops because rollback resets depth.
    await adapter.commit()

    issued = [sql for sql, _ in patched_aiomysql.executed]
    assert issued.count("BEGIN") == 1
    assert issued.count("ROLLBACK") == 1
    assert "COMMIT" not in issued


# ---- parameterized queries: 注入安全 smoke -------------------------------


async def test_parameterized_query_keeps_payload_in_params(patched_aiomysql):
    """Adapter 必须用驱动级参数化, 不会把 payload 拼进 SQL。"""
    adapter = MySQLAdapter(DatabaseConfig.mysql(database="app"))
    await adapter.connect()

    payload = "'; DROP TABLE users;--"
    await adapter.execute("SELECT * FROM users WHERE name = %s", (payload,))
    last_sql, last_params = patched_aiomysql.executed[-1]
    assert payload not in last_sql
    assert last_params == (payload,)
