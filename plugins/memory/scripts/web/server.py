"""
Web 服务器模块

提供 Web 服务器启动和管理功能。
"""

import asyncio
import random
import socket
import webbrowser
from typing import Optional

from lib import logging


def find_available_port() -> int:
    """
    查找可用端口
    
    随机选择一个可用端口（范围：8000-9000）。
        
    Returns:
        int: 可用端口号
        
    Raises:
        RuntimeError: 无法找到可用端口时抛出
    """
    start_port = random.randint(8000, 8900)
    for offset in range(100):
        port = start_port + offset
        if port > 9000:
            port = 8000 + (port - 9001)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    raise RuntimeError("无法找到可用端口 (尝试范围: 8000-9000)")


async def run_web_server(port: Optional[int] = None, open_browser: bool = True, reload: bool = False) -> None:
    """
    启动 Web 服务器
    
    Args:
        port: 端口号，如不指定则自动查找可用端口
        open_browser: 是否自动打开浏览器
        reload: 是否启用热重载
    """
    import uvicorn
    
    from .api import create_app
    
    if port is None:
        port = find_available_port()
    
    url = f"http://127.0.0.1:{port}"
    logging.info(f"Web 服务器启动: {url}")
    
    if reload:
        logging.info("热重载已启用 - 文件变更将自动重启服务器")
    
    if open_browser:
        webbrowser.open(url)
    
    if reload:
        config = uvicorn.Config(
            "web.api:create_app",
            host="127.0.0.1",
            port=port,
            log_level="warning",
            reload=True,
            factory=True,
        )
    else:
        app = create_app()
        config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    
    server = uvicorn.Server(config)
    await server.serve()


def start_web(port: Optional[int] = None, open_browser: bool = True, reload: bool = False) -> None:
    """
    启动 Web 服务器（同步入口）
    
    Args:
        port: 端口号，如不指定则自动查找可用端口
        open_browser: 是否自动打开浏览器
        reload: 是否启用热重载
    """
    asyncio.run(run_web_server(port=port, open_browser=open_browser, reload=reload))
