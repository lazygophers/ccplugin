---
name: async
description: Python 异步编程规范：asyncio、并发模式、异步测试。写异步代码时必须加载。
---

# Python 异步编程规范

## 相关 Skills

| 场景 | Skill | 说明 |
|------|-------|------|
| 核心规范 | Skills(core) | PEP 8、命名规范 |

## asyncio 基本用法

```python
import asyncio

async def fetch_data(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

async def main():
    result = await fetch_data("https://api.example.com")
    print(result)

asyncio.run(main())
```

## 并发模式

```python
# 并行执行
async def fetch_all(urls: list[str]) -> list[dict]:
    tasks = [fetch_data(url) for url in urls]
    return await asyncio.gather(*tasks)

# TaskGroup (Python 3.11+)
async def process_items(items: list[Item]):
    async with asyncio.TaskGroup() as tg:
        for item in items:
            tg.create_task(process_item(item))
```

## 避免阻塞

```python
# ✅ 使用异步库
async with aiofiles.open("file.txt") as f:
    content = await f.read()

# ❌ 避免阻塞调用
with open("file.txt") as f:  # 阻塞！
    content = f.read()

# ✅ 在线程池中运行阻塞代码
content = await asyncio.to_thread(read_file, "file.txt")
```

## 检查清单

- [ ] 使用 async/await
- [ ] 避免阻塞事件循环
- [ ] 使用 asyncio.gather 并行
- [ ] 使用 asyncio.to_thread 处理阻塞
