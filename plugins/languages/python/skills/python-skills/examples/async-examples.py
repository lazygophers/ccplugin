"""
Python 异步编程示例

本文件展示了异步编程的正确模式。
遵循 python-skills/specialized/async-programming.md 规范。
"""

import asyncio
import logging
from typing import Any, AsyncIterator
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from contextlib import asynccontextmanager
from functools import partial

logger = logging.getLogger(__name__)


# =============================================================================
# 1. 异步函数定义
# =============================================================================

# ✅ 正确 - 使用清晰的异步函数签名
async def fetch_user(user_id: int) -> dict:
    """异步获取用户信息.

    Args:
        user_id: 用户 ID

    Returns:
        用户对象字典

    Raises:
        NotFoundError: 用户不存在
        ServiceError: 服务不可用
    """
    await asyncio.sleep(0.1)  # 模拟网络延迟

    if user_id == 999:
        raise NotFoundError(f"User {user_id} not found")

    return {
        "id": user_id,
        "name": f"User{user_id}",
        "email": f"user{user_id}@example.com",
    }


class NotFoundError(Exception):
    """资源未找到异常."""
    pass


class ServiceError(Exception):
    """服务异常."""
    pass


# ❌ 错误 - 没有异常处理
async def fetch_user_bad(user_id: int) -> dict:
    """获取用户 - 缺少异常处理."""
    await asyncio.sleep(0.1)
    # 如果出错，调用者不知道如何处理
    return {"id": user_id}


# =============================================================================
# 2. 并发模式（Python 3.11+ TaskGroup）
# =============================================================================

# ✅ 推荐 - 使用 TaskGroup（Python 3.11+）
async def fetch_multiple_users_taskgroup(user_ids: list[int]) -> list[dict]:
    """批量获取用户，使用 TaskGroup 管理并发."""
    if hasattr(asyncio, 'TaskGroup'):
        # Python 3.11+ 使用 TaskGroup
        async with asyncio.TaskGroup() as tg:
            tasks = {
                user_id: tg.create_task(fetch_user(user_id))
                for user_id in user_ids
            }

        # TaskGroup 确保所有任务完成或抛出异常
        return [task.result() for task in tasks.values()]
    else:
        # Python 3.10- 兼容方案
        return await fetch_multiple_users_gather(user_ids)


# ✅ 兼容 - 使用 asyncio.gather（Python 3.10-）
async def fetch_multiple_users_gather(user_ids: list[int]) -> list[dict]:
    """批量获取用户，使用 gather 管理."""
    tasks = [fetch_user(uid) for uid in user_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    users = []
    for user_id, result in zip(user_ids, results):
        if isinstance(result, Exception):
            logger.warning("failed to fetch user %s: %s", user_id, result)
        elif isinstance(result, dict):
            users.append(result)

    return users


# ✅ 推荐 - 使用 as_completed 获取流式结果
async def fetch_users_streaming(user_ids: list[int]) -> AsyncIterator[dict]:
    """流式获取用户，先完成的先返回."""
    tasks = [asyncio.create_task(fetch_user(uid)) for uid in user_ids]

    for task in asyncio.as_completed(tasks):
        try:
            user = await task
            yield user
        except NotFoundError as e:
            logger.warning("user not found: %s", e)


# ❌ 错误 - 无限制创建任务
async def fetch_users_unbounded(ids: list[int]) -> list[dict]:
    """危险：可能创建数千个并发连接."""
    # 不推荐：对于大量 ID，应该限制并发数量
    tasks = [asyncio.create_task(fetch_user(i)) for i in ids]
    return await asyncio.gather(*tasks)


# =============================================================================
# 3. 限制并发数量
# =============================================================================

# ✅ 正确 - 使用 Semaphore 限制并发
async def fetch_many_with_limit(
    ids: list[int],
    max_concurrent: int = 10,
) -> list[dict]:
    """限制并发数量的批量获取."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def bounded_fetch(user_id: int) -> dict | None:
        async with semaphore:
            try:
                return await fetch_user(user_id)
            except NotFoundError:
                logger.warning("user %s not found", user_id)
                return None

    tasks = [bounded_fetch(uid) for uid in ids]
    results = await asyncio.gather(*tasks)

    return [r for r in results if r is not None]


# ✅ 推荐 - 使用 asyncio.Queue 实现工作池
async def fetch_with_worker_pool(
    ids: list[int],
    pool_size: int = 5,
) -> list[dict]:
    """使用工作池模式处理任务."""
    queue: asyncio.Queue[int] = asyncio.Queue()
    result_queue: asyncio.Queue[dict] = asyncio.Queue()

    # 填充任务队列
    for user_id in ids:
        await queue.put(user_id)

    async def worker() -> None:
        """工作协程."""
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


# =============================================================================
# 4. 避免阻塞事件循环
# =============================================================================

# ❌ 禁止 - 在 async 函数中使用阻塞 I/O
async def process_file_bad(path: str) -> str:
    """错误：阻塞事件循环."""
    # 危险！这会阻塞整个事件循环
    with open(path, "r") as f:
        return f.read()


# ❌ 禁止 - 使用 time.sleep
async def wait_bad(seconds: int) -> None:
    """错误：阻塞事件循环."""
    # 危险！这会阻塞整个事件循环
    import time
    time.sleep(seconds)


# ✅ 正确 - 使用 asyncio.sleep
async def wait_async(seconds: int) -> None:
    """异步等待."""
    await asyncio.sleep(seconds)


# ✅ 正确 - 使用 aiofiles（需要安装）
async def process_file_async(path: str) -> str:
    """异步读取文件."""
    # 注意：需要安装 aiofiles
    # async with aiofiles.open(path, "r", encoding="utf-8") as f:
    #     return await f.read()
    # 这里用模拟代码替代
    await asyncio.sleep(0.1)
    return "file content"


# =============================================================================
# 5. CPU 密集任务处理
# =============================================================================

# ✅ 正确 - 使用 run_in_executor 处理 CPU 密集任务
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
            partial(heavy_computation, chunk),
        )
        tasks.append(task)

    return await asyncio.gather(*tasks)


# =============================================================================
# 6. 线程池用于 I/O 密集阻塞操作
# =============================================================================

# ✅ 正确 - 使用线程池处理阻塞 I/O
thread_pool = ThreadPoolExecutor(max_workers=10)


async def run_blocking_io(operation, *args) -> Any:
    """在线程池中运行阻塞 I/O 操作."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(thread_pool, operation, *args)


# 使用示例
def sync_database_query(query: str) -> list[dict]:
    """同步数据库查询（阻塞）."""
    # 模拟阻塞操作
    import time
    time.sleep(0.1)
    return [{"id": 1, "name": "Alice"}]


async def query_async(query: str) -> list[dict]:
    """异步包装同步数据库查询."""
    return await run_blocking_io(sync_database_query, query)


# =============================================================================
# 7. 异步上下文管理器
# =============================================================================

# ✅ 正确 - 使用 async with 管理异步资源
@asynccontextmanager
async def async_http_client():
    """异步 HTTP 客户端上下文管理器."""
    client = {"active": True}
    try:
        yield client
    finally:
        client["active"] = False
        logger.info("async client closed")


async def process_api_data(url: str) -> dict:
    """从 API 获取数据."""
    async with async_http_client():
        # 模拟 API 调用
        await asyncio.sleep(0.1)
        return {"data": "example"}


# ✅ 正确 - 完整的异步上下文管理器类
class AsyncTimer:
    """异步计时器上下文管理器."""

    def __init__(self, name: str):
        self.name = name
        self.start_time = None

    async def __aenter__(self) -> "AsyncTimer":
        self.start_time = asyncio.get_event_loop().time()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        elapsed = asyncio.get_event_loop().time() - self.start_time
        logger.info("%s took %.4fs", self.name, elapsed)


# =============================================================================
# 8. 超时控制
# =============================================================================

# ✅ 推荐 - 使用 asyncio.timeout（Python 3.11+）
async def fetch_with_timeout_new(user_id: int, timeout: float = 1.0) -> dict:
    """带超时的 HTTP 请求."""
    try:
        if hasattr(asyncio, 'timeout'):
            async with asyncio.timeout(timeout):
                return await fetch_user(user_id)
        else:
            return await fetch_with_timeout_old(user_id, timeout)
    except asyncio.TimeoutError:
        logger.error("request timeout after %ss", timeout)
        raise ServiceError("Request timeout") from None


# ✅ 兼容 - 使用 asyncio.wait_for（Python 3.10-）
async def fetch_with_timeout_old(user_id: int, timeout: float = 1.0) -> dict:
    """带超时的 HTTP 请求（兼容版本）."""
    try:
        return await asyncio.wait_for(fetch_user(user_id), timeout=timeout)
    except asyncio.TimeoutError:
        logger.error("request timeout after %ss", timeout)
        raise ServiceError("Request timeout") from None


# =============================================================================
# 9. 取消处理
# =============================================================================

# ✅ 正确 - 正确处理取消
async def cancellable_operation(
    task: asyncio.Task,
    timeout: float = 1.0,
) -> None:
    """可取消的操作."""
    try:
        if hasattr(asyncio, 'timeout'):
            async with asyncio.timeout(timeout):
                await task
        else:
            await asyncio.wait_for(task, timeout=timeout)
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
async def critical_task() -> str:
    """必须完成的任务（即使父任务被取消）."""
    logger.info("critical task started")
    await asyncio.sleep(0.5)
    logger.info("critical task completed")
    return "critical result"


async def run_with_protection() -> str:
    """使用 shield 保护关键任务."""
    try:
        # shield 会保护任务不被外部取消
        result = await asyncio.shield(critical_task())
        return result
    except asyncio.CancelledError:
        logger.warning("parent cancelled, but critical task continues")
        # 等待关键任务完成
        return await critical_task()


# =============================================================================
# 10. 异步迭代器和生成器
# =============================================================================

# ✅ 正确 - 使用异步生成器处理流式数据
async def read_lines_stream(path: str) -> AsyncIterator[str]:
    """逐行异步读取大文件."""
    lines = ["line 1", "line 2", "line 3"]
    for line in lines:
        await asyncio.sleep(0.05)
        yield line


async def process_large_file(path: str) -> int:
    """处理大文件，逐行处理."""
    count = 0
    async for line in read_lines_stream(path):
        await process_line(line)
        count += 1
    return count


async def process_line(line: str) -> None:
    """处理单行数据."""
    await asyncio.sleep(0.01)


# ✅ 正确 - 异步列表推导
async def fetch_all_users(ids: list[int]) -> list[dict]:
    """批量获取用户."""
    return [user async for user in fetch_users_streaming(ids)]


# ✅ 正确 - 异步字典推导
async def build_user_map(ids: list[int]) -> dict[int, dict]:
    """构建用户 ID 到用户的映射."""
    return {
        user["id"]: user
        async for user in fetch_users_streaming(ids)
    }


# ✅ 正确 - 异步过滤
async def filter_active_users(ids: list[int]) -> list[dict]:
    """过滤活跃用户."""
    return [
        user
        async for user in fetch_users_streaming(ids)
        if user.get("id", 0) % 2 == 0  # 模拟活跃用户条件
    ]


# =============================================================================
# 运行示例
# =============================================================================

async def main() -> None:
    """运行所有示例."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    print("\n=== 异步函数示例 ===")
    user = await fetch_user(1)
    print(f"Fetched user: {user}")

    print("\n=== TaskGroup 示例 ===")
    users = await fetch_multiple_users_taskgroup([1, 2, 3])
    print(f"Fetched {len(users)} users")

    print("\n=== 限制并发示例 ===")
    users = await fetch_many_with_limit(list(range(1, 21)), max_concurrent=5)
    print(f"Fetched {len(users)} users with concurrency limit")

    print("\n=== 工作池示例 ===")
    users = await fetch_with_worker_pool([1, 2, 3, 4, 5], pool_size=2)
    print(f"Fetched {len(users)} users with worker pool")

    print("\n=== 超时控制示例 ===")
    user = await fetch_with_timeout_new(1, timeout=1.0)
    print(f"Fetched user with timeout: {user}")

    print("\n=== 异步计时器示例 ===")
    async with AsyncTimer("data processing"):
        await asyncio.sleep(0.1)

    print("\n=== 异步迭代器示例 ===")
    count = await process_large_file("dummy.txt")
    print(f"Processed {count} lines")

    print("\n=== 异步列表推导示例 ===")
    users = await fetch_all_users([1, 2, 3])
    print(f"Fetched users via comprehension: {len(users)}")


if __name__ == "__main__":
    asyncio.run(main())
