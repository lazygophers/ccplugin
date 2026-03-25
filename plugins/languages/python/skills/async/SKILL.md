---
description: Python 异步编程模式 - asyncio、trio、httpx、结构化并发。I/O 密集型操作的最佳实践。
user-invocable: true
context: fork
model: sonnet
memory: project
---

# Python 异步编程模式

## 适用 Agents

- **python:dev** - 开发阶段使用
- **python:debug** - 异步代码调试
- **python:test** - 异步测试编写

## 相关 Skills

- **Skills(python:core)** - 基础规范
- **Skills(python:types)** - 异步函数类型注解
- **Skills(python:error)** - 异步异常处理
- **Skills(python:web)** - FastAPI 异步集成

## 核心原则

### 1. 异步优先

**I/O 密集型操作默认使用 async/await**：

```python
# ✅ 正确：异步 I/O
import httpx

async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()

# ❌ 错误：同步 I/O（阻塞事件循环）
import requests

def fetch_data_sync(url: str) -> dict:
    response = requests.get(url)  # 阻塞！
    return response.json()
```

**适用场景**：
- ✅ HTTP 请求（httpx.AsyncClient）
- ✅ 数据库操作（AsyncSession）
- ✅ 文件 I/O（aiofiles）
- ✅ WebSocket 连接
- ❌ CPU 密集型任务（使用 multiprocessing）

## asyncio vs trio vs anyio

### 对比表（2024-2025）

| 特性 | asyncio | trio | anyio |
|------|---------|------|-------|
| 标准库 | ✅ | ❌ | ❌ |
| 结构化并发 | ❌ | ✅ | ✅ |
| 取消语义 | 复杂 | 清晰 | 清晰 |
| 错误传播 | 手动 | 自动 | 自动 |
| 学习曲线 | 陡峭 | 平缓 | 平缓 |
| 生态系统 | 最大 | 中等 | 中等 |

### 推荐策略

- **新项目**：优先考虑 trio（更安全的并发）
- **大型项目**：asyncio + anyio（兼容性）
- **Web 框架**：FastAPI（基于 asyncio）

## HTTP 请求：httpx 替代 requests

### 性能对比

```python
# ❌ requests（同步，维护模式）
import requests
response = requests.get("https://api.example.com")

# ✅ httpx（异步优先，活跃维护）
import httpx

# 同步（兼容 requests）
with httpx.Client() as client:
    response = client.get("https://api.example.com")

# 异步（推荐）
async with httpx.AsyncClient() as client:
    response = await client.get("https://api.example.com")
```

### httpx 优势

- ✅ 异步支持（原生）
- ✅ HTTP/2 支持
- ✅ 更好的类型注解
- ✅ 更好的测试工具（httpx.MockTransport）

### 完整示例

```python
import httpx
from typing import AsyncIterator

async def fetch_user(user_id: int) -> dict:
    """获取单个用户"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/users/{user_id}")
        response.raise_for_status()
        return response.json()

async def fetch_users(user_ids: list[int]) -> list[dict]:
    """并行获取多个用户"""
    async with httpx.AsyncClient() as client:
        tasks = [
            client.get(f"https://api.example.com/users/{uid}")
            for uid in user_ids
        ]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]

async def stream_large_file(url: str) -> AsyncIterator[bytes]:
    """流式下载大文件"""
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", url) as response:
            async for chunk in response.aiter_bytes():
                yield chunk
```

## 并发模式

### 1. asyncio.gather（基础并行）

```python
import asyncio

async def fetch_all(urls: list[str]) -> list[dict]:
    """并行执行多个任务"""
    tasks = [fetch_data(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 过滤错误
    valid_results = [r for r in results if not isinstance(r, Exception)]
    return valid_results
```

### 2. TaskGroup（Python 3.11+ 推荐）

```python
async def process_items(items: list[Item]) -> None:
    """使用 TaskGroup 管理任务"""
    async with asyncio.TaskGroup() as tg:
        for item in items:
            tg.create_task(process_item(item))

    # 离开上下文时，所有任务已完成或取消
    print("所有任务已完成")
```

### 3. trio 结构化并发（最安全）

```python
import trio

async def fetch_user(user_id: int) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"/users/{user_id}")
        return response.json()

async def main():
    """结构化并发：所有子任务在 nursery 作用域内"""
    async with trio.open_nursery() as nursery:
        nursery.start_soon(fetch_user, 1)
        nursery.start_soon(fetch_user, 2)
        nursery.start_soon(fetch_user, 3)

    # 离开 nursery 时，保证所有任务已完成或取消
    print("所有任务已完成")
```

**trio 优势**：
- ✅ 自动取消管理（父任务取消，子任务自动取消）
- ✅ 异常自动传播
- ✅ 避免任务泄漏

### 4. 并发限制（Semaphore）

```python
import asyncio

async def fetch_with_limit(urls: list[str], max_concurrent: int = 5) -> list[dict]:
    """限制并发数量"""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def fetch_one(url: str) -> dict:
        async with semaphore:
            return await fetch_data(url)

    tasks = [fetch_one(url) for url in urls]
    return await asyncio.gather(*tasks)
```

## 数据库异步操作

### SQLAlchemy 2.0 Async

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# 创建异步引擎
engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_user(user_id: int) -> User | None:
    """异步查询用户"""
    async with async_session() as session:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

async def create_user(username: str, email: str) -> User:
    """异步创建用户"""
    async with async_session() as session:
        user = User(username=username, email=email)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
```

## 文件 I/O

### aiofiles

```python
import aiofiles

async def read_file(path: str) -> str:
    """异步读取文件"""
    async with aiofiles.open(path, 'r') as f:
        content = await f.read()
    return content

async def write_file(path: str, content: str) -> None:
    """异步写入文件"""
    async with aiofiles.open(path, 'w') as f:
        await f.write(content)

async def process_large_file(input_path: str, output_path: str) -> None:
    """流式处理大文件"""
    async with aiofiles.open(input_path, 'r') as infile:
        async with aiofiles.open(output_path, 'w') as outfile:
            async for line in infile:
                processed = line.upper()
                await outfile.write(processed)
```

## 避免阻塞事件循环

### 识别阻塞操作

```python
# ❌ 阻塞操作（禁止在 async 函数中）
import time

async def bad_sleep():
    time.sleep(1)  # 阻塞事件循环！

# ✅ 正确：使用异步睡眠
async def good_sleep():
    await asyncio.sleep(1)  # 不阻塞事件循环

# ❌ 阻塞文件 I/O
async def bad_file_read():
    with open("file.txt") as f:  # 阻塞！
        content = f.read()

# ✅ 正确：异步文件 I/O
async def good_file_read():
    async with aiofiles.open("file.txt") as f:
        content = await f.read()
```

### 处理阻塞代码

```python
import asyncio

# 方式 1：asyncio.to_thread（Python 3.9+）
async def run_blocking():
    result = await asyncio.to_thread(blocking_function, arg1, arg2)
    return result

# 方式 2：loop.run_in_executor
async def run_blocking_executor():
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, blocking_function, arg1, arg2)
    return result
```

## 异步测试

### pytest-asyncio

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_fetch_user():
    """测试异步函数"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/users/1")
        assert response.status_code == 200
        assert response.json()["username"] == "alice"

@pytest.fixture
async def async_client():
    """异步 fixture"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_create_user(async_client):
    """使用异步 fixture"""
    response = await async_client.post("/users", json={
        "username": "testuser",
        "email": "test@example.com"
    })
    assert response.status_code == 201
```

## Red Flags：AI 常见误区

| AI 可能的理性化解释 | 实际应该检查的内容 |
|---------------------|-------------------|
| "同步代码更简单易读" | ✅ I/O 操作是否使用了 async/await？ |
| "requests 库很成熟" | ✅ 是否使用了 httpx.AsyncClient？ |
| "aiohttp 够用了" | ✅ 是否迁移到 httpx（更好的类型支持）？ |
| "asyncio.gather 足够" | ✅ 是否使用了 TaskGroup（Python 3.11+）？ |
| "不需要结构化并发" | ✅ 是否考虑使用 trio 避免任务泄漏？ |
| "time.sleep() 在 async 函数中可以用" | ✅ 是否使用了 asyncio.sleep()？ |
| "同步数据库查询足够快" | ✅ 是否使用了 AsyncSession？ |

## 性能优化

### 1. 连接池管理

```python
import httpx

# ✅ 正确：复用客户端
client = httpx.AsyncClient()

async def fetch_data(url: str) -> dict:
    response = await client.get(url)
    return response.json()

# 应用关闭时清理
await client.aclose()

# ❌ 错误：每次创建新客户端
async def fetch_data_bad(url: str) -> dict:
    async with httpx.AsyncClient() as client:  # 每次创建连接！
        response = await client.get(url)
        return response.json()
```

### 2. 超时控制

```python
import httpx

async def fetch_with_timeout(url: str) -> dict:
    """设置超时"""
    timeout = httpx.Timeout(10.0, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url)
        return response.json()
```

## 检查清单

### 基础要求
- [ ] I/O 操作使用 async/await
- [ ] HTTP 请求使用 httpx.AsyncClient
- [ ] 数据库使用 AsyncSession
- [ ] 文件操作使用 aiofiles

### 并发管理
- [ ] 使用 TaskGroup（Python 3.11+）或 trio
- [ ] 使用 Semaphore 限制并发数
- [ ] 正确处理异常（gather 使用 return_exceptions=True）

### 避免阻塞
- [ ] 没有 time.sleep() 调用
- [ ] 没有同步文件 I/O
- [ ] 没有 requests.get() 调用
- [ ] 阻塞代码使用 asyncio.to_thread()

### 测试
- [ ] 使用 pytest-asyncio
- [ ] 异步 fixture 定义正确
- [ ] @pytest.mark.asyncio 标记所有异步测试
