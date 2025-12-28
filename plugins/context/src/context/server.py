"""Context Plugin MCP Server 实现."""

import logging
from typing import Any

from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    CallToolRequest,
    CallToolResult,
)

logger = logging.getLogger(__name__)


class ContextServer:
    """上下文管理 MCP Server."""

    def __init__(self) -> None:
        """初始化 Context Server."""
        self.server = Server("context-server")
        self.setup_handlers()
        logger.info("Context Server 初始化完成")

    def setup_handlers(self) -> None:
        """注册 MCP server 处理器."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """列出可用工具."""
            return [
                Tool(
                    name="context_save",
                    description="保存会话上下文",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "会话ID"
                            },
                            "content": {
                                "type": "string",
                                "description": "上下文内容"
                            },
                            "role": {
                                "type": "string",
                                "description": "角色 (user/assistant/system)",
                                "enum": ["user", "assistant", "system"],
                                "default": "user"
                            }
                        },
                        "required": ["session_id", "content"]
                    }
                ),
                Tool(
                    name="context_retrieve",
                    description="检索会话上下文",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "string",
                                "description": "会话ID"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "返回数量限制",
                                "default": 20
                            }
                        },
                        "required": ["session_id"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(request: CallToolRequest) -> CallToolResult:
            """处理工具调用."""
            try:
                if request.params.name == "context_save":
                    return await self._handle_context_save(request.params.arguments)
                elif request.params.name == "context_retrieve":
                    return await self._handle_context_retrieve(request.params.arguments)
                else:
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=f"未知工具: {request.params.name}"
                        )],
                        isError=True
                    )
            except Exception as e:
                logger.error(f"工具执行错误: {e}", exc_info=True)
                return CallToolResult(
                    content=[TextContent(type="text", text=f"错误: {str(e)}")],
                    isError=True
                )

    async def _handle_context_save(self, args: dict[str, Any]) -> CallToolResult:
        """处理上下文保存.

        v0.1.0: 框架实现，返回确认消息
        v0.3.0: 将实现 SQLAlchemy 持久化存储
        """
        session_id = args.get("session_id", "")
        content = args.get("content", "")
        role = args.get("role", "user")

        result = f"已保存上下文到会话 '{session_id}' (角色: {role}, 内容长度: {len(content)})"
        logger.info(f"上下文保存: {result}")

        return CallToolResult(
            content=[TextContent(type="text", text=result)]
        )

    async def _handle_context_retrieve(self, args: dict[str, Any]) -> CallToolResult:
        """处理上下文检索.

        v0.1.0: 框架实现，返回提示消息
        v0.3.0: 将实现从数据库检索历史上下文
        """
        session_id = args.get("session_id", "")
        limit = args.get("limit", 20)

        result = f"检索会话 '{session_id}' 的上下文 (限制: {limit}条)\n\n" \
                 f"注意: v0.1.0 为框架实现，实际检索功能将在 v0.3.0 中实现。"
        logger.info(f"上下文检索: session_id={session_id}, limit={limit}")

        return CallToolResult(
            content=[TextContent(type="text", text=result)]
        )

    async def run(self) -> None:
        """运行 MCP server."""
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )
