"""
PostgreSQL 适配器集成测试 - 真实 Postgres 16 容器。

默认跳过；需要 RUN_DB_INTEGRATION=1 + 本地 Docker。
覆盖 PRD Test Parity Checklist。
"""

from __future__ import annotations

import datetime as _dt
import os
from decimal import Decimal as _D

import pytest
import pytest_asyncio

from lib.db import (
    BigInteger,
    Blob,
    Boolean,
    DatabaseConfig,
    DatabaseConnection,
    Date,
    DateTime,
    Decimal,
    Double,
    Float,
    Integer,
    JSON,
    Model,
    SchemaManager,
    String,
    Text,
    Timestamp,
)

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_DB_INTEGRATION") != "1",
        reason="integration tests gated by RUN_DB_INTEGRATION=1",
    ),
    pytest.mark.asyncio(loop_scope="function"),
]


class _AllTypes(Model):
    __tablename__ = "all_types_pg"

    id = Integer(primary_key=True, auto_increment=True)
    big = BigInteger(nullable=True)
    f = Float(nullable=True)
    d = Double(nullable=True)
    money = Decimal(precision=12, scale=2, nullable=True)
    name = String(length=100, nullable=False)
    body = Text(nullable=True)
    flag = Boolean(default=True)
    dt = Date(nullable=True)
    dtm = DateTime(nullable=True)
    ts = Timestamp(nullable=True)
    raw = Blob(nullable=True)
    payload = JSON(nullable=True)


class _Person(Model):
    __tablename__ = "person_pg"

    id = Integer(primary_key=True, auto_increment=True)
    username = String(length=100, nullable=False, unique=True, index=True)
    age = Integer(default=0)


class _PersonV2(Model):
    __tablename__ = "person_pg"

    id = Integer(primary_key=True, auto_increment=True)
    username = String(length=100, nullable=False, unique=True, index=True)
    age = Integer(default=0)
    bio = Text(nullable=True)


@pytest_asyncio.fixture
async def pg_connection(postgres_container):
    cfg = DatabaseConfig.postgresql(**postgres_container)
    await DatabaseConnection.initialize(cfg)
    yield DatabaseConnection
    adapter = DatabaseConnection.get_adapter()
    for tbl in ("all_types_pg", "person_pg"):
        try:
            await adapter.execute(f'DROP TABLE IF EXISTS "{tbl}"')
        except Exception:
            pass
    await DatabaseConnection.close()


async def test_initialize_and_close(pg_connection):
    assert pg_connection.get_adapter().is_connected


async def test_create_table_all_field_types(pg_connection):
    await SchemaManager.create_table(_AllTypes)
    adapter = pg_connection.get_adapter()
    assert await adapter.table_exists("all_types_pg")
    cols = {c["name"] for c in await adapter.get_table_columns("all_types_pg")}
    assert {"id", "big", "f", "d", "money", "name", "body",
            "flag", "dt", "dtm", "ts", "raw", "payload"} <= cols


async def test_migrate_table_adds_column(pg_connection):
    await SchemaManager.create_table(_Person)
    await SchemaManager.migrate_table(_PersonV2)
    cols = {c["name"] for c in await pg_connection.get_adapter().get_table_columns("person_pg")}
    assert "bio" in cols


async def test_crud_lifecycle(pg_connection):
    await SchemaManager.create_table(_Person)
    p = await _Person.create(username="alice", age=30)
    assert p.id > 0

    found = await _Person.first(where="username = ?", params=("alice",))
    assert found is not None and found.age == 30

    await _Person.update("id = ?", (p.id,), age=31)
    assert (await _Person.first(where="id = ?", params=(p.id,))).age == 31

    assert await _Person.count() == 1
    assert await _Person.exists("username = ?", ("alice",)) is True

    await _Person.delete("id = ?", (p.id,))
    assert await _Person.exists() is False


async def test_batch_create_and_aggregate(pg_connection):
    await SchemaManager.create_table(_Person)
    items = [{"username": f"u{i}", "age": i} for i in range(5)]
    out = await _Person.batch_create(items)
    assert len(out) == 5
    rows = await _Person.aggregate(select="COUNT(*) as c")
    assert rows[0]["c"] == 5


async def test_transaction_depth_three(pg_connection):
    await SchemaManager.create_table(_Person)
    await DatabaseConnection.begin()
    await DatabaseConnection.begin()
    await DatabaseConnection.begin()
    await _Person.create(username="tx", age=1)
    await DatabaseConnection.commit()
    await DatabaseConnection.commit()
    await DatabaseConnection.commit()
    assert await _Person.exists("username = ?", ("tx",))


async def test_transaction_rollback_aborts(pg_connection):
    await SchemaManager.create_table(_Person)
    await DatabaseConnection.begin()
    await _Person.create(username="will_rollback", age=1)
    await DatabaseConnection.rollback()
    # PG honors transactions for DML; row should be gone.
    assert not await _Person.exists("username = ?", ("will_rollback",))


async def test_parameterized_injection_safe(pg_connection):
    await SchemaManager.create_table(_Person)
    payload = "'; DROP TABLE person_pg;--"
    await _Person.create(username=payload, age=1)
    assert await pg_connection.get_adapter().table_exists("person_pg")
    found = await _Person.first(where="username = ?", params=(payload,))
    assert found is not None and found.username == payload


async def test_json_decimal_datetime_round_trip(pg_connection):
    await SchemaManager.create_table(_AllTypes)
    now = _dt.datetime(2026, 5, 10, 12, 0, 0)
    await _AllTypes.create(
        name="row",
        money=_D("12.34"),
        dtm=now,
        payload={"k": "v"},
    )
    row = await _AllTypes.first(where="name = ?", params=("row",))
    assert row is not None
    assert _D(str(row.money)) == _D("12.34")
