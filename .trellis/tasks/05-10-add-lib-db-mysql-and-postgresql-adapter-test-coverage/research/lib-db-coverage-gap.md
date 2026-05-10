# lib/db Test Coverage Gap (extracted from deep-study session 2026-05-10)

## Existing coverage

| Module | Test file | LOC | Scope |
|--------|-----------|-----|-------|
| logging | tests/test_logging.py | ~50 | enable_debug, info, debug, error, warn happy-path |
| db (SQLite only) | tests/test_db.py | ~80 | connection, create_table, basic schema ops |

## Untested

| Module | Risk |
|--------|------|
| db/adapters/mysql.py (137 LOC) | INFORMATION_SCHEMA queries, datetime, charset, transactions |
| db/adapters/postgresql.py (153 LOC) | pg_catalog queries, serial/bigserial, timezone |
| db/adapters/base.py:47 transaction nesting | begin/commit/rollback at depth >1 untested |
| Model.find / aggregate / batch_create / first_or_create / save / update / delete | Multiple untested across all adapters |
| SchemaManager.migrate_table (auto-add column) | Untested |
| Field types: Decimal, Blob, JSON, Date, Timestamp | Untested with non-SQLite |

## Adapter contract (from base.py:47)

```python
class BaseAdapter(ABC):
    async def connect(): ...
    async def disconnect(): ...
    async def execute(sql, params): ...
    async def fetch_one(sql, params): ...
    async def fetch_all(sql, params): ...
    async def begin(): ...        # nested-aware: only outer call issues SQL
    async def commit(): ...
    async def rollback(): ...
    async def table_exists(name): ...
    async def get_table_columns(name): ...
    async def get_table_indexes(name): ...
```

Each adapter overrides; mysql.py and postgresql.py have driver-specific implementations needing dialect-aware tests.

## Driver-specific test concerns

### MySQL (aiomysql)
- DATETIME vs TIMESTAMP semantics (TIMESTAMP auto-updates, DATETIME doesn't)
- charset=utf8mb4 required for emoji/4-byte UTF-8
- AUTO_INCREMENT semantics on INSERT IGNORE / REPLACE
- INFORMATION_SCHEMA.COLUMNS query format
- Backtick-quoted identifiers
- Implicit commit on DDL (transaction can't span CREATE TABLE)

### PostgreSQL (asyncpg)
- SERIAL / BIGSERIAL → underlying SEQUENCE
- TIMESTAMP WITH TIME ZONE
- pg_catalog.pg_attribute for column intro
- Double-quoted identifiers (case-sensitive)
- DDL inside transaction OK
- $1, $2 parameter style (not %s)

## Strategy options

### A. Docker testcontainers (recommended)
- `testcontainers-python` or `pytest-docker`
- Real driver, real SQL dialect
- ENV gate: `RUN_DB_INTEGRATION=1` skips by default
- CI: dedicated job with services
- Cost: ~5-10s container startup, ~1-2s per test suite

### B. Mock at driver level
- Mock `aiomysql.connect`, `asyncpg.connect`
- Tests adapter logic but not real SQL behavior
- Misses SQL dialect bugs entirely
- Fast (<100ms total)

### C. Hybrid
- Unit tests with mocks (fast, default CI)
- Integration with containers (gated, deeper)

**Recommendation**: C. Mocked unit tests in `test_db_mysql_unit.py` and `test_db_pg_unit.py` (always run); container integration in `test_db_mysql_integration.py` and `test_db_pg_integration.py` (RUN_DB_INTEGRATION=1).

## Container fixture sketch

```python
# conftest.py
import pytest
from testcontainers.mysql import MySqlContainer
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def mysql_container():
    if not os.getenv("RUN_DB_INTEGRATION"):
        pytest.skip("integration tests gated")
    with MySqlContainer("mysql:8") as mysql:
        yield mysql.get_connection_url()

@pytest.fixture(scope="session")
def postgres_container():
    if not os.getenv("RUN_DB_INTEGRATION"):
        pytest.skip("integration tests gated")
    with PostgresContainer("postgres:16") as pg:
        yield pg.get_connection_url()
```

## Test parity checklist (apply per adapter)

- [ ] DatabaseConfig factory accepts host/port/user/pass/db
- [ ] DatabaseConnection.initialize() succeeds with valid config
- [ ] DatabaseConnection.close() releases resources
- [ ] SchemaManager.create_table for Model with all 13 field types
- [ ] SchemaManager.migrate_table adds new column to existing
- [ ] Model.create returns instance with PK populated
- [ ] Model.first(where) returns None when not found
- [ ] Model.find(where) returns list (empty when none)
- [ ] Model.update(where, **kwargs) returns affected row count
- [ ] Model.delete(where) returns affected row count
- [ ] Model.count(where) returns int
- [ ] Model.exists(where) returns bool
- [ ] Model.aggregate(select="COUNT(*)") returns rows
- [ ] Model.batch_create([...]) inserts multiple
- [ ] Transaction nesting depth 1: explicit commit
- [ ] Transaction nesting depth 2: inner commit no-op, outer commits
- [ ] Transaction rollback at any depth aborts entire outer
- [ ] Parameterized query injection-safe (insert `'; DROP TABLE x;--`)
- [ ] Datetime field round-trips with timezone preserved (PG) / naive (MySQL)
- [ ] JSON field stores/retrieves dict
- [ ] Decimal field preserves precision

## Coverage target

- mysql.py: ≥80% line coverage
- postgresql.py: ≥80% line coverage
- base.py: ≥90% (transaction nesting critical path)

## Dependencies to add (lib/pyproject.toml [dev])

```toml
[tool.uv.dev-dependencies]
testcontainers = ">=4.0"
pytest-asyncio = ">=0.23"
aiomysql = "..."  # already?
asyncpg = "..."  # already?
```
