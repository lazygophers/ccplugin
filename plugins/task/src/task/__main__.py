"""任务管理插件主入口。

运行方式：
    python -m task
    uv run python -m task
"""

import asyncio

from .server import main

if __name__ == "__main__":
    asyncio.run(main())
