---
name: python-async
description: Python 异步编程与并发规范 (asyncio 3.13+)。涵盖 async/await、TaskGroup 结构化并发、httpx 异步 HTTP、aiofiles、超时与取消、free-threading (PEP 703)。在写异步函数、并发调度、I/O 优化、迁移同步代码、调试 async bug 时使用。也触发于"asyncio"、"async/await"、"并发"、"httpx"、"TaskGroup"。
---

# Python 异步编程 (2026)

Python 3.13+, asyncio 优先。3.14 的 free-threading (PEP 703) 解决 CPU 密集, asyncio 仍是 I/O 密集首选。

## 何时用 async

| 场景 | 选择 |
|------|------|
| I/O 密集 (HTTP, DB, 文件) | `async`/`await` |
| CPU 密集 (计算、加密、图像) | `asyncio.to_thread` 或 free-threading (3.14t) 多线程 |
| 真并行 CPU | 3.13 用 `multiprocessing`, 3.14 用 free-threading 多线程 |
| 单次脚本, 一两个 I/O | 同步代码 + `httpx.Client` 即可, 别强上 async |

整个调用链要么全 async 要么全 sync。混合调用 (`asyncio.run` 嵌套, `loop.run_until_complete` 在异步上下文里) 会死锁。

## 基本用法

```python
import asyncio
import httpx

async def fetch_user(client: httpx.AsyncClient, uid: int) -> dict:
    resp = await client.get(f"/users/{uid}")
    resp.raise_for_status()
    return resp.json()

async def main() -> None:
    async with httpx.AsyncClient(base_url="https://api.example.com") as client:
        user = await fetch_user(client, 1)
        print(user)

asyncio.run(main())  # 进程入口唯一一次
```

## 结构化并发 (TaskGroup, 3.11+)

并发首选 `TaskGroup`, 不用 `asyncio.gather` (除非确实需要 `return_exceptions=True`):

```python
async def fetch_all(uids: list[int]) -> list[dict]:
    async with httpx.AsyncClient() as client:
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(fetch_user(client, uid)) for uid in uids]
        return [t.result() for t in tasks]
```

TaskGroup 优势:
- 任一任务失败, 自动取消其他任务
- 多任务失败聚合成 `ExceptionGroup`, 用 `except*` 处理 (见 `python-error`)
- 退出 `async with` 前等所有任务完成, 防止任务泄漏

`gather` 仅在需要"全部跑完, 错误单独收集"时用:

```python
results = await asyncio.gather(*tasks, return_exceptions=True)
```

## 超时

`asyncio.timeout` (3.11+) 替代 `wait_for`:

```python
async with asyncio.timeout(5.0):
    data = await slow_operation()
# TimeoutError 在退出时抛出
```

不要用 `wait_for` (老 API, 取消语义有坑)。

## 取消

`CancelledError` 是控制流而非异常, 不要吞掉:

```python
async def worker():
    try:
        await do_work()
    except asyncio.CancelledError:
        await cleanup()
        raise   # 必须 re-raise
    except Exception:
        log.error("worker_failed", exc_info=True)
        raise
```

清理用 `try/finally` 或 `async with`, 不要依赖捕获 `CancelledError`。

## HTTP 客户端: httpx

不要再用 `requests` / `urllib`:

```python
# 复用 client (连接池, 性能 10x+)
async with httpx.AsyncClient(
    base_url="https://api.example.com",
    timeout=httpx.Timeout(10.0, connect=5.0),
    limits=httpx.Limits(max_connections=100),
) as client:
    resp = await client.get("/users", params={"page": 1})
```

每次请求都 `httpx.AsyncClient()` 是反模式 (无连接复用)。把 client 放在 app 生命周期 (FastAPI lifespan) 或 fixture 里。

## 文件 I/O: aiofiles

异步上下文里读写文件:

```python
import aiofiles

async with aiofiles.open("data.json") as f:
    content = await f.read()
```

但小文件直接 `Path.read_text()` (同步, 几 ms) 比开 aiofiles 还快, 别过度异步化。

## CPU 密集: to_thread / free-threading

CPU 密集任务**不要**写成 `async def`, 会阻塞事件循环:

```python
# 同步 CPU 函数
def compute_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

# 在 async 上下文里调
result = await asyncio.to_thread(compute_hash, big_data)
```

3.14 free-threading (`python3.14t`) 让多线程真并行, 多核 CPU 任务可用 `concurrent.futures.ThreadPoolExecutor`, 但生态 (C 扩展兼容) 还在补齐, 生产环境先评估。

## 并发限流

```python
sem = asyncio.Semaphore(10)  # 同时最多 10 并发

async def bounded_fetch(client, url):
    async with sem:
        return await client.get(url)

async with asyncio.TaskGroup() as tg:
    for url in urls:
        tg.create_task(bounded_fetch(client, url))
```

## 数据库: SQLAlchemy 2.0 异步

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import select

engine = create_async_engine("postgresql+asyncpg://...")

async def get_user(session: AsyncSession, uid: int) -> User | None:
    stmt = select(User).where(User.id == uid)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
```

不要在 async 代码里用同步 `psycopg2` / `sqlite3`。

## 调试

- `asyncio.run(main(), debug=True)` 启用 debug 模式, 检测慢回调和未 await 协程
- `PYTHONASYNCIODEBUG=1` 环境变量同效果
- `loop.set_slow_callback_duration(0.05)` 报警长回调

## 反模式

- `requests` / `urllib3` / `aiohttp` (新代码统一 httpx)
- `asyncio.get_event_loop()` (用 `asyncio.get_running_loop()` 或不用)
- 在 async 函数里 `time.sleep()` (用 `await asyncio.sleep()`)
- `asyncio.run(...)` 多次嵌套 (整个程序只一次)
- 协程未 await (会 `RuntimeWarning: coroutine 'x' was never awaited`)
- 在 async 里调阻塞 IO 不加 `to_thread`
- `for x in tasks: await x` (串行, 失去并发, 用 TaskGroup)
- 吞 `CancelledError`
