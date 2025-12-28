"""Memory Plugin MCP Server 实现."""

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


class MemoryServer:
    """记忆管理 MCP Server."""

    def __init__(self) -> None:
        """初始化 Memory Server."""
        self.server = Server("memory-server")
        self.setup_handlers()
        logger.info("Memory Server 初始化完成")

    def setup_handlers(self) -> None:
        """注册 MCP server 处理器."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """列出可用工具."""
            return [
                Tool(
                    name="memory_store",
                    description="存储记忆项到知识图谱",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "记忆内容"
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "标签列表",
                                "default": []
                            },
                            "metadata": {
                                "type": "object",
                                "description": "元数据",
                                "default": {}
                            }
                        },
                        "required": ["content"]
                    }
                ),
                Tool(
                    name="memory_search",
                    description="搜索记忆项",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜索查询"
                            },
                            "tags": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "标签过滤",
                                "default": []
                            },
                            "limit": {
                                "type": "integer",
                                "description": "返回数量限制",
                                "default": 10
                            }
                        },
                        "required": ["query"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(request: CallToolRequest) -> CallToolResult:
            """处理工具调用."""
            try:
                if request.params.name == "memory_store":
                    return await self._handle_memory_store(request.params.arguments)
                elif request.params.name == "memory_search":
                    return await self._handle_memory_search(request.params.arguments)
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

    async def _handle_memory_store(self, args: dict[str, Any]) -> CallToolResult:
        """处理记忆存储.

        v0.1.0: 框架实现，返回确认消息
        v0.2.0: 将实现 NetworkX 知识图谱存储
        """
        content = args.get("content", "")
        tags = args.get("tags", [])
        metadata = args.get("metadata", {})

        result = f"已存储记忆: {content[:50]}{'...' if len(content) > 50 else ''} (标签: {', '.join(tags) if tags else '无'})"
        logger.info(f"记忆存储: {result}")

        return CallToolResult(
            content=[TextContent(type="text", text=result)]
        )

    async def _handle_memory_search(self, args: dict[str, Any]) -> CallToolResult:
        """处理记忆搜索.

        v0.1.0: 框架实现，返回提示消息
        v0.2.0: 将实现基于知识图谱的搜索
        """
        query = args.get("query", "")
        tags = args.get("tags", [])
        limit = args.get("limit", 10)

        result = f"搜索记忆: '{query}' (标签: {', '.join(tags) if tags else '无'}, 限制: {limit})\n\n" \
                 f"注意: v0.1.0 为框架实现，实际搜索功能将在 v0.2.0 中实现。"
        logger.info(f"记忆搜索: query={query}, tags={tags}, limit={limit}")

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
