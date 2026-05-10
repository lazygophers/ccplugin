# lib/tests

## 运行单元测试 (默认)

```bash
uv run pytest lib/tests -m "not integration"
```

不依赖 Docker / 外部服务；MySQL 与 PostgreSQL 适配器通过 mock 驱动层覆盖。

## 运行集成测试 (需要 Docker)

```bash
RUN_DB_INTEGRATION=1 uv run pytest lib/tests -m integration
```

集成测试通过 `testcontainers` 启动真实 `mysql:8.0` 与 `postgres:16-alpine` 容器，
覆盖驱动级行为：DATETIME 语义、SERIAL/BIGSERIAL、`pg_catalog` / `INFORMATION_SCHEMA` 内省、
真实事务嵌套、JSON / Decimal 往返。

未设置 `RUN_DB_INTEGRATION=1` 时，所有 `@pytest.mark.integration` 用例 skip。

## 覆盖率

```bash
uv run pytest --cov=lib.db.adapters lib/tests -m "not integration"
```

仅单元测试时 mysql / postgresql 适配器主要覆盖 SQL 形态、占位符、内省结构化与事务嵌套；
完整 ≥80% 行覆盖目标需开启集成测试。
