---
name: error
description: Python 错误处理和日志 - 结构化日志（structlog）、异常设计、Context Manager。现代错误处理的最佳实践。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Python 错误处理和日志

## 适用 Agents

- **python:dev** - 开发阶段使用
- **python:debug** - 调试时优先应用
- **python:test** - 测试错误处理逻辑

## 相关 Skills

- **Skills(python:core)** - 基础规范
- **Skills(python:types)** - 异常类型注解
- **Skills(python:async)** - 异步异常处理

## 核心原则

### 1. 结构化日志优于 print

**使用 structlog 替代 print 调试**：

```python
import structlog

log = structlog.get_logger()

# ✅ 正确：结构化日志
log.info("user_created",
    user_id=123,
    username="alice",
    email="alice@example.com",
    ip_address="192.168.1.1"
)

# 输出（JSON 格式，易于解析）
# {"event": "user_created", "user_id": 123, "username": "alice", ...}

# ❌ 错误：print 调试
print(f"User created: {username}")  # 无结构、难以搜索
```

### 2. 具体异常捕获

```python
# ✅ 正确：捕获具体异常
try:
    result = process_data(data)
except ValueError as e:
    log.error("validation_failed", error=str(e), data=data)
    raise
except FileNotFoundError as e:
    log.warning("file_not_found", path=str(e))
    return None

# ❌ 错误：裸 except
try:
    result = process_data(data)
except:  # 捕获所有异常，包括 KeyboardInterrupt！
    pass

# ⚠️ 谨慎使用：Exception
try:
    result = process_data(data)
except Exception as e:  # 可以，但要记录日志
    log.exception("unexpected_error")
    raise
```

### 3. 自定义异常层次

```python
# 异常基类
class AppError(Exception):
    """应用错误基类"""
    pass

class ValidationError(AppError):
    """数据验证错误"""

    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")

class DatabaseError(AppError):
    """数据库错误"""
    pass

class NotFoundError(AppError):
    """资源未找到"""

    def __init__(self, resource: str, id: int) -> None:
        self.resource = resource
        self.id = id
        super().__init__(f"{resource} not found: {id}")
```

## structlog 配置

### 基础配置

```python
import structlog

# 配置 structlog
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),  # JSON 格式输出
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

log = structlog.get_logger()
```

### 使用示例

```python
import structlog

log = structlog.get_logger()

# 基础日志
log.info("server_started", port=8000, workers=4)

# 错误日志
log.error("database_connection_failed",
    host="localhost",
    port=5432,
    error="connection refused"
)

# 异常日志（自动包含堆栈跟踪）
try:
    risky_operation()
except Exception:
    log.exception("operation_failed", operation="risky")

# 上下文绑定
log = log.bind(user_id=123, request_id="abc-123")
log.info("user_action", action="login")
log.info("user_action", action="logout")
# 两条日志都包含 user_id=123, request_id="abc-123"
```

## Context Manager 最佳实践

### 1. 资源管理

```python
from contextlib import contextmanager, asynccontextmanager
import structlog

log = structlog.get_logger()

# 同步 context manager
@contextmanager
def database_transaction():
    """数据库事务管理"""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
        log.info("transaction_committed")
    except Exception as e:
        conn.rollback()
        log.error("transaction_rollback", error=str(e))
        raise
    finally:
        conn.close()

# 使用
with database_transaction() as conn:
    conn.execute("INSERT INTO users ...")

# 异步 context manager
@asynccontextmanager
async def async_database_transaction():
    """异步数据库事务"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
            log.info("async_transaction_committed")
        except Exception as e:
            await session.rollback()
            log.error("async_transaction_rollback", error=str(e))
            raise
```

### 2. 计时器

```python
import time
from contextlib import contextmanager

@contextmanager
def timer(operation: str):
    """性能计时"""
    start = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start
        log.info("operation_completed",
            operation=operation,
            duration_ms=round(duration * 1000, 2)
        )

# 使用
with timer("process_data"):
    process_large_dataset()
```

### 3. 临时状态管理

```python
from contextlib import contextmanager

@contextmanager
def temporary_change(obj, attr: str, new_value):
    """临时修改对象属性"""
    old_value = getattr(obj, attr)
    setattr(obj, attr, new_value)
    try:
        yield
    finally:
        setattr(obj, attr, old_value)

# 使用
with temporary_change(config, "debug", True):
    run_debug_operation()
# config.debug 自动恢复为原值
```

## 异步异常处理

### 异步函数中的异常

```python
import asyncio
import structlog

log = structlog.get_logger()

async def fetch_user(user_id: int) -> User:
    """异步获取用户（带异常处理）"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"/users/{user_id}")
            response.raise_for_status()
            return User(**response.json())
    except httpx.HTTPStatusError as e:
        log.error("http_error",
            user_id=user_id,
            status_code=e.response.status_code
        )
        raise NotFoundError("User", user_id)
    except httpx.RequestError as e:
        log.error("network_error",
            user_id=user_id,
            error=str(e)
        )
        raise
```

### asyncio.gather 异常处理

```python
async def fetch_all_users(user_ids: list[int]) -> list[User | None]:
    """并行获取用户，忽略错误"""
    tasks = [fetch_user(uid) for uid in user_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 分离成功和失败
    users = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            log.error("fetch_failed",
                user_id=user_ids[i],
                error=str(result)
            )
            users.append(None)
        else:
            users.append(result)

    return users
```

## Result 类型模式（可选）

```python
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar('T')
E = TypeVar('E', bound=Exception)

@dataclass
class Ok(Generic[T]):
    """成功结果"""
    value: T

@dataclass
class Err(Generic[E]):
    """失败结果"""
    error: E

Result = Ok[T] | Err[E]

def safe_divide(a: float, b: float) -> Result[float, ValueError]:
    """安全除法（返回 Result 而非抛异常）"""
    if b == 0:
        return Err(ValueError("division by zero"))
    return Ok(a / b)

# 使用
result = safe_divide(10, 2)
match result:
    case Ok(value):
        print(f"Result: {value}")
    case Err(error):
        log.error("division_failed", error=str(error))
```

## Red Flags：AI 常见误区

| AI 可能的理性化解释 | 实际应该检查的内容 |
|---------------------|-------------------|
| "print 调试足够了" | ✅ 是否使用了 structlog 或 logging？ |
| "裸 except 能捕获所有错误" | ✅ 是否捕获了具体异常类型？ |
| "异常处理会影响性能" | ✅ 是否正确使用了 try-except？ |
| "不需要自定义异常" | ✅ 是否创建了有意义的异常类？ |
| "日志记录太啰嗦" | ✅ 是否记录了足够的上下文信息？ |
| "f-string 格式化日志" | ✅ 是否使用了结构化日志字段？ |

## FastAPI 集成

### 异常处理器

```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import structlog

app = FastAPI()
log = structlog.get_logger()

class AppException(Exception):
    """应用异常基类"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code

@app.exception_handler(AppException)
async def app_exception_handler(request, exc: AppException):
    log.error("app_exception",
        path=request.url.path,
        message=exc.message,
        status_code=exc.status_code
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    log.exception("unhandled_exception", path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )
```

## 完整示例

### 带完整错误处理的 API

```python
import structlog
from fastapi import FastAPI, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()
log = structlog.get_logger()

class UserNotFoundError(Exception):
    """用户未找到"""
    pass

async def get_user_from_db(db: AsyncSession, user_id: int) -> User:
    """从数据库获取用户"""
    try:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            raise UserNotFoundError(f"User {user_id} not found")

        log.info("user_retrieved", user_id=user_id)
        return user

    except UserNotFoundError:
        log.warning("user_not_found", user_id=user_id)
        raise
    except Exception as e:
        log.exception("database_error", user_id=user_id)
        raise

@app.get("/users/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """获取用户端点"""
    try:
        with timer(f"get_user_{user_id}"):
            user = await get_user_from_db(db, user_id)
            return user
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception:
        log.exception("get_user_failed", user_id=user_id)
        raise HTTPException(status_code=500, detail="Internal server error")
```

## 检查清单

### 日志
- [ ] 使用 structlog 替代 print
- [ ] 日志使用 JSON 格式
- [ ] 记录足够的上下文信息
- [ ] 异常包含堆栈跟踪

### 异常处理
- [ ] 捕获具体异常类型
- [ ] 没有裸 except
- [ ] 异常记录日志后再 raise
- [ ] 创建自定义异常层次

### Context Manager
- [ ] 使用 with 语句管理资源
- [ ] 数据库事务使用 context manager
- [ ] 性能计时使用 context manager

### 异步异常
- [ ] 异步函数正确处理异常
- [ ] asyncio.gather 使用 return_exceptions=True
- [ ] 异步 context manager 正确实现
