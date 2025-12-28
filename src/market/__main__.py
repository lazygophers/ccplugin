"""Market Plugin MCP Server 入口点."""

import asyncio
import logging

from .server import main
from .config import config

if __name__ == "__main__":
    # 配置验证
    config.validate()

    # 日志配置
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 启动服务器
    asyncio.run(main())
