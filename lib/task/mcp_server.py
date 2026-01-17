#!/usr/bin/env python3
"""
Task MCP Server - 任务管理 MCP 服务器
基于 Model Context Protocol 实现任务管理功能

⚠️ 必须使用 uv 执行此脚本：
  uv run mcp_server.py [options]

依赖：
  - mcp: MCP 协议实现
  - async: 异步 I/O 支持
  - pydantic: 数据验证
  - uvloop: 高性能事件循环（可选）
"""

import warnings
warnings.filterwarnings('ignore')

import asyncio
import sys
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from logging.handlers import RotatingFileHandler

# 从 lib.task.core 导入 task 模块的函数
# 注意：这个文件现在在 lib/task/ 中，core.py 也在同一目录
# 已经可以通过 from .core import ... 导入

try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    from pydantic import BaseModel, Field
except ImportError as e:
    print(f"MCP 依赖安装错误: {e}", file=sys.stderr)
    print("请安装 MCP 依赖: uv pip install mcp", file=sys.stderr)
    sys.exit(1)

# 配置日志（仅文件，不输出到控制台以遵守 MCP stdio 协议）
logger = logging.getLogger("task-mcp-server")
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

class TaskRequest(BaseModel):
    """基础任务请求模型"""
    title: str = Field(..., description="Task title")

class AddTaskRequest(TaskRequest):
    """添加任务请求模型"""
    description: Optional[str] = Field(None, description="Task description")
    task_type: str = Field("feature", description="Task type (feature/bug/refactor/test/docs/config)")
    status: str = Field("pending", description="Task status")
    acceptance_criteria: Optional[str] = Field(None, description="Acceptance criteria")
    dependencies: Optional[str] = Field(None, description="依赖任务ID（逗号分隔）")
    parent: Optional[str] = Field(None, description="父任务ID")

class UpdateTaskRequest(BaseModel):
    """更新任务请求模型"""
    task_id: str = Field(..., description="Task ID")
    title: Optional[str] = Field(None, description="Updated task title")
    description: Optional[str] = Field(None, description="Updated task description")
    status: Optional[str] = Field(None, description="Updated task status")
    acceptance_criteria: Optional[str] = Field(None, description="Updated acceptance criteria")

class ListTasksRequest(BaseModel):
    """列出任务请求模型"""
    status: Optional[str] = Field(None, description="Filter by status")
    task_type: Optional[str] = Field(None, description="Filter by task type")
    limit: int = Field(50, ge=1, le=100, description="Maximum number of tasks to return")

class TaskMCPServer:
    """任务管理 MCP 服务器"""

    def __init__(self):
        self.server = Server("task-manager")
        self.task_db = None

        # 读取系统提示词
        self.agent_content = self._load_agent_content()

        # 注册 MCP 工具
        self._register_tools()

    def _load_agent_content(self) -> str:
        """加载系统提示词（从 agent_prompt.py 导入内置字符串）"""
        try:
            from agent_prompt import get_task_agent_prompt
            logger.info("成功加载系统提示词（从 agent_prompt.py）")
            return get_task_agent_prompt()
        except Exception as e:
            logger.error(f"加载系统提示词失败: {e}")
            return self._get_default_prompt()

    def _get_default_prompt(self) -> str:
        """获取默认系统提示词"""
        return """
### Task Management Plugin

**使用 task 插件进行项目任务管理**

当需要管理项目任务时，使用 task 插件。其主要功能包括：

- **任务管理** - 创建、更新、删除、查看任务
- **状态跟踪** - 支持 pending/in_progress/completed/blocked/cancelled 状态
- **任务分类** - 支持 feature/bug/refactor/test/docs/config 类型
- **依赖管理** - 支持任务依赖和父子关系
- **SQLite 存储** - 本地数据库存储，支持增量备份

## 使用方式

```bash
# 添加任务
/task-add "实现用户认证" --description "添加JWT认证功能" --type feature

# 更新任务
/task-update "abc123" --status in_progress

# 列出任务
/task-list --status pending --limit 10

# 删除任务
/task-delete "abc123"
```

所有任务自动保存到本地 SQLite 数据库。
"""

    def _ensure_task_db_initialized(self):
        """确保任务数据库已初始化"""
        if self.task_db is None:
            try:
                # 导入任务管理模块（延迟初始化）
                from .core import init_database, get_db_path, add_task, update_task, delete_task, list_tasks, get_task

                # 自动检查并初始化
                db_path = get_db_path()
                init_database(db_path)

                # 存储任务管理函数引用
                self.task_db = {
                    'add_task': add_task,
                    'update_task': update_task,
                    'delete_task': delete_task,
                    'list_tasks': list_tasks,
                    'get_task': get_task
                }

                logger.info("任务数据库初始化成功")
                return True

            except Exception as e:
                logger.error(f"初始化任务数据库失败: {e}")
                return False
        return True

    def _register_tools(self):
        """注册 MCP 工具"""

        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """返回可用工具列表"""
            return [
                Tool(
                    name="add",
                    description="Add a new task to the project",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Task title (required)"
                            },
                            "description": {
                                "type": "string",
                                "description": "Task description (optional)"
                            },
                            "task_type": {
                                "type": "string",
                                "description": "Task type",
                                "enum": ["feature", "bug", "refactor", "test", "docs", "config"],
                                "default": "feature"
                            },
                            "status": {
                                "type": "string",
                                "description": "Task status",
                                "enum": ["pending", "in_progress", "completed", "blocked", "cancelled"],
                                "default": "pending"
                            },
                            "acceptance_criteria": {
                                "type": "string",
                                "description": "Acceptance criteria for the task (optional)"
                            },
                            "dependencies": {
                                "type": "string",
                                "description": "Comma-separated list of task IDs this task depends on (optional)"
                            },
                            "parent": {
                                "type": "string",
                                "description": "Parent task ID for creating subtasks (optional)"
                            }
                        },
                        "required": ["title"]
                    }
                ),
                Tool(
                    name="up",
                    description="Update existing task information",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "Task ID to update (required)"
                            },
                            "title": {
                                "type": "string",
                                "description": "Updated task title (optional)"
                            },
                            "description": {
                                "type": "string",
                                "description": "Updated task description (optional)"
                            },
                            "status": {
                                "type": "string",
                                "description": "Updated task status",
                                "enum": ["pending", "in_progress", "completed", "blocked", "cancelled"]
                            },
                            "acceptance_criteria": {
                                "type": "string",
                                "description": "Updated acceptance criteria (optional)"
                            }
                        },
                        "required": ["task_id"]
                    }
                ),
                Tool(
                    name="del",
                    description="Delete a task by its ID. Note: This action cannot be undone.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "Task ID to delete (required)"
                            }
                        },
                        "required": ["task_id"]
                    }
                ),
                Tool(
                    name="list",
                    description="List tasks with optional filtering by status or type",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "description": "Filter by task status (optional)",
                                "enum": ["pending", "in_progress", "completed", "blocked", "cancelled"]
                            },
                            "task_type": {
                                "type": "string",
                                "description": "Filter by task type (optional)",
                                "enum": ["feature", "bug", "refactor", "test", "docs", "config"]
                            },
                            "limit": {
                                "type": "number",
                                "description": "Maximum number of tasks to return (default 50, range 1-100)",
                                "minimum": 1,
                                "maximum": 100,
                                "default": 50
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="get",
                    description="Get detailed information about a specific task by its ID.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "task_id": {
                                "type": "string",
                                "description": "Task ID to retrieve (required)"
                            }
                        },
                        "required": ["task_id"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """处理工具调用"""
            if name == "add":
                return await self._handle_add_task(arguments)
            elif name == "up":
                return await self._handle_update_task(arguments)
            elif name == "del":
                return await self._handle_delete_task(arguments)
            elif name == "list":
                return await self._handle_list_tasks(arguments)
            elif name == "get":
                return await self._handle_get_task(arguments)
            else:
                return [TextContent(
                    type="text",
                    text=f"Error: Unknown tool '{name}'"
                )]

    async def _handle_add_task(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """处理添加任务请求"""
        try:
            request = AddTaskRequest(**arguments)
            logger.info(f"收到添加任务请求: title='{request.title}'")

            # 确保数据库已初始化
            if not self._ensure_task_db_initialized():
                return [TextContent(
                    type="text",
                    text="Error: Task database not initialized. Please check plugin configuration and restart Claude Code."
                )]

            # 添加任务
            task_id = self.task_db['add_task'](
                title=request.title,
                description=request.description or "",
                task_type=request.task_type,
                status=request.status,
                acceptance_criteria=request.acceptance_criteria or "",
                dependencies=request.dependencies or "",
                parent=request.parent
            )

            return [TextContent(
                type="text",
                text=f"Task added successfully with ID: {task_id}"
            )]

        except Exception as e:
            logger.error(f"添加任务错误: {e}")
            return [TextContent(
                type="text",
                text=f"Failed to add task: {str(e)}"
            )]

    async def _handle_update_task(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """处理更新任务请求"""
        try:
            request = UpdateTaskRequest(**arguments)
            logger.info(f"收到更新任务请求: task_id='{request.task_id}'")

            # 确保数据库已初始化
            if not self._ensure_task_db_initialized():
                return [TextContent(
                    type="text",
                    text="Error: Task database not initialized. Please check plugin configuration and restart Claude Code."
                )]

            # 更新任务
            success = self.task_db['update_task'](
                task_id=request.task_id,
                title=request.title,
                description=request.description,
                status=request.status,
                acceptance_criteria=request.acceptance_criteria
            )

            if success:
                return [TextContent(
                    type="text",
                    text=f"Task {request.task_id} updated successfully"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Failed to update task {request.task_id}: Task not found"
                )]

        except Exception as e:
            logger.error(f"更新任务错误: {e}")
            return [TextContent(
                type="text",
                text=f"Failed to update task: {str(e)}"
            )]

    async def _handle_delete_task(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """处理删除任务请求"""
        try:
            task_id = arguments.get('task_id')
            if not task_id:
                return [TextContent(
                    type="text",
                    text="Error: task_id is required"
                )]

            logger.info(f"收到删除任务请求: task_id='{task_id}'")

            # 确保数据库已初始化
            if not self._ensure_task_db_initialized():
                return [TextContent(
                    type="text",
                    text="Error: Task database not initialized. Please check plugin configuration and restart Claude Code."
                )]

            # 删除任务
            success = self.task_db['delete_task'](task_id)

            if success:
                return [TextContent(
                    type="text",
                    text=f"Task {task_id} deleted successfully"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Failed to delete task {task_id}: Task not found"
                )]

        except Exception as e:
            logger.error(f"删除任务错误: {e}")
            return [TextContent(
                type="text",
                text=f"Failed to delete task: {str(e)}"
            )]

    async def _handle_list_tasks(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """处理列出任务请求"""
        try:
            request = ListTasksRequest(**arguments)
            logger.info(f"收到列出任务请求: status={request.status}, type={request.task_type}, limit={request.limit}")

            # 确保数据库已初始化
            if not self._ensure_task_db_initialized():
                return [TextContent(
                    type="text",
                    text="Error: Task database not initialized. Please check plugin configuration and restart Claude Code."
                )]

            # 列出任务
            tasks = self.task_db['list_tasks'](
                status=request.status,
                task_type=request.task_type,
                limit=request.limit
            )

            return self._format_task_list(tasks)

        except Exception as e:
            logger.error(f"列出任务错误: {e}")
            return [TextContent(
                type="text",
                text=f"Failed to list tasks: {str(e)}"
            )]

    async def _handle_get_task(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """处理获取任务详情请求"""
        try:
            task_id = arguments.get('task_id')
            if not task_id:
                return [TextContent(
                    type="text",
                    text="Error: task_id is required"
                )]

            logger.info(f"收到获取任务请求: task_id='{task_id}'")

            # 确保数据库已初始化
            if not self._ensure_task_db_initialized():
                return [TextContent(
                    type="text",
                    text="Error: Task database not initialized. Please check plugin configuration and restart Claude Code."
                )]

            # 获取任务
            task = self.task_db['get_task'](task_id)

            if task:
                return self._format_task_detail(task)
            else:
                return [TextContent(
                    type="text",
                    text=f"Task {task_id} not found"
                )]

        except Exception as e:
            logger.error(f"获取任务错误: {e}")
            return [TextContent(
                type="text",
                text=f"Failed to get task: {str(e)}"
            )]

    def _format_task_list(self, tasks: List[Dict]) -> List[TextContent]:
        """格式化任务列表"""
        if not tasks:
            return [TextContent(
                type="text",
                text="No tasks found"
            )]

        # 构建结果文本
        output_lines = [
            f"Found {len(tasks)} tasks",
            "",
        ]

        for task in tasks:
            status_emoji = {"pending": "⏳", "in_progress": "🔄", "completed": "✅", "blocked": "🚫", "cancelled": "❌"}
            type_emoji = {"feature": "✨", "bug": "🐛", "refactor": "♻️", "test": "🧪", "docs": "📝", "config": "⚙️"}

            status_icon = status_emoji.get(task['status'], "📋")
            type_icon = type_emoji.get(task['type'], "📋")

            output_lines.extend([
                f"{status_icon} {type_icon} **{task['title']}** (#{task['id']})",
                f"  Status: {task['status']} | Type: {task['type']}",
                f"  Created: {task['created_at']}",
                ""
            ])

        return [TextContent(type="text", text="\n".join(output_lines))]

    def _format_task_detail(self, task: Dict) -> List[TextContent]:
        """格式化任务详情"""
        status_emoji = {"pending": "⏳", "in_progress": "🔄", "completed": "✅", "blocked": "🚫", "cancelled": "❌"}
        type_emoji = {"feature": "✨", "bug": "🐛", "refactor": "♻️", "test": "🧪", "docs": "📝", "config": "⚙️"}

        status_icon = status_emoji.get(task['status'], "📋")
        type_icon = type_emoji.get(task['type'], "📋")

        output_lines = [
            f"{status_icon} {type_icon} **{task['title']}** (#{task['id']})",
            "",
            f"**Status**: {task['status']}",
            f"**Type**: {task['type']}",
            f"**Created**: {task['created_at']}",
        ]

        if task['description']:
            output_lines.extend(["", "**Description**:", task['description']])

        if task['acceptance_criteria']:
            output_lines.extend(["", "**Acceptance Criteria**:", task['acceptance_criteria']])

        if task['dependencies']:
            output_lines.extend(["", f"**Dependencies**: {task['dependencies']}"])

        if task['parent']:
            output_lines.extend(["", f"**Parent Task**: #{task['parent']}"])

        if task['completed_at']:
            output_lines.extend(["", f"**Completed**: {task['completed_at']}"])

        return [TextContent(type="text", text="\n".join(output_lines))]

    async def run(self):
        """启动 MCP 服务器"""
        from mcp.server.stdio import stdio_server
        from mcp.server.models import InitializationOptions

        # 准备统计信息（用于初始化检查）
        self._ensure_task_db_initialized()

        # 运行服务器
        logger.info("Task MCP Server 启动")
        async with stdio_server() as (read_stream, write_stream):
            initialization_options = self.server.create_initialization_options()
            await self.server.run(read_stream, write_stream, initialization_options)

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="任务管理 MCP 服务器")
    parser.add_argument("--mcp", action="store_true", help="以 MCP 服务器模式运行")
    parser.add_argument("--debug", action="store_true", help="启用调试日志")
    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.INFO)

    if args.mcp:
        # 运行 MCP 服务器
        server = TaskMCPServer()
        asyncio.run(server.run())
    else:
        # 默认启动 MCP 服务器
        server = TaskMCPServer()
        asyncio.run(server.run())

if __name__ == "__main__":
    main()