# Database Guidelines

> Persistence conventions for ccplugin plugins. The shared async ORM lives in `lib/db/`.

---

## Scope

How plugins talk to databases. Covers configuration, connection lifecycle, model declaration, queries, and transactions. Applies to every plugin that persists data (today: `plugins/memory/`).

---

## Stack

- **ORM**: in-house `lib.db` — async, thin, single-instance `DatabaseConnection`.
- **Default backend**: SQLite (file-based, async via `aiosqlite`). Plugins MUST default to SQLite unless a hard requirement dictates otherwise.
- **Other supported backends**: MySQL (`aiomysql`), PostgreSQL (`asyncpg`). Opt in via plugin's `[project.optional-dependencies]`.
- **Async runtime**: `asyncio`. All adapter methods are async; the connection singleton is initialized once per process.

---

## Public Surface

Always import from `lib.db` (re-exported from `lib/db/__init__.py:7-49`):

```python
from lib.db import (
    DatabaseConfig, DatabaseConnection, DatabaseType,
    Model, Field, FieldType,
    Integer, BigInteger, Float, Double, Decimal,
    String, Text, Boolean, Date, DateTime, Timestamp, Blob, JSON,
    SchemaManager,
)
```

Never reach into `lib.db.adapters.*` directly; create adapters via `DatabaseConfig.sqlite(...)` / `.mysql(...)` / `.postgresql(...)` and let `DatabaseConnection.initialize` pick the right adapter.

---

## Configuration

Use the classmethod constructors on `DatabaseConfig` (`lib/db/core.py:40-82`):

```python
# SQLite (default; plugin-local file under the project plugin dir)
config = DatabaseConfig.sqlite(path="memory.db")

# MySQL
config = DatabaseConfig.mysql(host="...", username="...", password="...", database="...")

# PostgreSQL
config = DatabaseConfig.postgresql(host="...", username="...", password="...", database="...")
```

Plugin-local DB files MUST live under the project plugin dir resolved via `lib.utils.env.get_project_plugins_dir()`. Never write DB files into the plugin source directory.

---

## Lifecycle

`DatabaseConnection` is a process-wide singleton (`lib/db/core.py:135-145`). The standard lifecycle is:

1. `await DatabaseConnection.initialize(config)` — connect (idempotent within one process).
2. Use the connection (`execute`, `fetch_one`, `fetch_all`, `begin`/`commit`/`rollback`).
3. `await DatabaseConnection.close()` — disconnect before process exit.

Hooks ran from short-lived processes (e.g. the memory plugin's hooks) MUST close the connection before returning, otherwise the background loop blocks shutdown:

```python
# plugins/memory/scripts/hooks.py:36-47
async def _handle():
    await init_db()
    try:
        core_memories = await get_memories_by_priority(max_priority=3)
        ...
    finally:
        await close_db()    # critical for hook process to exit cleanly
```

---

## Model Declaration

Use `Model` + typed `Field` subclasses from `lib.db`. Field types are defined in `lib/db/models.py:54-67`:

```
INTEGER, BIGINT, FLOAT, DOUBLE, DECIMAL,
VARCHAR, TEXT, BOOLEAN,
DATE, DATETIME, TIMESTAMP,
BLOB, JSON
```

`Field` (dataclass at `lib/db/models.py:70-99`) supports `primary_key`, `auto_increment`, `nullable`, `default`, `unique`, `index`, `length`, `precision`, `scale`. Per-backend SQL type rendering is delegated to `Field.get_sql_type(db_type)` — it adapts BOOLEAN to TINYINT(1) on MySQL and JSON to TEXT on SQLite, so application code does not need to special-case backends.

---

## Query Patterns

- **Always use parameterized SQL.** Pass tuples, never f-string interpolation.
- **Identifier validation is built-in.** `lib/db/models.py:16-51` validates `ORDER BY`, `GROUP BY`, and aggregate `SELECT` strings via regexes. Anything containing `;`, comments (`--`), or `DROP/DELETE/INSERT/UPDATE/ALTER/CREATE` keywords is rejected — do not try to bypass these checks.
- **Use the placeholder helper** when writing raw SQL across backends:
  ```python
  ph = DatabaseConnection.get_adapter().get_placeholder()  # '?' for sqlite, '%s' for mysql
  await DatabaseConnection.execute(f"SELECT * FROM t WHERE id = {ph}", (uri,))
  ```
- **Quote identifiers** with `adapter.quote_identifier(name)` when names are user-derived.

---

## Transactions

```python
await DatabaseConnection.begin()
try:
    await DatabaseConnection.execute(sql_a, params_a)
    await DatabaseConnection.execute(sql_b, params_b)
    await DatabaseConnection.commit()
except Exception:
    await DatabaseConnection.rollback()
    raise
```

Never leave a `begin()` without a paired `commit()` or `rollback()` on every code path.

---

## Migrations

- Schema is created with `SchemaManager` (`lib/db/schema.py`). On first run, plugins call `await SchemaManager.create_all()` to create tables defined by registered `Model` subclasses.
- There is no formal migration framework. For destructive changes:
  - bump the plugin minor version
  - document the manual migration step in the plugin's CHANGELOG
  - prefer additive changes (new nullable columns, new tables) over breaking ones
- Test migrations on SQLite first; run the plugin's pytest suite before tagging.

---

## Naming

- Table names: snake_case singular (`memory`, not `memories`); pluralize only when collision-prone.
- Column names: snake_case. Booleans named `is_*` or `has_*`. Timestamps `*_at`.
- Indexes: `Field(index=True)` for single-column; declare composite indexes via `SchemaManager`.

---

## Forbidden Patterns

```python
# ❌ String interpolation into SQL
await DatabaseConnection.execute(f"SELECT * FROM t WHERE id = '{user_id}'")

# ❌ Multiple connection singletons / second initialize
await DatabaseConnection.initialize(cfg_a)
await DatabaseConnection.initialize(cfg_b)   # silent no-op; cfg_a still in effect

# ❌ Synchronous DB drivers (sqlite3, pymysql)
import sqlite3                                 # blocks the event loop

# ❌ Leaving the connection open in short-lived hook processes
await init_db()
do_work()
# missing `await close_db()` — the hook hangs at exit
```

---

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Calling `DatabaseConnection.get_adapter()` before `initialize()` | Initialize once at plugin entry; the helper raises `RuntimeError("数据库未初始化")` |
| Writing raw `ORDER BY` from user input | Pass through the validator or whitelist allowed columns |
| Using `JSON` field on SQLite and assuming JSON queries | SQLite stores JSON as TEXT — read/write whole blobs in Python |
| Sharing one event loop across threads | Each thread needs its own loop or the connection must be opened in the right loop (see `run_async` in `plugins/memory/scripts/hooks.py:17-30`) |
| Forgetting to install backend extra | Add `aiosqlite` / `aiomysql` / `asyncpg` to the plugin's `[project.optional-dependencies]` matching `lib`'s extras (`lib/pyproject.toml:8-13`) |

---

## References

- `lib/db/core.py:21-192` — `DatabaseType`, `DatabaseConfig`, `DatabaseAdapter`, `DatabaseConnection`
- `lib/db/models.py:16-99` — SQL validators, `FieldType`, `Field`
- `lib/db/__init__.py` — public surface
- `plugins/memory/scripts/hooks.py:33-49` — correct lifecycle inside a hook
- `lib/pyproject.toml:8-13` — optional backend extras
