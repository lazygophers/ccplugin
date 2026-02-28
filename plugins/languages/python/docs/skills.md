# 技能系统

Python 插件提供六个核心技能，覆盖 Python 开发的主要领域。

## 技能列表

| 技能 | 描述 | 自动激活 |
|------|------|----------|
| `core` | Python 核心规范 | 始终激活 |
| `types` | 类型提示规范 | 使用类型时 |
| `error` | 错误处理规范 | 处理错误时 |
| `testing` | 测试策略 | 编写测试时 |
| `async` | 异步编程规范 | 异步代码时 |
| `web` | Web 开发规范 | Web 开发时 |

## core - Python 核心规范

### 编程规范

- 遵循 PEP 8 编码规范
- 使用 Python 3.8+ 特性
- 优先使用标准库

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块 | snake_case | `my_module.py` |
| 类 | PascalCase | `MyClass` |
| 函数 | snake_case | `my_function` |
| 变量 | snake_case | `my_variable` |
| 常量 | UPPER_SNAKE_CASE | `MY_CONSTANT` |

### 项目结构

```
my-project/
├── src/
│   └── mypackage/
│       ├── __init__.py
│       ├── core.py
│       ├── models.py
│       └── utils.py
├── tests/
│   ├── conftest.py
│   ├── test_core.py
│   └── test_models.py
├── pyproject.toml
└── README.md
```

## types - 类型提示规范

### 基本类型

```python
from typing import List, Dict, Optional, Union

def process(
    items: List[str],
    config: Dict[str, Any],
    timeout: Optional[float] = None,
) -> Union[Result, None]:
    ...
```

### 泛型

```python
from typing import TypeVar, Generic

T = TypeVar('T')

class Container(Generic[T]):
    def __init__(self, value: T) -> None:
        self.value = value
```

### Protocol

```python
from typing import Protocol

class Drawable(Protocol):
    def draw(self) -> None: ...
```

## error - 错误处理规范

### 异常定义

```python
class AppError(Exception):
    """应用基础异常."""

class ValidationError(AppError):
    """验证错误."""

class NotFoundError(AppError):
    """资源未找到."""
```

### 异常处理

```python
try:
    result = process(data)
except ValidationError as e:
    logger.error("validation failed", error=str(e))
    raise
except Exception as e:
    logger.exception("unexpected error")
    raise AppError("process failed") from e
```

## testing - 测试策略

### 测试结构

```python
import pytest

class TestUserService:
    """用户服务测试."""

    @pytest.fixture
    def service(self):
        return UserService()

    def test_create_user(self, service):
        """测试创建用户."""
        user = service.create(name="test")
        assert user.name == "test"
```

### 参数化测试

```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("World", "WORLD"),
    ("", ""),
])
def test_uppercase(input, expected):
    assert input.upper() == expected
```

## async - 异步编程规范

### 基本用法

```python
import asyncio

async def fetch_data(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

async def main():
    data = await fetch_data("https://api.example.com")
    print(data)

asyncio.run(main())
```

### 并发控制

```python
async def process_all(items: list) -> list:
    semaphore = asyncio.Semaphore(10)

    async def limited(item):
        async with semaphore:
            return await process(item)

    return await asyncio.gather(*[limited(i) for i in items])
```

## web - Web 开发规范

### FastAPI 示例

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class User(BaseModel):
    name: str
    email: str

@app.post("/users")
async def create_user(user: User) -> User:
    return user

@app.get("/users/{user_id}")
async def get_user(user_id: int) -> User:
    if user_id not in users:
        raise HTTPException(status_code=404, detail="User not found")
    return users[user_id]
```
