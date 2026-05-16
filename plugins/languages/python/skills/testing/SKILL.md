---
name: python-testing
description: Python 测试规范 (pytest 8.x)。涵盖 fixture/parametrize/mark、pytest-asyncio 异步测试、hypothesis 属性测试、覆盖率 (pytest-cov)、mock 策略、TDD 流程。在编写单元/集成测试、修复测试失败、提升覆盖率、配置 conftest.py 时使用。也触发于"写测试"、"pytest"、"测试覆盖率"、"mock"、"fixture"。
---

# Python 测试规范 (2026)

pytest 8.x + pytest-asyncio + hypothesis + pytest-cov。不用 `unittest.TestCase` 风格。

## 项目结构

```text
tests/
├── conftest.py            # 全局 fixture
├── unit/
│   ├── test_models.py
│   └── test_services.py
├── integration/
│   ├── conftest.py        # 集成层 fixture (db, app)
│   └── test_api.py
└── e2e/
    └── test_workflows.py
```

`pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-ra --strict-markers --strict-config"
asyncio_mode = "auto"
markers = [
    "slow: 慢测试 (跑前需 -m slow)",
    "integration: 需要外部服务",
]

[tool.coverage.run]
source = ["src"]
branch = true

[tool.coverage.report]
fail_under = 80
show_missing = true
```

## 测试结构 (AAA)

每个测试 = Arrange / Act / Assert 三段:

```python
def test_calculate_average_normal_case():
    # Arrange
    numbers = [1.0, 2.0, 3.0, 4.0, 5.0]

    # Act
    result = calculate_average(numbers)

    # Assert
    assert result == 3.0
```

测试函数名: `test_<被测对象>_<场景>_<期望>`。一个测试只验证一件事。

## Fixture

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

@pytest.fixture
def sample_user() -> dict:
    return {"username": "alice", "email": "alice@example.com"}

@pytest.fixture(scope="session")
async def db_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(db_engine) -> AsyncSession:
    async with AsyncSession(db_engine) as session:
        yield session
        await session.rollback()
```

scope 选择: `function` (默认, 隔离最强) > `module` > `session`。共享开销大的资源用 session, 易变状态用 function。

## Parametrize

数据驱动多个用例, 避免循环:

```python
@pytest.mark.parametrize("numbers, expected", [
    ([1], 1.0),
    ([1, 2, 3], 2.0),
    ([0, 0, 0], 0.0),
], ids=["single", "triple", "zeros"])
def test_average_parametrized(numbers, expected):
    assert calculate_average(numbers) == expected
```

## 异常测试

```python
def test_empty_list_raises():
    with pytest.raises(ValueError, match="cannot be empty"):
        calculate_average([])
```

不要只断 `pytest.raises(Exception)`, 写具体异常类型 + `match` 验证消息。

## 异步测试 (pytest-asyncio)

`asyncio_mode = "auto"` 后, 异步函数自动识别为异步测试:

```python
async def test_fetch_user(async_client):
    resp = await async_client.get("/users/1")
    assert resp.status_code == 200
    assert resp.json()["id"] == 1
```

FastAPI 集成测试用 `httpx.AsyncClient` + `ASGITransport`, 不用 `TestClient` (后者是同步的):

```python
@pytest.fixture
async def async_client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
```

## Mock 策略

优先级: **真实对象 > fake 实现 > mock 部分 > mock 全部**。

```python
from unittest.mock import patch, AsyncMock

# 在边界 mock (HTTP / 时间 / 随机), 不要 mock 业务对象
def test_send_email_calls_smtp(mocker):
    mock_smtp = mocker.patch("myapp.notifier.smtplib.SMTP")
    send_email("a@b.c", "hi")
    mock_smtp.return_value.sendmail.assert_called_once()

# 异步 mock
async def test_external_api(mocker):
    mock = mocker.patch("myapp.client.httpx.AsyncClient.get", new_callable=AsyncMock)
    mock.return_value.json.return_value = {"id": 1}
    result = await fetch_user(1)
    assert result.id == 1
```

不要 mock 自己写的纯逻辑函数 (改用真实调用)。

## 属性测试 (hypothesis)

枚举测不到的边界, 让 hypothesis 自动生成:

```python
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_reverse_twice_is_identity(items):
    assert list(reversed(list(reversed(items)))) == items

@given(st.text(min_size=1))
def test_username_validation_never_crashes(name):
    # 不该抛任何未预期异常
    try:
        UserCreate(username=name, email="a@b.c", age=20)
    except ValidationError:
        pass
```

适合: 序列化往返、数学性质、不变量。不适合: 业务流程编排。

## 覆盖率

```bash
uv run pytest --cov=src --cov-branch --cov-report=term-missing
```

目标:
- 核心业务逻辑 ≥ 90%, branch 覆盖
- 整体 ≥ 80%
- 不追求 100% (会写无价值测试)
- 关注**未覆盖的分支**, 不是绝对数字

## TDD 流程

1. 写**失败的**测试 (RED) — 命名清晰描述需求
2. 写**最少代码**让它通过 (GREEN)
3. 重构, 测试保持绿 (REFACTOR)

不要先写实现再补测试 (覆盖率高但测不到真实行为)。

## 反模式

- 一个测试 assert 5+ 个不相关字段 (拆分)
- 测试相互依赖, 顺序敏感 (每个测试自包含)
- `time.sleep()` 等待 (用 `freezegun` 或事件机制)
- mock 自己的纯函数
- 测试里写循环遍历数据 (用 `parametrize`)
- `assert result == True` (写 `assert result`)
- 测试名 `test_1`, `test_works` (描述场景 + 期望)
