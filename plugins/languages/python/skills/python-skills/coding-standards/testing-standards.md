# Python 测试规范

## 核心原则

### ✅ 必须遵守

1. **测试覆盖要求** - 核心业务逻辑覆盖率 > 95%
2. **使用 pytest** - 统一使用 pytest 作为测试框架
3. **测试隔离** - 测试之间相互独立，不依赖执行顺序
4. **AAA 模式** - Arrange（准备）、Act（执行）、Assert（断言）
5. **测试可读性** - 测试代码清晰易懂，测试意图明确

### ❌ 禁止行为

- 测试依赖执行顺序
- 测试之间共享可变状态
- 硬编码环境依赖（如数据库连接）
- 忽略测试失败
- 在测试中使用 `sleep()` 等待（使用同步原语）
- 测试代码过于复杂

## pytest 使用规范

### 基本测试结构

```python
# ✅ 正确 - 使用 pytest 和 AAA 模式
def test_create_user_success(db_session):
    """
    测试成功创建用户。

    Given: 有效用户数据
    When: 调用创建用户接口
    Then: 返回创建的用户对象
    """
    # Arrange（准备）
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "secure123",
    }

    # Act（执行）
    user = create_user(db_session, user_data)

    # Assert（断言）
    assert user.id is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.password_hash != "secure123"  # 密码已加密


# ❌ 错误 - 缺少准备和断言
def test_create_user_bad(db_session):
    user = create_user(db_session, {...})
```

### 参数化测试

```python
# ✅ 正确 - 使用 pytest.mark.parametrize
import pytest


@pytest.mark.parametrize("email,valid", [
    ("test@example.com", True),
    ("user@domain.co.uk", True),
    ("invalid", False),
    ("", False),
    ("@example.com", False),
    ("test@", False),
])
def test_validate_email(email: str, valid: bool):
    """测试邮箱验证。"""
    assert is_valid_email(email) == valid


# ✅ 正确 - 使用参数化 ID
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("WORLD", "WORLD"),
    ("PyThOn", "PYTHON"),
], ids=["lowercase", "uppercase", "mixedcase"])
def test_to_upper(input: str, expected: str):
    """测试转大写。"""
    assert to_upper(input) == expected
```

### 异常测试

```python
# ✅ 正确 - 使用 pytest.raises
def test_create_user_duplicate_email(db_session):
    """测试创建用户时邮箱重复应抛出异常。"""
    # Arrange
    user_data = {
        "username": "user1",
        "email": "duplicate@example.com",
        "password": "pass123",
    }
    create_user(db_session, user_data)

    duplicate_data = {
        "username": "user2",
        "email": "duplicate@example.com",  # 重复邮箱
        "password": "pass456",
    }

    # Act & Assert
    with pytest.raises(DuplicateEmailError) as exc_info:
        create_user(db_session, duplicate_data)

    assert "邮箱已存在" in str(exc_info.value)


# ✅ 正确 - 检查异常属性
def test_insufficient_funds():
    """测试余额不足时的转账。"""
    account = Account(balance=100)

    with pytest.raises(InsufficientFundsError) as exc_info:
        account.withdraw(200)

    assert exc_info.value.required == 200
    assert exc_info.value.available == 100
```

## 测试命名约定

### 文件命名

```python
# ✅ 正确 - 测试文件命名
tests/
├── unit/
│   ├── test_models.py        # 测试 models.py
│   ├── test_services.py      # 测试 services.py
│   └── test_utils.py         # 测试 utils.py
└── integration/
    ├── test_database.py
    └── test_api.py

# ❌ 错误 - 不规范的命名
tests/
├── models_tests.py           # 应该是 test_models.py
├── test.py                   # 太通用
└── Tests.py                  # 不应该大写
```

### 函数命名

```python
# ✅ 正确 - 清晰的测试命名
def test_user_login_success():
    """测试用户登录成功场景。"""
    pass

def test_user_login_invalid_password():
    """测试用户登录时密码无效场景。"""
    pass

def test_user_login_user_not_found():
    """测试用户登录时用户不存在场景。"""
    pass


# ❌ 错误 - 不清晰的命名
def test_login1():
    pass

def test_login_fail():
    pass  # 不够具体
```

### 类命名

```python
# ✅ 正确 - 测试类命名
class TestUserService:
    """用户服务测试类。"""

    def test_create_user(self):
        pass

    def test_delete_user(self):
        pass


class TestOrderService:
    """订单服务测试类。"""

    def test_create_order(self):
        pass
```

## Fixture 使用

### 基本 Fixture

```python
# ✅ 正确 - 在 conftest.py 中定义共享 fixtures
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from my_app.database import Base
from my_app.models import User


@pytest.fixture(scope="function")
def db_session():
    """创建内存数据库会话，每个测试函数独立。"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    session = Session(engine)
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture(scope="function")
def test_user(db_session: Session):
    """创建测试用户。"""
    user = User(
        username="testuser",
        email="test@example.com",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ✅ 正确 - 使用 fixture
def test_get_user_by_id(db_session: Session, test_user: User):
    """测试根据 ID 获取用户。"""
    found_user = get_user_by_id(db_session, test_user.id)
    assert found_user.username == "testuser"
```

### Fixture 作用域

```python
# ✅ 正确 - 合理使用 fixture 作用域
@pytest.fixture(scope="session")
def global_config():
    """会话级配置，整个测试会话只创建一次。"""
    return load_config("test-config.yaml")


@pytest.fixture(scope="module")
def database():
    """模块级数据库，每个测试模块创建一次。"""
    engine = create_test_database()
    yield engine
    cleanup_test_database(engine)


@pytest.fixture(scope="function")
def db_session(database):
    """函数级会话，每个测试函数创建新会话。"""
    session = Session(database)
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(autouse=True)
def reset_state():
    """自动使用的 fixture，每个测试前重置状态。"""
    reset_global_state()
    yield
    cleanup_global_state()
```

### Fixture 参数化

```python
# ✅ 正确 - 参数化 fixture
@pytest.fixture(params=[
    {"username": "user1", "email": "user1@example.com"},
    {"username": "user2", "email": "user2@example.com"},
])
def user_data(request):
    """提供不同的用户数据。"""
    return request.param


def test_create_user_with_different_data(db_session, user_data):
    """测试使用不同数据创建用户。"""
    user = create_user(db_session, user_data)
    assert user.username == user_data["username"]
```

## 覆盖率要求

### 配置覆盖率

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = [
    "--cov=my_package",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-fail-under=95",  # 覆盖率低于 95% 则失败
]
```

### 运行覆盖率测试

```bash
# ✅ 运行测试并生成覆盖率报告
uv run pytest --cov=my_package --cov-report=html

# ✅ 查看特定模块的覆盖率
uv run pytest --cov=my_package.services --cov-report=term-missing

# ✅ 设置覆盖率阈值
uv run pytest --cov=my_package --cov-fail-under=95
```

### 覆盖率排除

```python
# ✅ 正确 - 排除不需要测试的代码
# pyproject.toml
[tool.coverage.run]
omit = [
    "*/tests/*",
    "*/migrations/*",
    "*/__init__.py",
    "*/conftest.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]


# ✅ 正确 - 使用注释标记不需要覆盖的代码
def internal_debug_function():
    """内部调试函数，不需要测试。"""
    # pragma: no cover
    print_debug_info()
```

## 单元测试 vs 集成测试

### 单元测试

```python
# ✅ 正确 - 单元测试隔离依赖，使用 mock
import pytest
from unittest.mock import Mock, patch


def test_send_email_success():
    """测试发送邮件成功（单元测试，不实际发送）。"""
    # Arrange
    mock_smtp = Mock()
    email_service = EmailService(smtp_client=mock_smtp)

    # Act
    email_service.send("user@example.com", "Subject", "Body")

    # Assert
    mock_smtp.send_message.assert_called_once()
    call_args = mock_smtp.send_message.call_args
    assert "user@example.com" in str(call_args)


def test_calculate_price_with_discount():
    """测试价格计算（纯函数，无依赖）。"""
    # Arrange
    price = 100.0
    discount_rate = 0.2  # 8 折

    # Act
    final_price = calculate_price(price, discount_rate)

    # Assert
    assert final_price == 80.0
```

### 集成测试

```python
# ✅ 正确 - 集成测试使用真实依赖
@pytest.mark.integration
def test_user_workflow(db_session):
    """测试用户注册到登录的完整流程。"""
    # 注册
    user = register_user(
        db_session,
        username="newuser",
        email="new@example.com",
        password="password123",
    )
    assert user.id is not None

    # 登录
    logged_in = authenticate_user(db_session, "new@example.com", "password123")
    assert logged_in is True

    # 错误密码
    logged_in = authenticate_user(db_session, "new@example.com", "wrongpassword")
    assert logged_in is False
```

### 标记测试类型

```python
# ✅ 正确 - 使用 pytest.mark 标记测试类型
@pytest.mark.unit
def test_pure_function():
    """单元测试。"""
    assert add(1, 2) == 3


@pytest.mark.integration
def test_database_query(db_session):
    """集成测试。"""
    user = create_user(db_session, {...})
    assert user.id is not None


@pytest.mark.slow
def test_long_running_operation():
    """慢速测试。"""
    time.sleep(10)


# 运行特定类型的测试
# pytest -m unit          # 只运行单元测试
# pytest -m integration   # 只运行集成测试
# pytest -m "not slow"    # 跳过慢速测试
```

## 测试分层

### 测试金字塔

```
        /\
       /  \        E2E 测试 (10%)
      /    \
     /------\      集成测试 (30%)
    /        \
   /----------\    单元测试 (60%)
  /            \
```

### 测试分层示例

```python
# 第一层：单元测试 - 快速、隔离
# tests/unit/test_services.py
def test_user_service_calculate_age():
    """测试年龄计算逻辑。"""
    user = User(birth_date=date(1990, 1, 1))
    age = user_service.calculate_age(user, reference_date=date(2024, 1, 1))
    assert age == 34


# 第二层：集成测试 - 中速、真实依赖
# tests/integration/test_database.py
def test_user_crud_operations(db_session):
    """测试用户数据库操作。"""
    # Create
    user = User(username="test", email="test@example.com")
    db_session.add(user)
    db_session.commit()

    # Read
    found = db_session.query(User).filter_by(username="test").first()
    assert found is not None

    # Update
    found.email = "updated@example.com"
    db_session.commit()

    # Delete
    db_session.delete(found)
    db_session.commit()
    assert db_session.query(User).filter_by(username="test").first() is None


# 第三层：E2E 测试 - 慢速、完整流程
# tests/e2e/test_user_flow.py
@pytest.mark.e2e
def test_complete_user_registration_flow(test_client):
    """测试完整的用户注册流程。"""
    # 注册请求
    response = test_client.post("/api/register", json={
        "username": "newuser",
        "email": "new@example.com",
        "password": "secure123",
    })
    assert response.status_code == 201

    # 验证邮件发送（使用 test account）
    # 点击验证链接

    # 登录
    response = test_client.post("/api/login", json={
        "email": "new@example.com",
        "password": "secure123",
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
```

## 异步测试

### 使用 pytest-asyncio

```python
# ✅ 正确 - 异步测试
import pytest


@pytest.mark.asyncio
async def test_async_create_user():
    """测试异步创建用户。"""
    user = await async_create_user(
        username="asyncuser",
        email="async@example.com",
    )
    assert user.id is not None


@pytest.mark.asyncio
async def test_async_fetch_multiple():
    """测试并发获取多个用户。"""
    user_ids = [1, 2, 3, 4, 5]

    # 并发获取
    users = await asyncio.gather(*[
        fetch_user(user_id) for user_id in user_ids
    ])

    assert len(users) == 5
    assert all(u is not None for u in users)


# ✅ 正确 - 使用异步 fixture
@pytest.fixture
async def async_db_session():
    """创建异步数据库会话。"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_async_user_crud(async_db_session: AsyncSession):
    """测试异步 CRUD 操作。"""
    user = User(username="test", email="test@example.com")
    async_db_session.add(user)
    await async_db_session.commit()

    result = await async_db_session.execute(
        select(User).filter_by(username="test")
    )
    found_user = result.scalar_one()
    assert found_user.email == "test@example.com"
```

## Mock 使用

### 使用 unittest.mock

```python
# ✅ 正确 - Mock 外部依赖
from unittest.mock import Mock, patch, AsyncMock


def test_api_client_with_mock():
    """测试 API 客户端（Mock HTTP 请求）。"""
    # Arrange
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"result": "success"}

    with patch("requests.get", return_value=mock_response) as mock_get:
        client = ApiClient()
        result = client.get_data("https://api.example.com/data")

    # Assert
    assert result == {"result": "success"}
    mock_get.assert_called_once_with("https://api.example.com/data")


# ✅ 正确 - Mock 异步函数
@pytest.mark.asyncio
async def test_async_service_with_mock():
    """测试异步服务。"""
    mock_repo = AsyncMock()
    mock_repo.get_user.return_value = User(id=1, username="test")

    service = UserService(user_repo=mock_repo)
    user = await service.get_user(1)

    assert user.username == "test"
    mock_repo.get_user.assert_called_once_with(1)


# ✅ 正确 - 使用 patch 装饰器
@patch("my_app.services.external_api_call")
def test_service_with_patch(mock_api):
    """测试服务函数，Mock 外部 API 调用。"""
    mock_api.return_value = {"status": "ok"}

    result = my_service_function()

    assert result["status"] == "ok"
    mock_api.assert_called_once()
```

## 测试最佳实践

### 使用 pytest_assertions

```python
# ✅ 正确 - 使用 pytest 的详细断言
def test_user_attributes(test_user):
    """测试用户属性。"""
    assert test_user.username == "testuser"
    assert test_user.email == "test@example.com"
    assert test_user.is_active is True
    assert test_user.created_at < datetime.now()


# ✅ 正确 - 断言近似值
def test_calculation_with_tolerance():
    """测试浮点数计算。"""
    result = calculate_pi()
    assert result == pytest.approx(3.14159, rel=1e-5)


# ✅ 正确 - 断言集合内容
def test_user_list_contains(test_users):
    """测试用户列表。"""
    usernames = [u.username for u in test_users]
    assert "alice" in usernames
    assert "bob" in usernames
    assert len(usernames) == 2
```

### 测试数据构建

```python
# ✅ 正确 - 使用工厂模式构建测试数据
# tests/factories.py
import factory

class UserFactory(factory.Factory):
    """用户测试数据工厂。"""
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")
    is_active = True


# ✅ 正确 - 使用工厂
def test_with_multiple_users(db_session):
    """测试使用工厂创建多个用户。"""
    users = UserFactory.create_batch(5, is_active=False)
    assert len(users) == 5
    assert all(not u.is_active for u in users)
```

## 检查清单

提交代码前，确保：

- [ ] 测试文件以 `test_` 开头或 `_test.py` 结尾
- [ ] 测试函数以 `test_` 开头
- [ ] 使用 AAA 模式（Arrange、Act、Assert）
- [ ] 核心业务逻辑有测试覆盖
- [ ] 测试覆盖率 >= 95%
- [ ] 测试之间相互独立
- [ ] 不使用硬编码的环境依赖
- [ ] 异常测试使用 `pytest.raises`
- [ ] 集成测试标记 `@pytest.mark.integration`
- [ ] 慢速测试标记 `@pytest.mark.slow`
- [ ] 异步测试使用 `@pytest.mark.asyncio`
- [ ] 使用 fixtures 管理共享资源
