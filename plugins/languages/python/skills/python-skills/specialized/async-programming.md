# Python 异步编程规范

## 核心原则

### ✅ 必须遵守

1. **使用 asyncio** - Python 3.11+ 优先使用 `asyncio` 而非其他异步框架
2. **TaskGroup 优先** - Python 3.11+ 使用 `asyncio.TaskGroup` 替代 `gather`/`wait`
3. **避免阻塞** - 永远不要在异步函数中执行阻塞操作
4. **正确的上下文管理** - 异步资源使用 `async with` 管理
5. **明确的异常处理** - 异步函数必须有清晰的异常处理策略
6. **超时控制** - 所有 I/O 操作都应该有超时限制

### ❌ 禁止行为

- 在 async 函数中使用阻塞 I/O（如 `time.sleep`、`requests.get`）
- 使用 `asyncio.create_task` 但不等待结果
- 在循环中无限制地创建任务
- 忽略 `Future`/`Task` 的异常
- 混用同步和异步代码
- 在 async 函数中使用 `run_in_executor` 执行 CPU 密集任务

## asyncio 最佳实践

### 异步函数定义

```python
# ✅ 正确 - 使用清晰的异步函数签名
async def fetch_user(user_id: int) -> User:
    """异步获取用户信息.

    Args:
        user_id: 用户 ID

    Returns:
        用户对象

    Raises:
        NotFoundError: 用户不存在
        ServiceError: 服务不可用
    """
    try:
        async with http_client.get(f"/api/users/{user_id}") as response:
            response.raise_for_status()
            data = await response.json()
            return User.model_validate(data)
    except httpx.HTTPStatusError as e:
        logger.error("http error: %s", e)
        raise NotFoundError("User", user_id) from e
    except httpx.RequestError as e:
        logger.error("request failed: %s", e)
        raise ServiceError("Service unavailable") from e

# ❌ 错误 - 没有异常处理
async def fetch_user_bad(user_id: int) -> User:
    async with http_client.get(f"/api/users/{user_id}") as response:
        return await response.json()
```

### 并发模式（Python 3.11+）

```python
# ✅ 推荐 - 使用 TaskGroup（Python 3.11+）
async def fetch_multiple_users(user_ids: list[int]) -> list[User]:
    """批量获取用户，使用 TaskGroup 管理并发."""
    users = []

    async with asyncio.TaskGroup() as tg:
        tasks = {
            user_id: tg.create_task(fetch_user(user_id))
            for user_id in user_ids
        }

    # TaskGroup 确保所有任务完成或抛出异常
    for user_id, task in tasks.items():
        users.append(task.result())

    return users

# ✅ 兼容 - 使用 asyncio.gather（Python 3.10-）
async def fetch_multiple_users_compat(user_ids: list[int]) -> list[User]:
    """批量获取用户，使用 gather 管理."""
    tasks = [fetch_user(uid) for uid in user_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    users = []
    for user_id, result in zip(user_ids, results):
        if isinstance(result, Exception):
            logger.warning("failed to fetch user %s: %s", user_id, result)
        else:
            users.append(result)

    return users

# ✅ 推荐 - 使用 as_completed 获取流式结果
async def fetch_users_streaming(user_ids: list[int]) -> AsyncIterator[User]:
    """流式获取用户，先完成的先返回."""
    tasks = [asyncio.create_task(fetch_user(uid)) for uid in user_ids]

    for task in asyncio.as_completed(tasks):
        try:
            user = await task
            yield user
        except NotFoundError as e:
            logger.warning("user not found: %s", e)
        except ServiceError as e:
            logger.error("service error: %s", e)

# ❌ 错误 - 无限制创建任务
async def fetch_users_unbounded(ids: list[int]) -> list[User]:
    # 危险：可能创建数千个并发连接
    tasks = [asyncio.create_task(fetch_user(i)) for i in ids]
    return await asyncio.gather(*tasks)
```

### 限制并发数量

```python
# ✅ 正确 - 使用 Semaphore 限制并发
async def fetch_many_with_limit(
    ids: list[int],
    max_concurrent: int = 10,
) -> list[User]:
    """限制并发数量的批量获取."""
    semaphore = asyncio.Semaphore(max_concurrent)
    results = []
    errors = []

    async def bounded_fetch(user_id: int) -> User | None:
        async with semaphore:
            try:
                return await fetch_user(user_id)
            except NotFoundError:
                return None

    tasks = [bounded_fetch(uid) for uid in ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    users = [r for r in results if isinstance(r, User)]
    return users

# ✅ 推荐 - 使用 asyncio.Queue 实现工作池
async def fetch_with_worker_pool(ids: list[int], pool_size: int = 5) -> list[User]:
    """使用工作池模式处理任务."""
    queue: asyncio.Queue[int] = asyncio.Queue()
    result_queue: asyncio.Queue[User] = asyncio.Queue()

    # 填充任务队列
    for user_id in ids:
        await queue.put(user_id)

    async def worker() -> None:
        while True:
            try:
                user_id = queue.get_nowait()
            except asyncio.QueueEmpty:
                break

            try:
                user = await fetch_user(user_id)
                await result_queue.put(user)
            except Exception as e:
                logger.error("worker error: %s", e)
            finally:
                queue.task_done()

    # 启动工作协程
    workers = [asyncio.create_task(worker()) for _ in range(pool_size)]
    await queue.join()

    # 取消剩余工作协程
    for w in workers:
        w.cancel()

    # 收集结果
    users = []
    while not result_queue.empty():
        users.append(await result_queue.get())

    return users
```

## 避免阻塞事件循环

### 阻塞操作检测

```python
# ❌ 禁止 - 在 async 函数中使用阻塞 I/O
async def process_file_bad(path: str) -> str:
    # 阻塞事件循环！
    with open(path, "r") as f:
        return f.read()

# ❌ 禁止 - 使用 time.sleep
async def wait_bad(seconds: int) -> None:
    # 阻塞事件循环！
    time.sleep(seconds)

# ❌ 禁止 - 使用 requests 库
async def fetch_url_bad(url: str) -> dict:
    # 阻塞事件循环！
    response = requests.get(url)
    return response.json()

# ✅ 正确 - 使用 aiofiles
import aiofiles

async def process_file(path: str) -> str:
    """异步读取文件."""
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        return await f.read()

# ✅ 正确 - 使用 asyncio.sleep
async def wait_async(seconds: int) -> None:
    """异步等待."""
    await asyncio.sleep(seconds)

# ✅ 正确 - 使用 httpx/aiohttp
async def fetch_url(url: str) -> dict:
    """异步 HTTP 请求."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
```

### CPU 密集任务处理

```python
# ✅ 正确 - 使用 run_in_executor 处理 CPU 密集任务
import functools
from concurrent.futures import ProcessPoolExecutor

# 进程池用于 CPU 密集任务
process_pool = ProcessPoolExecutor(max_workers=4)


def heavy_computation(data: list[int]) -> int:
    """CPU 密集计算（在单独进程中运行）."""
    # 这是一个同步函数，但会在独立进程中执行
    return sum(x ** 2 for x in data)


async def compute_heavy_async(data: list[int]) -> int:
    """异步包装 CPU 密集任务."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        process_pool,
        heavy_computation,
        data,
    )


# ✅ 正确 - 使用 functools.partial 预绑定参数
async def batch_compute(data_chunks: list[list[int]]) -> list[int]:
    """批量计算."""
    loop = asyncio.get_event_loop()
    tasks = []

    for chunk in data_chunks:
        task = loop.run_in_executor(
            process_pool,
            functools.partial(heavy_computation, chunk),
        )
        tasks.append(task)

    return await asyncio.gather(*tasks)
```

### 线程池用于 I/O 密集阻塞操作

```python
# ✅ 正确 - 使用线程池处理阻塞 I/O
from concurrent.futures import ThreadPoolExecutor

# 线程池用于 I/O 密集阻塞任务
thread_pool = ThreadPoolExecutor(max_workers=10)


async def run_blocking_io(operation: Callable[[], T]) -> T:
    """在线程池中运行阻塞 I/O 操作."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, operation)


# 使用示例
def sync_database_query(query: str) -> list[dict]:
    """同步数据库查询（阻塞）."""
    # 使用同步数据库驱动
    connection = psycopg2.connect(DATABASE_URL)
    cursor = connection.cursor()
    cursor.execute(query)
    return cursor.fetchall()


async def query_async(query: str) -> list[dict]:
    """异步包装同步数据库查询."""
    return await run_blocking_io(lambda: sync_database_query(query))
```

## 异步上下文管理器

### 标准异步上下文管理器

```python
# ✅ 正确 - 使用 async with 管理异步资源
import aiohttp
import aiofiles


async def process_api_data(url: str, output_path: str) -> None:
    """从 API 获取数据并保存到文件."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            data = await response.json()

    # 使用 aiofiles 异步写入
    async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(data, ensure_ascii=False, indent=2))


# ❌ 错误 - 在 async with 中使用同步资源
async def process_bad(url: str, output_path: str) -> None:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()

    # 危险！同步文件写入会阻塞
    with open(output_path, "w") as f:
        f.write(json.dumps(data))
```

### 自定义异步上下文管理器

```python
# ✅ 推荐 - 使用 @asynccontextmanager
from contextlib import asynccontextmanager


@asynccontextmanager
async def database_transaction(session: AsyncSession):
    """数据库事务上下文管理器."""
    try:
        await session.begin()
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error("transaction failed, rolled back: %s", e)
        raise


# 使用
async def create_user(user_data: dict) -> User:
    async with database_transaction(async_session) as session:
        user = User(**user_data)
        session.add(user)
        await session.flush()
        return user


# ✅ 完整的异步上下文管理器类
class AsyncTimer:
    """异步计时器上下文管理器."""

    def __init__(self, name: str):
        self.name = name
        self.start_time: float | None = None

    async def __aenter__(self) -> "AsyncTimer":
        self.start_time = asyncio.get_event_loop().time()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        elapsed = asyncio.get_event_loop().time() - self.start_time
        logger.info(f"{self.name} took {elapsed:.4f}s")


# 使用
async def process_with_timing() -> None:
    async with AsyncTimer("data processing"):
        await process_data()
```

## 超时控制

### 设置超时

```python
# ✅ 推荐 - 使用 asyncio.timeout（Python 3.11+）
async def fetch_with_timeout(url: str, timeout: float = 5.0) -> dict:
    """带超时的 HTTP 请求."""
    try:
        async with asyncio.timeout(timeout):
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
                return await response.json()
    except TimeoutError:
        logger.error("request timeout after %ss", timeout)
        raise ServiceError("Request timeout") from None


# ✅ 兼容 - 使用 asyncio.wait_for（Python 3.10-）
async def fetch_with_timeout_compat(url: str, timeout: float = 5.0) -> dict:
    """带超时的 HTTP 请求（兼容版本）."""
    try:
        async with httpx.AsyncClient() as client:
            response = await asyncio.wait_for(
                client.get(url),
                timeout=timeout,
            )
            response.raise_for_status()
            return await response.json()
    except asyncio.TimeoutError:
        logger.error("request timeout after %ss", timeout)
        raise ServiceError("Request timeout") from None


# ✅ 推荐 - 使用 httpx 内置超时
async def fetch_with_client_timeout(url: str) -> dict:
    """使用 httpx 的超时配置."""
    timeout = httpx.Timeout(
        connect=5.0,   # 连接超时
        read=30.0,     # 读取超时
        write=5.0,     # 写入超时
        pool=10.0,     # 连接池超时
    )

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url)
        response.raise_for_status()
        return await response.json()
```

### 取消处理

```python
# ✅ 正确 - 正确处理取消
async def cancellable_operation(
    task: asyncio.Task,
    timeout: float = 30.0,
) -> None:
    """可取消的操作."""
    try:
        async with asyncio.timeout(timeout):
            await task
    except asyncio.TimeoutError:
        logger.warning("operation timeout, cancelling...")
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            logger.info("task cancelled successfully")
            raise
    except asyncio.CancelledError:
        logger.info("operation cancelled by caller")
        raise


# ✅ 正确 - 使用 shield 保护重要任务
async def critical_task() -> None:
    """必须完成的任务（即使父任务被取消）."""
    logger.info("critical task started")
    await asyncio.sleep(10)
    logger.info("critical task completed")


async def run_with_protection() -> None:
    """使用 shield 保护关键任务."""
    try:
        # shield 会保护任务不被外部取消
        await asyncio.shield(critical_task())
    except asyncio.CancelledError:
        logger.warning("parent cancelled, but critical task continues")
        # 等待关键任务完成
        await critical_task()
```

## 异步迭代器和生成器

### 异步生成器

```python
# ✅ 正确 - 使用异步生成器处理流式数据
from typing import AsyncIterator


async def read_lines_stream(path: str) -> AsyncIterator[str]:
    """逐行异步读取大文件."""
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        async for line in f:
            yield line.strip()


async def process_large_file(path: str) -> int:
    """处理大文件，逐行处理."""
    count = 0
    async for line in read_lines_stream(path):
        # 处理每一行
        await process_line(line)
        count += 1
    return count


# ✅ 正确 - 使用异步生成器分页查询
async def fetch_paginated(
    endpoint: str,
    page_size: int = 100,
) -> AsyncIterator[dict]:
    """分页获取数据."""
    page = 1
    client = httpx.AsyncClient()

    try:
        while True:
            response = await client.get(
                endpoint,
                params={"page": page, "page_size": page_size},
            )
            response.raise_for_status()
            data = response.json()

            if not data["items"]:
                break

            for item in data["items"]:
                yield item

            page += 1
    finally:
        await client.aclose()


async def sync_all_users(endpoint: str) -> None:
    """同步所有用户数据."""
    async for user in fetch_paginated(endpoint):
        await save_user(user)
```

### 异步列表推导

```python
# ✅ 正确 - 使用异步列表推导
async def fetch_all_users(ids: list[int]) -> list[User]:
    """批量获取用户."""
    return [user async for user in fetch_users_streaming(ids)]


# ✅ 正确 - 使用异步字典推导
async def build_user_map(ids: list[int]) -> dict[int, User]:
    """构建用户 ID 到用户的映射."""
    return {
        user.id: user
        async for user in fetch_users_streaming(ids)
    }


# ✅ 正确 - 使用 acomprehension 与 async for
async def filter_active_users(ids: list[int]) -> list[User]:
    """过滤活跃用户."""
    return [
        user
        async for user in fetch_users_streaming(ids)
        if user.is_active
    ]
```

## 异步测试

### pytest-asyncio 配置

```python
# ✅ 正确 - 配置 pytest-asyncio
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

### 异步测试示例

```python
# ✅ 正确 - 异步测试
import pytest


@pytest.mark.asyncio
async def test_fetch_user_success(http_client_mock):
    """测试成功获取用户."""
    # Arrange
    user_id = 123
    http_client_mock.get.return_value = MockResponse(
        {"id": 123, "name": "Alice"},
    )

    # Act
    user = await fetch_user(user_id)

    # Assert
    assert user.id == 123
    assert user.name == "Alice"


@pytest.mark.asyncio
async def test_fetch_user_not_found(http_client_mock):
    """测试用户不存在."""
    # Arrange
    user_id = 999
    http_client_mock.get.side_effect = httpx.HTTPStatusError(
        "Not Found",
        request=Mock(),
        response=MockResponse(status_code=404),
    )

    # Act & Assert
    with pytest.raises(NotFoundError):
        await fetch_user(user_id)


@pytest.mark.asyncio
async def test_concurrent_fetch(http_client_mock):
    """测试并发获取."""
    # Arrange
    user_ids = [1, 2, 3]
    http_client_mock.get.return_value = MockResponse(
        {"id": 1, "name": "User"},
    )

    # Act
    users = await fetch_multiple_users(user_ids)

    # Assert
    assert len(users) == 3
```

### 异步 Fixture

```python
# ✅ 正确 - 异步 fixture
@pytest.fixture
async def async_client():
    """异步 HTTP 客户端 fixture."""
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def database_session():
    """数据库会话 fixture."""
    async with async_session() as session:
        await session.begin()
        yield session
        await session.rollback()


@pytest.mark.asyncio
async def test_create_user(async_client, database_session):
    """测试创建用户."""
    response = await async_client.post(
        "/api/users",
        json={"name": "Alice", "email": "alice@example.com"},
    )
    assert response.status_code == 201
```

## 最佳实践总结

### 1. 结构清晰

```python
# ✅ 正确 - 清晰的异步结构
class UserService:
    """用户服务."""

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def get_user(self, user_id: int) -> User:
        """获取用户."""
        # 实现细节...

    async def list_users(self, limit: int = 100) -> list[User]:
        """列出用户."""
        # 实现细节...

    async def create_user(self, data: dict) -> User:
        """创建用户."""
        # 实现细节...
```

### 2. 资源管理

```python
# ✅ 正确 - 确保资源释放
async def process_many_items(items: list[Item]) -> None:
    """处理多个项目."""
    client = httpx.AsyncClient()
    try:
        await process_items(client, items)
    finally:
        await client.aclose()

# ✅ 推荐 - 使用上下文管理器
async def process_many_items_safe(items: list[Item]) -> None:
    """处理多个项目（自动资源管理）."""
    async with httpx.AsyncClient() as client:
        await process_items(client, items)
```

### 3. 错误处理

```python
# ✅ 正确 - 统一的异步错误处理
async def safe_operation() -> Result:
    """安全的异步操作."""
    try:
        result = await risky_operation()
        return Result.success(result)
    except NotFoundError as e:
        logger.error("not found: %s", e)
        return Result.not_found()
    except ServiceError as e:
        logger.error("service error: %s", e)
        return Result.error(str(e))
    except Exception as e:
        logger.exception("unexpected error: %s", e)
        return Result.error("Unexpected error")
```

## 检查清单

提交异步代码前，确保：

- [ ] 所有异步函数都使用 `async def` 定义
- [ ] 阻塞操作使用 `run_in_executor` 或异步库替代
- [ ] I/O 操作都有超时设置
- [ ] 异步资源使用 `async with` 管理
- [ ] Python 3.11+ 使用 `TaskGroup` 而非 `gather`
- [ ] 限制并发数量（使用 Semaphore 或工作池）
- [ ] 正确处理 `CancelledError`
- [ ] 测试覆盖异步代码
- [ ] 没有在异步函数中使用 `time.sleep`
- [ ] 没有在异步函数中使用阻塞 I/O（如 `open`、`requests`）
