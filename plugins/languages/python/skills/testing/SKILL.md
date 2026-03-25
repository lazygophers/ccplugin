---
description: Python 测试框架和策略 - pytest 8.x、hypothesis 属性测试、pytest-asyncio。测试驱动开发的核心规范。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Python 测试框架和策略

## 适用 Agents

- **python:dev** - 开发阶段使用
- **python:debug** - 测试失败调试
- **python:test** - 测试代码编写

## 相关 Skills

- **Skills(python:core)** - 基础规范
- **Skills(python:types)** - 测试类型注解
- **Skills(python:async)** - 异步测试
- **Skills(python:error)** - 测试异常处理

## 核心原则

### 1. 测试驱动开发（TDD）

- **单元测试覆盖率 ≥ 90%**
- **集成测试覆盖核心流程**
- **属性测试自动生成边界用例**
- **CI/CD 自动运行测试**

### 2. pytest 8.x 新特性

**package 级作用域 fixture**：

```python
@pytest.fixture(scope="package")  # 新增：package 级作用域
def database():
    db = connect_db()
    yield db
    db.close()
```

**改进的参数化**：

```python
@pytest.mark.parametrize(
    "input,expected",
    [
        pytest.param(1, 2, id="case-1"),
        pytest.param(2, 4, id="case-2"),
        pytest.param(3, 6, id="case-3", marks=pytest.mark.slow),
    ]
)
def test_double(input, expected):
    assert double(input) == expected
```

## hypothesis 属性测试

### 基础示例

```python
from hypothesis import given, strategies as st

@given(st.lists(st.integers()))
def test_reverse_twice_is_identity(items):
    """反转两次应该得到原列表"""
    assert list(reversed(list(reversed(items)))) == items

@given(st.integers(min_value=0, max_value=150))
def test_age_validation(age):
    """年龄验证应该接受 0-150"""
    user = User(username="test", age=age)
    assert 0 <= user.age <= 150
```

### 高级策略

```python
from hypothesis import given
from hypothesis.strategies import builds, text, emails

# 生成复杂对象
@given(builds(
    User,
    username=text(min_size=3, max_size=50),
    email=emails(),
    age=st.integers(min_value=18, max_value=120)
))
def test_user_creation(user):
    """测试用户创建逻辑"""
    assert user.username
    assert "@" in user.email
    assert 18 <= user.age <= 120
```

## Fixtures 最佳实践

### 异步 Fixture

```python
import pytest
from httpx import AsyncClient

@pytest.fixture
async def async_client():
    """异步客户端 fixture"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def test_user(async_client):
    """创建测试用户"""
    response = await async_client.post("/users", json={
        "username": "testuser",
        "email": "test@example.com"
    })
    return response.json()
```

### Fixture 作用域

```python
# 函数级（默认）
@pytest.fixture(scope="function")
def user():
    return User(name="test")

# 模块级
@pytest.fixture(scope="module")
def db_connection():
    conn = create_connection()
    yield conn
    conn.close()

# 包级（pytest 8.0+）
@pytest.fixture(scope="package")
def database():
    db = setup_database()
    yield db
    teardown_database(db)

# 会话级
@pytest.fixture(scope="session")
def test_config():
    return load_test_config()
```

## 异步测试（pytest-asyncio）

### 基础用法

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_user(async_client):
    """测试创建用户"""
    response = await async_client.post("/users", json={
        "username": "newuser",
        "email": "new@example.com"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
```

### 配置自动模式

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"  # 自动检测异步测试，无需 @pytest.mark.asyncio
```

## 测试组织

### 项目结构

```
tests/
├── conftest.py              # 全局 fixture
├── unit/                    # 单元测试
│   ├── test_models.py
│   ├── test_services.py
│   └── test_utils.py
├── integration/             # 集成测试
│   ├── test_api.py
│   └── test_database.py
└── e2e/                     # 端到端测试
    └── test_user_flows.py
```

### conftest.py 示例

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="session")
def engine():
    """创建测试数据库引擎"""
    return create_engine("sqlite:///:memory:")

@pytest.fixture(scope="function")
def db_session(engine):
    """创建数据库会话"""
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def async_client():
    """异步客户端"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
```

## 覆盖率配置

### pyproject.toml

```toml
[tool.coverage.run]
source = ["src"]
branch = true
omit = [
    "*/tests/*",
    "*/migrations/*",
    "*/__pycache__/*",
]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false

# 质量门控
fail_under = 90  # 最低 90% 覆盖率

exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
]
```

### 运行覆盖率检查

```bash
# 运行测试并生成覆盖率报告
pytest --cov=src tests/

# 生成 HTML 报告
pytest --cov=src --cov-report=html tests/
open htmlcov/index.html

# 显示未覆盖的行
pytest --cov=src --cov-report=term-missing tests/

# 覆盖率不达标时失败
pytest --cov=src --cov-fail-under=90 tests/
```

## Mock 和 Patch

### unittest.mock

```python
from unittest.mock import Mock, patch, AsyncMock

def test_email_sending():
    """测试邮件发送（Mock 外部服务）"""
    with patch('app.services.email.send_email') as mock_send:
        mock_send.return_value = True

        result = UserService.create_and_notify(username="test")

        mock_send.assert_called_once()
        assert result.username == "test"

@pytest.mark.asyncio
async def test_async_api_call():
    """测试异步 API 调用"""
    with patch('app.services.api.fetch_data', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = {"status": "ok"}

        result = await process_external_data()

        mock_fetch.assert_awaited_once()
        assert result == {"status": "ok"}
```

## Red Flags：AI 常见误区

| AI 可能的理性化解释 | 实际应该检查的内容 |
|---------------------|-------------------|
| "这个测试用例覆盖了所有情况" | ✅ 是否使用了 hypothesis 属性测试？ |
| "手动测试更准确" | ✅ 是否有自动化测试覆盖？ |
| "80% 覆盖率够用了" | ✅ 是否达到 90% 覆盖率目标？ |
| "不需要测试简单函数" | ✅ 是否所有公共函数都有测试？ |
| "集成测试可以替代单元测试" | ✅ 是否有独立的单元测试？ |
| "同步测试更简单" | ✅ 异步代码是否使用了 pytest-asyncio？ |

## 完整示例

### FastAPI 应用测试

```python
import pytest
from httpx import AsyncClient
from hypothesis import given, strategies as st

# Fixture
@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def test_user(async_client):
    response = await async_client.post("/users", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword123"
    })
    return response.json()

# 单元测试
@pytest.mark.asyncio
async def test_create_user(async_client):
    """测试创建用户"""
    response = await async_client.post("/users", json={
        "username": "newuser",
        "email": "new@example.com",
        "password": "password123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@example.com"
    assert "id" in data

# 属性测试
@given(
    username=st.text(min_size=3, max_size=50),
    age=st.integers(min_value=0, max_value=150)
)
def test_user_validation(username, age):
    """属性测试：用户验证逻辑"""
    user = User(username=username, email="test@example.com", age=age)
    assert len(user.username) >= 3
    assert 0 <= user.age <= 150

# 集成测试
@pytest.mark.asyncio
async def test_user_workflow(async_client, test_user):
    """测试完整用户工作流"""
    # 1. 登录
    response = await async_client.post("/token", data={
        "username": test_user["username"],
        "password": "securepassword123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]

    # 2. 获取当前用户信息
    response = await async_client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == test_user["username"]
```

## 检查清单

### 测试组织
- [ ] 测试文件以 `test_` 开头
- [ ] 测试函数以 `test_` 开头
- [ ] 测试分层（unit/integration/e2e）
- [ ] conftest.py 定义全局 fixture

### pytest 配置
- [ ] pytest 8.x 使用最新特性
- [ ] pytest-asyncio 配置自动模式
- [ ] pytest-cov 配置覆盖率目标
- [ ] 使用参数化测试减少重复

### 覆盖率
- [ ] 单元测试覆盖率 ≥ 90%
- [ ] 集成测试覆盖核心流程
- [ ] 使用 hypothesis 进行属性测试
- [ ] CI/CD 集成覆盖率检查

### 异步测试
- [ ] 异步测试使用 @pytest.mark.asyncio
- [ ] 异步 fixture 正确定义
- [ ] Mock 异步函数使用 AsyncMock
