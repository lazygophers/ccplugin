#!/usr/bin/env python3
"""
Notification MCP Server - 系统通知 MCP 服务器
基于 Model Context Protocol 实现系统通知功能

⚠️ 必须使用 uv 执行此脚本：
  uv run mcp_server.py [options]

依赖：
  - mcp: MCP 协议实现
  - async: 异步 I/O 支持
  - pydantic: 数据验证
"""

import warnings
warnings.filterwarnings('ignore')

import asyncio
import sys
import logging
import platform
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
from logging.handlers import RotatingFileHandler

# 添加脚本路径到 sys.path 以导入 notifier.py 的模块
script_path = Path(__file__).parent
sys.path.insert(0, str(script_path))

try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    from pydantic import BaseModel, Field
except ImportError as e:
    print(f"MCP 依赖安装错误: {e}", file=sys.stderr)
    print("请安装 MCP 依赖: uv pip install mcp", file=sys.stderr)
    sys.exit(1)

# 配置日志（仅文件，不输出到控制台以遵守 MCP stdio 协议）
logger = logging.getLogger("notification-mcp-server")
logger.setLevel(logging.INFO)

# 禁用 basicConfig 以避免默认的 console handler
# 仅添加文件日志处理程序
log_dir = Path.home() / ".lazygophers" / "ccplugin"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "error.log"

# 使用 RotatingFileHandler：最大100MB，保留2份备份
file_handler = RotatingFileHandler(
    str(log_file),
    maxBytes=100 * 1024 * 1024,  # 100MB
    backupCount=2,  # 保留2份备份
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)  # 捕获 INFO 及以上级别的日志
file_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)
logger.addHandler(file_handler)

# 防止日志向上传播到 root logger（避免控制台输出）
logger.propagate = False


class NotificationRequest(BaseModel):
    """系统通知请求模型"""
    message: str = Field(..., description="Notification message")
    title: str = Field("Claude Code", description="Notification title")
    timeout: int = Field(5000, ge=1000, le=30000, description="Display timeout in milliseconds")


class NotificationMCPServer:
    """系统通知 MCP 服务器"""

    def __init__(self):
        self.server = Server("notification-system")
        self.notifier = None

        # 加载系统提示词
        self.agent_content = self._load_agent_content()

        # 注册 MCP 工具
        self._register_tools()

    def _load_agent_content(self) -> str:
        """加载系统提示词"""
        try:
            system_os = platform.system()
            return f"""
### Notification Plugin (系统通知插件)

**使用 notification 插件向用户发送系统通知**

当需要向用户显示重要信息或提示时，使用 notification 插件。其主要功能包括：

- **系统通知** - 跨平台发送系统级别的通知（macOS、Linux、Windows）
- **可配置显示时间** - 支持自定义通知显示时长（1000-30000 毫秒）
- **自定义标题** - 支持为通知添加标题，默认为 'Claude Code'
- **异步发送** - 通知发送不阻塞主线程

**支持的平台**:
- **macOS** - 使用 osascript 实现系统通知
- **Linux** - 使用 notify-send 实现系统通知（D-Bus）
- **Windows** - 使用 PowerShell Toast 通知

## 使用方式

```bash
# 发送简单通知（使用默认标题和显示时长）
/notify "任务已完成"

# 发送自定义标题的通知
/notify "任务已完成" --title "执行完成"

# 发送并指定显示时长
/notify "任务已完成" --title "执行完成" --timeout 8000
```

所有通知都会以平台原生的系统通知方式显示。

**当前系统**: {system_os}
"""
        except Exception as e:
            logger.error(f"加载系统提示词失败: {e}")
            return self._get_default_prompt()

    def _get_default_prompt(self) -> str:
        """获取默认系统提示词"""
        return """
### Notification Plugin

**使用 notification 插件发送系统通知**

主要功能：
- 跨平台系统通知（macOS、Linux、Windows）
- 可配置显示时长
- 自定义标题

使用 /notify 命令发送通知。
"""

    def _get_notifier(self):
        """延迟加载 Notifier 类"""
        if self.notifier is None:
            try:
                from notifier import Notifier
                self.notifier = Notifier()
                logger.info("Notifier 初始化成功")
            except Exception as e:
                logger.error(f"初始化 Notifier 失败: {e}")
        return self.notifier

    def _register_tools(self):
        """注册 MCP 工具"""

        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """返回可用工具列表"""
            return [
                Tool(
                    name="send",
                    description="Send a system notification to the user",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Notification message (required)"
                            },
                            "title": {
                                "type": "string",
                                "description": "Notification title (optional, default: 'Claude Code')"
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "Display timeout in milliseconds (optional, default: 5000, range: 1000-30000)"
                            }
                        },
                        "required": ["message"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """处理工具调用"""
            logger.info(f"调用工具: {name}, 参数: {arguments}")

            if name == "send":
                return await self._handle_send_notification(arguments)
            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

    async def _handle_send_notification(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """处理发送通知请求"""
        try:
            # 验证参数
            request = NotificationRequest(**arguments)

            # 获取 Notifier 实例
            notifier = self._get_notifier()
            if notifier is None:
                error_msg = "Failed to initialize notifier. Check system compatibility."
                logger.error(error_msg)
                return [TextContent(type="text", text=f"❌ {error_msg}")]

            # 发送通知
            logger.info(f"发送通知: title='{request.title}', message='{request.message}', timeout={request.timeout}ms")
            success = notifier.notify(request.title, request.message, request.timeout)

            if success:
                result = f"""✅ Notification sent successfully

**Title**: {request.title}
**Message**: {request.message}
**Timeout**: {request.timeout}ms
**Platform**: {platform.system()}"""
            else:
                result = f"""⚠️ Notification may not have been displayed

**Title**: {request.title}
**Message**: {request.message}
**Platform**: {platform.system()}

This might happen if:
- The system notification service is not available
- Desktop environment is not running (for Linux)
- Required tools are not installed"""

            logger.info(f"通知发送结果: {result}")
            return [TextContent(type="text", text=result)]

        except ValueError as e:
            error_msg = f"Invalid arguments: {str(e)}"
            logger.error(error_msg)
            return [TextContent(type="text", text=f"❌ {error_msg}")]
        except Exception as e:
            error_msg = f"Failed to send notification: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Exception details: {type(e).__name__}")
            return [TextContent(type="text", text=f"❌ {error_msg}")]

    async def run(self):
        """启动 MCP 服务器"""
        from mcp.server.stdio import stdio_server
        from mcp.server.models import InitializationOptions

        # 预加载 Notifier 以测试初始化
        self._get_notifier()

        # 运行服务器
        logger.info("Notification MCP Server 启动")
        async with stdio_server() as (read_stream, write_stream):
            initialization_options = self.server.create_initialization_options()
            await self.server.run(read_stream, write_stream, initialization_options)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="系统通知 MCP 服务器")
    parser.add_argument("--mcp", action="store_true", help="以 MCP 服务器模式运行")
    parser.add_argument("--debug", action="store_true", help="启用调试日志")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.mcp:
        # 运行 MCP 服务器
        server = NotificationMCPServer()
        asyncio.run(server.run())
    else:
        # 默认启动 MCP 服务器
        server = NotificationMCPServer()
        asyncio.run(server.run())


if __name__ == "__main__":
    main()
