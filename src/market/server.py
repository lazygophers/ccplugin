"""Market Plugin MCP Server 实现."""

import logging
from typing import Any

from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    CallToolRequest,
    CallToolResult,
)

from .config import config
from .types import FeatureType

logger = logging.getLogger(__name__)


class MarketServer:
    """市场插件 MCP Server."""

    def __init__(self) -> None:
        """初始化 Market Server."""
        self.server = Server("market-server")
        self.setup_handlers()
        logger.info("Market Server 初始化完成")

    def setup_handlers(self) -> None:
        """注册 MCP server 处理器."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """列出可用工具."""
            tools: list[Tool] = []

            # 记忆管理工具
            if config.enable_memory:
                tools.extend([
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
                                    "description": "标签列表"
                                },
                                "metadata": {
                                    "type": "object",
                                    "description": "元数据"
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
                                    "description": "标签过滤"
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
                ])

            # 上下文管理工具
            if config.enable_context:
                tools.extend([
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
                                    "enum": ["user", "assistant", "system"],
                                    "description": "角色类型"
                                }
                            },
                            "required": ["session_id", "content", "role"]
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
                                    "description": "返回数量",
                                    "default": 20
                                }
                            },
                            "required": ["session_id"]
                        }
                    )
                ])

            # 任务管理工具
            if config.enable_task:
                tools.extend([
                    Tool(
                        name="task_create",
                        description="创建任务",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "任务标题"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "任务描述"
                                },
                                "priority": {
                                    "type": "integer",
                                    "description": "优先级 (0-4)",
                                    "minimum": 0,
                                    "maximum": 4,
                                    "default": 2
                                },
                                "tags": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "标签列表"
                                }
                            },
                            "required": ["title", "description"]
                        }
                    ),
                    Tool(
                        name="task_list",
                        description="列出任务",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "status": {
                                    "type": "string",
                                    "enum": ["open", "in_progress", "completed", "blocked"],
                                    "description": "任务状态过滤"
                                },
                                "tags": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "标签过滤"
                                }
                            }
                        }
                    )
                ])

            # 知识库管理工具
            if config.enable_knowledge:
                tools.extend([
                    Tool(
                        name="knowledge_add",
                        description="添加知识到向量数据库",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "content": {
                                    "type": "string",
                                    "description": "知识内容"
                                },
                                "source": {
                                    "type": "string",
                                    "description": "来源"
                                },
                                "metadata": {
                                    "type": "object",
                                    "description": "元数据"
                                }
                            },
                            "required": ["content", "source"]
                        }
                    ),
                    Tool(
                        name="knowledge_search",
                        description="语义搜索知识库",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "搜索查询"
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "返回数量",
                                    "default": 5
                                }
                            },
                            "required": ["query"]
                        }
                    )
                ])

            return tools

        @self.server.call_tool()
        async def call_tool(request: CallToolRequest) -> CallToolResult:
            """处理工具调用."""
            try:
                logger.info(f"调用工具: {request.params.name}")

                # 记忆管理
                if request.params.name == "memory_store":
                    return await self._handle_memory_store(request.params.arguments)
                elif request.params.name == "memory_search":
                    return await self._handle_memory_search(request.params.arguments)

                # 上下文管理
                elif request.params.name == "context_save":
                    return await self._handle_context_save(request.params.arguments)
                elif request.params.name == "context_retrieve":
                    return await self._handle_context_retrieve(request.params.arguments)

                # 任务管理
                elif request.params.name == "task_create":
                    return await self._handle_task_create(request.params.arguments)
                elif request.params.name == "task_list":
                    return await self._handle_task_list(request.params.arguments)

                # 知识库管理
                elif request.params.name == "knowledge_add":
                    return await self._handle_knowledge_add(request.params.arguments)
                elif request.params.name == "knowledge_search":
                    return await self._handle_knowledge_search(request.params.arguments)

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

    # 记忆管理处理器
    async def _handle_memory_store(self, args: dict[str, Any]) -> CallToolResult:
        """处理记忆存储."""
        content = args.get("content", "")
        tags = args.get("tags", [])
        metadata = args.get("metadata", {})

        result = f"已存储记忆: {content[:50]}... (标签: {', '.join(tags)})"
        logger.info(f"记忆存储: {result}")

        return CallToolResult(
            content=[TextContent(type="text", text=result)]
        )

    async def _handle_memory_search(self, args: dict[str, Any]) -> CallToolResult:
        """处理记忆搜索."""
        query = args.get("query", "")
        tags = args.get("tags", [])
        limit = args.get("limit", 10)

        result = f"搜索记忆: '{query}' (标签: {tags}, 限制: {limit})\n暂无结果（功能开发中）"
        logger.info(f"记忆搜索: {query}")

        return CallToolResult(
            content=[TextContent(type="text", text=result)]
        )

    # 上下文管理处理器
    async def _handle_context_save(self, args: dict[str, Any]) -> CallToolResult:
        """处理上下文保存."""
        session_id = args.get("session_id", "")
        content = args.get("content", "")
        role = args.get("role", "user")

        result = f"已保存上下文 [{role}]: {content[:50]}... (会话: {session_id})"
        logger.info(f"上下文保存: {session_id}")

        return CallToolResult(
            content=[TextContent(type="text", text=result)]
        )

    async def _handle_context_retrieve(self, args: dict[str, Any]) -> CallToolResult:
        """处理上下文检索."""
        session_id = args.get("session_id", "")
        limit = args.get("limit", 20)

        result = f"检索会话上下文: {session_id} (限制: {limit})\n暂无结果（功能开发中）"
        logger.info(f"上下文检索: {session_id}")

        return CallToolResult(
            content=[TextContent(type="text", text=result)]
        )

    # 任务管理处理器
    async def _handle_task_create(self, args: dict[str, Any]) -> CallToolResult:
        """处理任务创建."""
        title = args.get("title", "")
        description = args.get("description", "")
        priority = args.get("priority", 2)
        tags = args.get("tags", [])

        result = f"已创建任务: {title}\n描述: {description}\n优先级: {priority}\n标签: {', '.join(tags)}"
        logger.info(f"任务创建: {title}")

        return CallToolResult(
            content=[TextContent(type="text", text=result)]
        )

    async def _handle_task_list(self, args: dict[str, Any]) -> CallToolResult:
        """处理任务列表."""
        status = args.get("status")
        tags = args.get("tags", [])

        result = f"任务列表 (状态: {status}, 标签: {tags})\n暂无任务（功能开发中）"
        logger.info(f"任务列表查询")

        return CallToolResult(
            content=[TextContent(type="text", text=result)]
        )

    # 知识库管理处理器
    async def _handle_knowledge_add(self, args: dict[str, Any]) -> CallToolResult:
        """处理知识添加."""
        content = args.get("content", "")
        source = args.get("source", "")
        metadata = args.get("metadata", {})

        result = f"已添加知识: {content[:50]}...\n来源: {source}"
        logger.info(f"知识添加: {source}")

        return CallToolResult(
            content=[TextContent(type="text", text=result)]
        )

    async def _handle_knowledge_search(self, args: dict[str, Any]) -> CallToolResult:
        """处理知识搜索."""
        query = args.get("query", "")
        limit = args.get("limit", 5)

        result = f"知识库搜索: '{query}' (限制: {limit})\n暂无结果（功能开发中）"
        logger.info(f"知识搜索: {query}")

        return CallToolResult(
            content=[TextContent(type="text", text=result)]
        )


async def main() -> None:
    """运行 MCP server."""
    import asyncio
    from mcp.server.stdio import stdio_server

    server_instance = MarketServer()

    async with stdio_server() as (read_stream, write_stream):
        logger.info("Market MCP Server 启动")
        await server_instance.server.run(
            read_stream,
            write_stream,
            server_instance.server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    asyncio.run(main())
