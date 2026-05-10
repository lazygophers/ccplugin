# PRD: Add lib db MySQL and PostgreSQL adapter test coverage

## Problem

`lib/db/adapters/{mysql.py:137, postgresql.py:153}` have zero test coverage. Only `lib/tests/test_db.py` exists, exercising SQLite adapter alone (~80 LOC). Production usage on MySQL/PG is untested: connection lifecycle, schema introspection (`INFORMATION_SCHEMA` for MySQL, `pg_catalog` for PG), datetime handling, transaction nesting, parameterized queries, serial/bigserial PK semantics.

## Goal

Add adapter test suites with parity to SQLite coverage: connection init/close, table create/migrate, all field types, CRUD, aggregate, transactions.

## Scope

### In-scope

- `lib/tests/test_db_mysql.py` — new
- `lib/tests/test_db_postgresql.py` — new
- `lib/tests/conftest.py` — shared fixtures (or extend existing)
- Each suite covers:
  - `DatabaseConfig.{mysql,postgresql}()` factory
  - `DatabaseConnection.initialize()` + `close()`
  - `SchemaManager.create_table()` for Model with all 13 field types
  - `SchemaManager.migrate_table()` (add new column to existing table)
  - `Model.create / find / first / update / delete / count / exists / aggregate / batch_create`
  - `BaseAdapter` transaction nesting (begin/commit/rollback at depth 1, 2, 3)
  - `get_table_columns / get_table_indexes` introspection
  - Parameterized query injection-safety smoke test

### Out-of-scope

- Performance benchmarks
- Replication / connection-pool stress
- Real cloud DB (use containers or in-process where possible)

## Approach

### Strategy decision

**Option A**: Docker testcontainers (`pytest-docker`, `testcontainers-python`) — real MySQL/PG instances. Heavyweight CI but real coverage.

**Option B**: Mock at adapter boundary (`aiomysql`, `asyncpg` mocks). Fast, but tests adapter logic not driver behavior.

**Option C**: SQLite-compatible mode for both (rewrite adapters to detect dialect). Not feasible for INFORMATION_SCHEMA queries.

**Recommendation**: Option A with `pytest.mark.integration` and ENV gate (`RUN_DB_INTEGRATION=1`). CI uses Docker; local dev opts-in.

### Implementation order

1. Add `pytest-docker` to `lib/pyproject.toml` dev deps
2. Define container fixtures (mysql:8, postgres:16) with healthcheck wait
3. Port `test_db.py` test cases with adapter parameter
4. Add adapter-specific tests (datetime quirks, serial PK, JSON column, charset)
5. Tag with `@pytest.mark.integration`; document opt-in run

## Acceptance Criteria

- `RUN_DB_INTEGRATION=1 uv run pytest lib/tests` passes for both adapters
- Coverage report shows mysql.py + postgresql.py reach ≥80% line coverage
- Each adapter has parity test for: schema, CRUD, aggregate, transaction nesting
- CI workflow includes integration job (separate from default unit job)
- Tests run cleanly without leaking containers (fixture teardown)

## Risk

- Docker dependency in dev environment; document setup in README
- Slow test runs may discourage execution; mitigation: separate marker
- Driver version drift: pin `aiomysql`, `asyncpg` versions

## References

- Deep-study report: `research/lib-db-coverage-gap.md` (this task)
- `lib/db/adapters/mysql.py`, `postgresql.py`
- `lib/tests/test_db.py` — SQLite reference suite
- `lib/db/adapters/base.py:47` — transaction nesting contract
