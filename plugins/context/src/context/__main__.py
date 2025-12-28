"""Context Plugin 入口点."""

import asyncio
import logging
import os

from .server import ContextServer

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def main() -> None:
    """启动 Context MCP Server."""
    server = ContextServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
