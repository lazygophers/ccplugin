---
name: python-error
description: Python 异常处理与结构化日志规范。涵盖自定义异常层次、except* / ExceptionGroup、structlog 结构化日志、Context Manager 资源管理、错误传播策略。在设计异常类型、配置日志、排查异常、写资源清理代码时使用。也触发于"异常处理"、"自定义异常"、"structlog"、"logging"、"try/except"。
---

# Python 错误处理与日志 (2026)

## 自定义异常层次

每个项目定义一个根异常, 业务异常都继承自它:

```python
class AppError(Exception):
    """应用根异常。所有业务异常继承自此。"""


class ValidationError(AppError):
    def __init__(self, field: str, message: str) -> None:
        super().__init__(f"{field}: {message}")
        self.field = field


class NotFoundError(AppError):
    def __init__(self, resource: str, id: int | str) -> None:
        super().__init__(f"{resource} #{id} not found")
        self.resource = resource
        self.id = id


class ExternalServiceError(AppError):
    """外部服务调用失败 (可重试)。"""
```

好处:
- 调用方 `except AppError` 捕获全部业务异常
- `except Exception` 仅用于框架边界 (HTTP handler, async task 顶层)
- 异常携带结构化字段, 便于日志和 API 响应

## 异常处理三原则

1. **只捕获具体异常类型**, 不写裸 `except:` 或 `except Exception:` (除非顶层 handler)
2. **不吞异常**: 至少 log + re-raise, 或转换成上层异常
3. **保留 traceback**: `raise NewError(...) from e` (用 `from`, 不要 `raise NewError(str(e))`)

```python
# good
try:
    user = await db.get_user(uid)
except DatabaseConnectionError as e:
    log.error("db_unavailable", user_id=uid, exc_info=True)
    raise ExternalServiceError("user-service") from e

# bad - 吞异常
try:
    user = await db.get_user(uid)
except Exception:
    user = None  # 静默失败, 上层无法察觉
```

## except* 与 ExceptionGroup (3.11+)

并发任务 (TaskGroup, asyncio.gather) 会抛 `ExceptionGroup`, 必须用 `except*`:

```python
async with asyncio.TaskGroup() as tg:
    tg.create_task(fetch_a())
    tg.create_task(fetch_b())
# 若两个都失败, raise ExceptionGroup([err_a, err_b])

try:
    await run_pipeline()
except* ValidationError as eg:
    for e in eg.exceptions:
        log.warning("validation_failed", error=str(e))
except* ExternalServiceError as eg:
    raise  # 让上层重试
```

## 结构化日志 (structlog)

不要用 `print` 调试, 不要用裸 `logging` 拼字符串。用 structlog 输出 JSON:

```python
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
)

log = structlog.get_logger()

# 业务代码: 键值对而非 f-string
log.info("user_created", user_id=user.id, email=user.email)
log.error("payment_failed", order_id=oid, amount=amt, exc_info=True)
```

关键约定:
- 事件名用 `snake_case`, 动词过去式 (`user_created` 而非 `creating user`)
- 上下文用 `structlog.contextvars.bind_contextvars(request_id=...)` 注入, 不在每行手传
- 异常用 `exc_info=True` 自动附带 traceback
- 不要把敏感数据 (password, token, full PII) 写日志, 用 redaction processor

## logging 标准库 (无 structlog 时)

老项目仍用 stdlib logging 也可, 但配置 dictConfig + JSON formatter:

```python
import logging
logger = logging.getLogger(__name__)  # 不要 logging.getLogger() 拿 root

logger.error("payment failed for order=%s amount=%s", oid, amt, exc_info=True)
```

不要用 f-string 拼日志消息 (字符串会先求值, 即使日志级别被过滤掉)。用 `%s` 占位符。

## Context Manager 资源管理

任何需要清理的资源都用 `with` / `async with`, 不要手写 try/finally:

```python
# sync
from contextlib import contextmanager

@contextmanager
def transaction(db):
    tx = db.begin()
    try:
        yield tx
        tx.commit()
    except Exception:
        tx.rollback()
        raise

with transaction(db) as tx:
    tx.execute(...)

# async
async with httpx.AsyncClient() as client:
    resp = await client.get(url)
```

多资源用 `contextlib.ExitStack` / `AsyncExitStack`, 不要嵌套 with。

## API 边界错误转换

FastAPI / Litestar 等 Web 框架边界, 把业务异常转 HTTP 响应:

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(NotFoundError)
async def not_found_handler(req: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={
        "error": "not_found",
        "resource": exc.resource,
        "id": exc.id,
    })
```

业务代码只 raise 领域异常, handler 统一翻译。不要在业务函数里 raise `HTTPException`。

## 反模式

- `except: pass` / `except Exception: pass` (静默失败)
- `raise Exception("...")` (用具体异常类)
- `logger.error(f"failed: {e}")` (丢 traceback, 用 `exc_info=True`)
- `print(...)` 调试代码留在生产
- 在 library 代码里配置 logging (库只 `getLogger(__name__)`, 应用层配置)
- 把异常 str 化后再 raise (丢失原始信息, 用 `raise X from e`)
