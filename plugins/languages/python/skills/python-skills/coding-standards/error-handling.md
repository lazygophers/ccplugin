# Python 错误处理规范

## 核心原则

### ✅ 必须遵守

1. **多行处理** - 所有异常必须多行处理，记录日志
2. **统一日志格式** - 使用 `logger.error("error: %s", e)` 统一格式
3. **明确异常类型** - 捕获具体异常类型，避免裸 except
4. **异常层次结构** - 定义清晰的异常层次，继承自合适的基础类
5. **上下文管理器** - 资源管理使用上下文管理器（with 语句）
6. **finally 清理** - 确保资源在 finally 块中正确释放

### ❌ 禁止行为

- 静默失败（空 except 块）
- 裸 except（`except:` 或 `except Exception:` 无区别捕获）
- 吞掉异常（不记录也不重新抛出）
- 在循环中捕获异常不记录
- 使用 assert 处理业务逻辑错误
- 过度使用 try-except 而非条件判断

## 标准错误处理模式

### 基本模式（强制）

```python
# ✅ 必须 - 多行处理 + 日志
try:
    data = read_file(path)
except FileNotFoundError as e:
    logger.error("error: %s", e)
    return None
except PermissionError as e:
    logger.error("error: %s", e)
    raise

# ✅ 正确 - 记录后重新抛出
try:
    process_data(data)
except ValueError as e:
    logger.error("error: %s", e)
    raise  # 重新抛出原始异常

# ❌ 禁止 - 静默失败
try:
    data = read_file(path)
except FileNotFoundError:
    pass  # 忽略错误

# ❌ 禁止 - 裸 except
try:
    data = read_file(path)
except:  # 捕获所有异常，包括 KeyboardInterrupt
    pass

# ❌ 禁止 - 过于宽泛的异常捕获
try:
    data = read_file(path)
except Exception as e:
    logger.error("error: %s", e)
    # 没有区分异常类型
```

### 异常类型判断

```python
# ✅ 使用 isinstance 检查异常类型
try:
    operation()
except (ValueError, TypeError) as e:
    logger.error("error: %s", e)
    handle_generic_error(e)

# ✅ 分别处理不同异常
try:
    data = parse_config(path)
except FileNotFoundError as e:
    logger.error("config file not found: %s", e)
    return default_config()
except json.JSONDecodeError as e:
    logger.error("invalid config json: %s", e)
    raise ConfigError(f"Invalid JSON in {path}") from e

# ❌ 禁止 - 捕获所有异常后手动判断
try:
    data = parse_config(path)
except Exception as e:
    if isinstance(e, FileNotFoundError):
        # 应该在 except 中直接指定类型
        pass
```

### 异常链（Exception Chaining）

```python
# ✅ 使用 raise ... from e 保留原始异常
try:
    data = validate(input_data)
except ValueError as e:
    logger.error("validation failed: %s", e)
    raise ProcessingError("Invalid input data") from e

# ✅ 使用 raise ... from None 显式断开异常链
try:
    password = get_password()
except Exception as e:
    logger.error("error: %s", e)
    raise SecurityError("Password check failed") from None  # 隐藏敏感信息

# ❌ 避免 - 不保留原始异常上下文
try:
    data = validate(input_data)
except ValueError:
    raise ProcessingError("Invalid input data")  # 丢失了原始异常
```

## 错误类型设计

### 自定义异常层次结构

```python
# ✅ 正确 - 清晰的异常层次
class AppError(Exception):
    """应用基础异常类"""

    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ValidationError(AppError):
    """验证错误 - 4xx"""

    def __init__(self, message: str, field: str = ""):
        self.field = field
        super().__init__(message, code=400)


class NotFoundError(AppError):
    """资源未找到 - 404"""

    def __init__(self, resource: str, identifier: str):
        self.resource = resource
        self.identifier = identifier
        message = f"{resource} with identifier '{identifier}' not found"
        super().__init__(message, code=404)


class ConflictError(AppError):
    """冲突错误 - 409"""

    def __init__(self, message: str):
        super().__init__(message, code=409)


# 使用示例
def get_user(user_id: int) -> User:
    try:
        return db.query(User).filter_by(id=user_id).one()
    except NoResultFound as e:
        logger.error("user not found: %s", user_id)
        raise NotFoundError("User", str(user_id)) from e
```

### 分层异常定义

```python
# errors/__init__.py
"""
模块级异常定义
"""

# 基础异常
class BaseError(Exception):
    """所有自定义异常的基类"""
    pass


# 数据层异常
class DatabaseError(BaseError):
    """数据库操作错误"""
    pass


class QueryError(DatabaseError):
    """查询错误"""
    pass


class TransactionError(DatabaseError):
    """事务错误"""
    pass


# 服务层异常
class ServiceError(BaseError):
    """服务层错误"""
    pass


class BusinessLogicError(ServiceError):
    """业务逻辑错误"""
    pass


# API 层异常
class APIError(BaseError):
    """API 错误"""

    def __init__(self, message: str, status_code: int = 500):
        self.status_code = status_code
        super().__init__(message)


class BadRequestError(APIError):
    """400 Bad Request"""

    def __init__(self, message: str):
        super().__init__(message, status_code=400)
```

## 上下文管理器使用

### 资源管理

```python
# ✅ 正确 - 使用 with 语句管理资源
def read_config(path: str) -> dict:
    """读取配置文件"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        logger.error("config file not found: %s", e)
        raise
    except json.JSONDecodeError as e:
        logger.error("invalid json in config: %s", e)
        raise

# ✅ 正确 - 多个资源管理
def merge_files(src1: str, src2: str, dst: str) -> None:
    """合并两个文件"""
    try:
        with open(src1, "r") as f1, open(src2, "r") as f2, open(dst, "w") as out:
            out.write(f1.read())
            out.write(f2.read())
    except OSError as e:
        logger.error("file operation failed: %s", e)
        raise

# ❌ 禁止 - 手动管理资源
def read_config_bad(path: str) -> dict:
    f = open(path, "r")
    data = json.load(f)
    f.close()  # 可能因异常而不执行
    return data
```

### 自定义上下文管理器

```python
# ✅ 使用 contextlib.contextmanager 装饰器
from contextlib import contextmanager


@contextmanager
def transaction(session):
    """数据库事务上下文管理器"""
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error("transaction failed, rolled back: %s", e)
        raise


# 使用
with transaction(db.session) as session:
    user = User(name="Alice")
    session.add(user)


# ✅ 实现完整的上下文管理器类
class Timer:
    """计时器上下文管理器"""

    def __init__(self, name: str):
        self.name = name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.perf_counter() - self.start_time
        logger.info(f"{self.name} took {elapsed:.4f}s")
        return False  # 不抑制异常


# 使用
with Timer("data processing"):
    process_data()
```

## 异步错误处理

### 异步函数中的异常处理

```python
# ✅ 正确 - 在 async 函数中处理异常
async def fetch_user(user_id: int) -> User:
    """异步获取用户"""
    try:
        response = await http_client.get(f"/api/users/{user_id}")
        response.raise_for_status()
        return User.parse_obj(response.json())
    except httpx.HTTPStatusError as e:
        logger.error("http error: %s", e)
        raise NotFoundError("User", user_id) from e
    except httpx.RequestError as e:
        logger.error("request failed: %s", e)
        raise ServiceError("Service unavailable") from e


# ✅ 正确 - 处理 asyncio.gather 的异常
async def fetch_multiple_users(user_ids: list[int]) -> list[User]:
    """批量获取用户，部分失败不影响整体"""
    tasks = [fetch_user(uid) for uid in user_ids]

    results = []
    errors = []

    for task in asyncio.as_completed(tasks):
        try:
            user = await task
            results.append(user)
        except NotFoundError as e:
            logger.warning("user not found: %s", e)
            errors.append(e)
        except ServiceError as e:
            logger.error("service error: %s", e)
            errors.append(e)

    if errors:
        logger.warning("completed with %d errors", len(errors))

    return results
```

### 异步上下文管理器

```python
# ✅ 异步上下文管理器
class AsyncSession:
    """异步会话管理器"""

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()


# 使用
async def fetch_data(url: str) -> dict:
    async with AsyncSession() as session:
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error("fetch failed: %s", e)
            raise
```

## 日志规范

### 日志级别和格式

```python
import logging

logger = logging.getLogger(__name__)

# ✅ Debug - 调试信息
logger.debug("processing item: %s", item)

# ✅ Info - 正常流程信息
logger.info("user registered: %s", email)
logger.info("loading config from %s", config_path)

# ✅ Warning - 警告（不影响功能）
logger.warning("cache miss for key: %s", key)
logger.warning("using default config")

# ✅ Error - 错误（功能异常）
logger.error("error: %s", e)
logger.error("failed to save user: %s", e, exc_info=True)

# ✅ Critical - 严重错误
logger.critical("database connection lost: %s", e)
```

### 统一的错误日志格式

```python
# ✅ 简洁统一的错误格式
try:
    process_data(data)
except ProcessingError as e:
    logger.error("error: %s", e)
    raise

# ❌ 避免 - 过于冗长
try:
    process_data(data)
except ProcessingError as e:
    logger.error(
        "An error occurred while processing the data. "
        "The error was of type ProcessingError. "
        "The error message is: %s. "
        "Please check your input and try again.",
        e
    )
    raise
```

### 异常堆栈信息

```python
# ✅ 记录完整堆栈
try:
    risky_operation()
except Exception as e:
    logger.error("operation failed: %s", e, exc_info=True)
    # 或
    logger.exception("operation failed: %s", e)
    raise

# ✅ 在开发环境记录堆栈，生产环境记录简化信息
if settings.DEBUG:
    logger.exception("detailed error: %s", e)
else:
    logger.error("error: %s", e)
```

## 特殊场景处理

### 重试机制

```python
# ✅ 使用 tenacity 库实现重试
from tenacity import retry, stop_after_attempt, wait_exponential


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)
def fetch_with_retry(url: str) -> dict:
    """带重试的网络请求"""
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    return response.json()


# ✅ 自定义重试逻辑
def fetch_with_custom_retry(url: str, max_retries: int = 3) -> dict:
    """带重试的网络请求"""
    last_error = None

    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestError as e:
            last_error = e
            wait_time = 2 ** attempt
            logger.warning("attempt %d failed, retrying in %ds: %s", attempt + 1, wait_time, e)
            time.sleep(wait_time)

    logger.error("all retries exhausted: %s", last_error)
    raise ServiceError("Service unavailable after retries") from last_error
```

### 超时处理

```python
# ✅ 使用信号处理超时（仅 Unix）
import signal
from contextlib import contextmanager


class TimeoutError(Exception):
    """操作超时"""
    pass


@contextmanager
def timeout(seconds: int):
    """超时上下文管理器"""

    def _timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds}s")

    old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


# 使用
try:
    with timeout(5):
        long_running_operation()
except TimeoutError as e:
    logger.error("error: %s", e)
    raise
```

### 优雅关闭

```python
# ✅ 处理 KeyboardInterrupt
def main():
    """主函数"""
    logger.info("starting application")

    try:
        run_application()
    except KeyboardInterrupt:
        logger.info("received interrupt signal, shutting down...")
    except Exception as e:
        logger.error("unexpected error: %s", e, exc_info=True)
        raise
    finally:
        cleanup_resources()
        logger.info("application stopped")


if __name__ == "__main__":
    main()
```

## 检查清单

提交代码前，确保：

- [ ] 所有异常都有明确的类型捕获
- [ ] 异常处理使用多行格式
- [ ] 所有异常都记录了日志
- [ ] 没有使用裸 except（`except:`）
- [ ] 没有空 except 块（静默失败）
- [ ] 资源使用 with 语句管理
- [ ] 重新抛出异常使用 `raise ... from e` 保留链
- [ ] 日志格式统一为 `logger.error("error: %s", e)`
- [ ] 自定义异常有清晰的层次结构
- [ ] 异常信息包含足够的上下文但不包含敏感信息
