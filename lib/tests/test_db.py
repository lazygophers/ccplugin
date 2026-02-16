"""
数据库 ORM 模块测试
"""

import asyncio
import os
import tempfile
from typing import Optional

import pytest
import pytest_asyncio

from lib.db import (
    DatabaseConfig,
    DatabaseConnection,
    DatabaseType,
    Model,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    SchemaManager,
)

pytestmark = pytest.mark.asyncio(loop_scope="function")


class User(Model):
    __tablename__ = "users"

    id = Integer(primary_key=True, auto_increment=True)
    username = String(length=100, nullable=False, unique=True, index=True)
    email = String(length=255, nullable=False, unique=True)
    is_active = Boolean(default=True)
    created_at = DateTime()


class Article(Model):
    __tablename__ = "articles"

    id = Integer(primary_key=True, auto_increment=True)
    title = String(length=200, nullable=False)
    content = Text()
    author_id = Integer(index=True)
    published = Boolean(default=False)


@pytest_asyncio.fixture
async def sqlite_connection():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    config = DatabaseConfig.sqlite(db_path)
    await DatabaseConnection.initialize(config)

    yield DatabaseConnection

    await DatabaseConnection.close()
    if os.path.exists(db_path):
        os.unlink(db_path)


async def test_sqlite_connection(sqlite_connection):
    adapter = sqlite_connection.get_adapter()
    assert adapter.is_connected
    assert adapter.config.database_type == DatabaseType.SQLITE


async def test_create_table(sqlite_connection):
    await User.create_table()

    adapter = sqlite_connection.get_adapter()
    exists = await adapter.table_exists("users")
    assert exists

    columns = await adapter.get_table_columns("users")
    column_names = [col["name"] for col in columns]

    assert "id" in column_names
    assert "username" in column_names
    assert "email" in column_names
    assert "is_active" in column_names
    assert "created_at" in column_names


async def test_create_and_first(sqlite_connection):
    await User.create_table()

    user = await User.create(
        username="testuser",
        email="test@example.com",
        is_active=True,
    )
    assert user.id > 0
    assert user.username == "testuser"

    found = await User.first(where="id = ?", params=(user.id,))
    assert found is not None
    assert found.username == "testuser"
    assert found.email == "test@example.com"


async def test_find(sqlite_connection):
    await User.create_table()

    await User.create(username="user1", email="user1@example.com")
    await User.create(username="user2", email="user2@example.com")
    await User.create(username="user3", email="user3@example.com")

    users = await User.find()
    assert len(users) == 3

    users = await User.find(limit=2)
    assert len(users) == 2

    users = await User.find(where="username = ?", params=("user1",))
    assert len(users) == 1
    assert users[0].username == "user1"


async def test_update(sqlite_connection):
    await User.create_table()

    user = await User.create(username="original", email="original@example.com")

    await User.update("id = ?", (user.id,), username="updated", email="updated@example.com")

    found = await User.first(where="id = ?", params=(user.id,))
    assert found.username == "updated"
    assert found.email == "updated@example.com"


async def test_delete(sqlite_connection):
    await User.create_table()

    user = await User.create(username="tobedeleted", email="delete@example.com")

    found = await User.first(where="id = ?", params=(user.id,))
    assert found is not None

    await User.delete("id = ?", (user.id,))

    found = await User.first(where="id = ?", params=(user.id,))
    assert found is None


async def test_count(sqlite_connection):
    await User.create_table()

    await User.create(username="user1", email="user1@example.com")
    await User.create(username="user2", email="user2@example.com")

    count = await User.count()
    assert count == 2

    count = await User.count("username = ?", ("user1",))
    assert count == 1


async def test_exists(sqlite_connection):
    await User.create_table()

    assert await User.exists() is False

    await User.create(username="user1", email="user1@example.com")

    assert await User.exists() is True
    assert await User.exists("username = ?", ("user1",)) is True
    assert await User.exists("username = ?", ("nonexistent",)) is False


async def test_model_save(sqlite_connection):
    await User.create_table()

    user = User(username="newuser", email="new@example.com", is_active=True)
    await user.save()
    assert user.id > 0

    user.email = "updated@example.com"
    await user.save()

    found = await User.first(where="id = ?", params=(user.id,))
    assert found.email == "updated@example.com"


async def test_batch_create(sqlite_connection):
    await User.create_table()

    items = [
        {"username": f"user{i}", "email": f"user{i}@example.com"}
        for i in range(10)
    ]

    users = await User.batch_create(items)
    assert len(users) == 10

    all_users = await User.find()
    assert len(all_users) == 10


async def test_migrate_table(sqlite_connection):
    await User.create_table()

    await User.migrate()

    adapter = sqlite_connection.get_adapter()
    exists = await adapter.table_exists("users")
    assert exists


async def test_drop_table(sqlite_connection):
    await User.create_table()

    adapter = sqlite_connection.get_adapter()
    exists = await adapter.table_exists("users")
    assert exists

    await User.drop_table()

    exists = await adapter.table_exists("users")
    assert not exists


async def test_transaction(sqlite_connection):
    await User.create_table()

    await DatabaseConnection.begin()

    try:
        await User.create(username="tx_user", email="tx@example.com")
        await DatabaseConnection.commit()
    except Exception:
        await DatabaseConnection.rollback()
        raise

    user = await User.first(where="username = ?", params=("tx_user",))
    assert user is not None


async def test_order_by_and_offset(sqlite_connection):
    await User.create_table()

    for i in range(5):
        await User.create(username=f"user{i}", email=f"user{i}@example.com")

    users = await User.find(order_by="id DESC")
    assert users[0].username == "user4"

    users = await User.find(order_by="id ASC", limit=2, offset=2)
    assert len(users) == 2
    assert users[0].username == "user2"


async def test_group_by_and_having(sqlite_connection):
    await User.create_table()

    await User.create(username="user1", email="a@example.com", is_active=True)
    await User.create(username="user2", email="b@example.com", is_active=True)
    await User.create(username="user3", email="c@example.com", is_active=False)

    results = await User.aggregate(
        select="is_active, COUNT(*) as count",
        group_by="is_active",
    )
    assert len(results) == 2

    results = await User.aggregate(
        select="is_active, COUNT(*) as count",
        group_by="is_active",
        having="COUNT(*) >= 2",
    )
    assert len(results) == 1
    assert results[0]["is_active"] == 1


async def test_join(sqlite_connection):
    await User.create_table()
    await Article.create_table()

    user1 = await User.create(username="author1", email="author1@example.com")
    user2 = await User.create(username="author2", email="author2@example.com")

    await Article.create(title="Article 1", author_id=user1.id)
    await Article.create(title="Article 2", author_id=user1.id)
    await Article.create(title="Article 3", author_id=user2.id)

    articles = await Article.find(
        joins=[
            {
                "type": "INNER",
                "table": "users",
                "on": "articles.author_id = users.id",
            }
        ],
        where="users.username = ?",
        params=("author1",),
    )
    assert len(articles) == 2


async def test_aggregate_with_join(sqlite_connection):
    await User.create_table()
    await Article.create_table()

    user1 = await User.create(username="author1", email="author1@example.com")
    user2 = await User.create(username="author2", email="author2@example.com")

    await Article.create(title="Article 1", author_id=user1.id)
    await Article.create(title="Article 2", author_id=user1.id)
    await Article.create(title="Article 3", author_id=user2.id)

    results = await Article.aggregate(
        select="users.username, COUNT(*) as article_count",
        joins=[
            {
                "type": "INNER",
                "table": "users",
                "on": "articles.author_id = users.id",
            }
        ],
        group_by="users.username",
    )
    assert len(results) == 2

    author1_result = next((r for r in results if r["username"] == "author1"), None)
    assert author1_result is not None
    assert author1_result["article_count"] == 2


async def test_first_or_create(sqlite_connection):
    await User.create_table()

    user, created = await User.first_or_create(
        defaults={"email": "new@example.com", "is_active": True},
        username="testuser",
    )
    assert created is True
    assert user.username == "testuser"
    assert user.email == "new@example.com"

    user2, created2 = await User.first_or_create(
        defaults={"email": "other@example.com"},
        username="testuser",
    )
    assert created2 is False
    assert user2.username == "testuser"
    assert user2.email == "new@example.com"


async def test_create_or_update(sqlite_connection):
    await User.create_table()

    user, created = await User.create_or_update(
        defaults={"email": "new@example.com", "is_active": True},
        username="testuser",
    )
    assert created is True
    assert user.username == "testuser"
    assert user.email == "new@example.com"

    user2, created2 = await User.create_or_update(
        defaults={"email": "updated@example.com", "is_active": False},
        username="testuser",
    )
    assert created2 is False
    assert user2.username == "testuser"
    assert user2.email == "updated@example.com"


async def test_create_if_not_exists(sqlite_connection):
    await User.create_table()

    user, created = await User.create_if_not_exists(
        username="testuser",
        email="test@example.com",
        is_active=True,
    )
    assert created is True
    assert user.username == "testuser"

    user2, created2 = await User.create_if_not_exists(
        username="testuser",
        email="test@example.com",
        is_active=True,
    )
    assert created2 is False
    assert user2.username == "testuser"
    assert user2.email == "test@example.com"


async def test_to_dict(sqlite_connection):
    await User.create_table()

    user = await User.create(username="dictuser", email="dict@example.com")

    user_dict = user.to_dict()
    assert user_dict["username"] == "dictuser"
    assert user_dict["email"] == "dict@example.com"
    assert "id" in user_dict
