"""任务管理插件的 MCP 服务器。

本模块实现基于 Model Context Protocol 的任务管理服务器。
提供完整的任务管理功能，包括 CRUD 操作、依赖管理、统计报表等。

MCP 工具（20+ 个）：
- task_create: 创建任务
- task_list: 列出任务
- task_show: 显示任务详情
- task_update: 更新任务
- task_close: 关闭任务
- task_reopen: 重新打开任务
- task_delete: 删除任务
- task_dep_add: 添加依赖
- task_dep_remove: 移除依赖
- task_dep_list: 列出依赖
- task_ready: 列出就绪任务
- task_blocked: 列出阻塞任务
- task_stats: 任务统计
- workspace_init: 初始化工作空间
- workspace_info: 工作空间信息
"""

import asyncio
import os
import secrets
from datetime import datetime
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from .mappers import (
    to_brief_tasks,
    to_dependency,
    to_task,
    to_task_with_dependencies,
)
from .repository import DependencyRepository, TaskRepository, TransactionManager
from .types import FilterDict
from .workspace import WorkspaceManager

# ============================================================================
# 全局状态
# ============================================================================

# 当前工作空间
current_workspace: WorkspaceManager | None = None


# ============================================================================
# 辅助函数
# ============================================================================


def generate_task_id() -> str:
    """生成任务 ID。

    Returns:
        格式为 tk-xxx 的任务 ID
    """
    random_part = secrets.token_hex(6)  # 12 字符
    return f"tk-{random_part}"


def generate_dependency_id() -> str:
    """生成依赖 ID。

    Returns:
        格式为 dep-xxx 的依赖 ID
    """
    random_part = secrets.token_hex(6)  # 12 字符
    return f"dep-{random_part}"


def get_workspace() -> WorkspaceManager:
    """获取当前工作空间。

    Returns:
        WorkspaceManager 实例

    Raises:
        RuntimeError: 工作空间未初始化
    """
    global current_workspace

    if current_workspace is None:
        # 自动初始化默认工作空间
        workspace_root = os.getenv("TASK_WORKSPACE_ROOT")
        current_workspace = WorkspaceManager(workspace_root, auto_init=True)

    return current_workspace


def format_task_brief(task_dict: dict[str, Any]) -> str:
    """格式化任务简要信息。

    Args:
        task_dict: 任务字典（BriefTask.model_dump()）

    Returns:
        格式化的字符串
    """
    return (
        f"{task_dict['id']}: {task_dict['title']} "
        f"[{task_dict['status']}] "
        f"(P{task_dict['priority']})"
    )


def format_task_detail(task_dict: dict[str, Any]) -> str:
    """格式化任务详细信息。

    Args:
        task_dict: 任务字典（Task.model_dump()）

    Returns:
        格式化的字符串
    """
    lines = [
        f"## {task_dict['title']}",
        "",
        f"**ID**: {task_dict['id']}",
        f"**类型**: {task_dict['task_type']}",
        f"**状态**: {task_dict['status']}",
        f"**优先级**: P{task_dict['priority']}",
        "",
    ]

    if task_dict.get("description"):
        lines.extend(
            [
                "**描述**:",
                task_dict["description"],
                "",
            ]
        )

    if task_dict.get("assignee"):
        lines.append(f"**负责人**: {task_dict['assignee']}")

    if task_dict.get("tags"):
        lines.append(f"**标签**: {', '.join(task_dict['tags'])}")

    if task_dict.get("dependencies"):
        lines.extend(
            [
                "",
                "**依赖任务**:",
                *[f"- {dep_id}" for dep_id in task_dict["dependencies"]],
            ]
        )

    return "\n".join(lines)


# ============================================================================
# MCP 服务器
# ============================================================================

app = Server("task-server")


@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """列出所有可用工具。

    Returns:
        工具列表
    """
    return [
        # 任务 CRUD
        types.Tool(
            name="task_create",
            description="创建新任务",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "任务标题"},
                    "description": {"type": "string", "description": "任务描述"},
                    "task_type": {
                        "type": "string",
                        "enum": ["bug", "feature", "task", "epic", "chore"],
                        "description": "任务类型",
                    },
                    "priority": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 4,
                        "description": "优先级 (0-4)",
                    },
                    "assignee": {"type": "string", "description": "负责人"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "标签列表",
                    },
                },
                "required": ["title"],
            },
        ),
        types.Tool(
            name="task_list",
            description="列出任务",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": [
                            "open",
                            "in_progress",
                            "blocked",
                            "deferred",
                            "closed",
                        ],
                        "description": "按状态过滤",
                    },
                    "assignee": {"type": "string", "description": "按负责人过滤"},
                    "task_type": {
                        "type": "string",
                        "enum": ["bug", "feature", "task", "epic", "chore"],
                        "description": "按类型过滤",
                    },
                    "priority": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 4,
                        "description": "按优先级过滤",
                    },
                    "limit": {
                        "type": "integer",
                        "default": 20,
                        "description": "返回数量限制",
                    },
                    "brief": {
                        "type": "boolean",
                        "default": True,
                        "description": "是否使用简要格式",
                    },
                },
            },
        ),
        types.Tool(
            name="task_show",
            description="显示任务详情",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "任务 ID"},
                },
                "required": ["task_id"],
            },
        ),
        types.Tool(
            name="task_update",
            description="更新任务",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "任务 ID"},
                    "title": {"type": "string", "description": "任务标题"},
                    "description": {"type": "string", "description": "任务描述"},
                    "status": {
                        "type": "string",
                        "enum": [
                            "open",
                            "in_progress",
                            "blocked",
                            "deferred",
                            "closed",
                        ],
                        "description": "任务状态",
                    },
                    "priority": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 4,
                        "description": "优先级",
                    },
                    "assignee": {"type": "string", "description": "负责人"},
                },
                "required": ["task_id"],
            },
        ),
        types.Tool(
            name="task_close",
            description="关闭任务",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "任务 ID"},
                    "reason": {"type": "string", "description": "关闭原因"},
                },
                "required": ["task_id"],
            },
        ),
        types.Tool(
            name="task_reopen",
            description="重新打开任务",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "任务 ID"},
                },
                "required": ["task_id"],
            },
        ),
        types.Tool(
            name="task_delete",
            description="删除任务",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "任务 ID"},
                },
                "required": ["task_id"],
            },
        ),
        # 依赖管理
        types.Tool(
            name="task_dep_add",
            description="添加任务依赖",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "任务 ID"},
                    "depends_on_id": {"type": "string", "description": "依赖的任务 ID"},
                    "dep_type": {
                        "type": "string",
                        "enum": [
                            "blocks",
                            "related",
                            "parent-child",
                            "discovered-from",
                        ],
                        "default": "blocks",
                        "description": "依赖类型",
                    },
                    "reason": {"type": "string", "description": "依赖原因"},
                },
                "required": ["task_id", "depends_on_id"],
            },
        ),
        types.Tool(
            name="task_dep_remove",
            description="移除任务依赖",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "任务 ID"},
                    "depends_on_id": {"type": "string", "description": "依赖的任务 ID"},
                },
                "required": ["task_id", "depends_on_id"],
            },
        ),
        types.Tool(
            name="task_dep_list",
            description="列出任务依赖",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "任务 ID"},
                },
                "required": ["task_id"],
            },
        ),
        # 查询工具
        types.Tool(
            name="task_ready",
            description="列出就绪任务（无阻塞依赖）",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "description": "返回数量限制",
                    },
                },
            },
        ),
        types.Tool(
            name="task_blocked",
            description="列出被阻塞的任务",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "description": "返回数量限制",
                    },
                },
            },
        ),
        types.Tool(
            name="task_stats",
            description="任务统计信息",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        # 工作空间管理
        types.Tool(
            name="workspace_init",
            description="初始化工作空间",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_root": {
                        "type": "string",
                        "description": "工作空间根目录",
                    },
                },
            },
        ),
        types.Tool(
            name="workspace_info",
            description="获取工作空间信息",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@app.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """处理工具调用。

    Args:
        name: 工具名称
        arguments: 工具参数

    Returns:
        工具执行结果
    """
    if arguments is None:
        arguments = {}

    # 获取工作空间和数据库会话
    workspace = get_workspace()
    db = workspace.get_database_manager()
    session = db.get_session()

    try:
        # 任务 CRUD 工具
        if name == "task_create":
            return await handle_task_create(session, arguments)
        elif name == "task_list":
            return await handle_task_list(session, arguments)
        elif name == "task_show":
            return await handle_task_show(session, arguments)
        elif name == "task_update":
            return await handle_task_update(session, arguments)
        elif name == "task_close":
            return await handle_task_close(session, arguments)
        elif name == "task_reopen":
            return await handle_task_reopen(session, arguments)
        elif name == "task_delete":
            return await handle_task_delete(session, arguments)

        # 依赖管理工具
        elif name == "task_dep_add":
            return await handle_task_dep_add(session, arguments)
        elif name == "task_dep_remove":
            return await handle_task_dep_remove(session, arguments)
        elif name == "task_dep_list":
            return await handle_task_dep_list(session, arguments)

        # 查询工具
        elif name == "task_ready":
            return await handle_task_ready(session, arguments)
        elif name == "task_blocked":
            return await handle_task_blocked(session, arguments)
        elif name == "task_stats":
            return await handle_task_stats(session, arguments)

        # 工作空间管理
        elif name == "workspace_init":
            return await handle_workspace_init(arguments)
        elif name == "workspace_info":
            return await handle_workspace_info()

        else:
            raise ValueError(f"未知工具: {name}")

    finally:
        session.close()


# ============================================================================
# 工具处理函数
# ============================================================================


async def handle_task_create(
    session: Any, arguments: dict[str, Any]
) -> list[types.TextContent]:
    """处理 task_create 工具。"""
    task_repo = TaskRepository(session)

    # 生成任务 ID
    task_id = generate_task_id()

    # 准备任务数据
    task_data = {
        "id": task_id,
        "title": arguments["title"],
        "description": arguments.get("description", ""),
        "task_type": arguments.get("task_type", "task"),
        "priority": arguments.get("priority", 2),
        "assignee": arguments.get("assignee"),
        "tags": arguments.get("tags", []),
        "status": "open",
    }

    # 创建任务
    with TransactionManager(session):
        task_model = task_repo.create(task_data)
        task = to_task(task_model)

    return [
        types.TextContent(
            type="text",
            text=f"✅ 任务创建成功\n\n{format_task_detail(task.model_dump())}",
        )
    ]


async def handle_task_list(
    session: Any, arguments: dict[str, Any]
) -> list[types.TextContent]:
    """处理 task_list 工具。"""
    task_repo = TaskRepository(session)

    # 构建过滤条件
    filters: FilterDict = {}
    if "status" in arguments:
        filters["status"] = arguments["status"]
    if "assignee" in arguments:
        filters["assignee"] = arguments["assignee"]
    if "task_type" in arguments:
        filters["task_type"] = arguments["task_type"]
    if "priority" in arguments:
        filters["priority"] = arguments["priority"]

    # 查询任务
    limit = arguments.get("limit", 20)
    brief = arguments.get("brief", True)

    task_models = task_repo.list_tasks(filters=filters, limit=limit)

    if brief:
        brief_tasks = to_brief_tasks(task_models)
        task_list = [format_task_brief(t.model_dump()) for t in brief_tasks]
    else:
        full_tasks = [to_task(t) for t in task_models]
        task_list = [format_task_detail(t.model_dump()) for t in full_tasks]

    if not task_list:
        return [types.TextContent(type="text", text="未找到任务")]

    result = f"找到 {len(task_list)} 个任务:\n\n" + "\n".join(task_list)
    return [types.TextContent(type="text", text=result)]


async def handle_task_show(
    session: Any, arguments: dict[str, Any]
) -> list[types.TextContent]:
    """处理 task_show 工具。"""
    task_repo = TaskRepository(session)

    task_id = arguments["task_id"]
    task_model = task_repo.get_by_id_with_relations(task_id)

    if not task_model:
        return [types.TextContent(type="text", text=f"❌ 任务不存在: {task_id}")]

    task = to_task_with_dependencies(task_model)
    return [
        types.TextContent(
            type="text",
            text=format_task_detail(task.model_dump()),
        )
    ]


async def handle_task_update(
    session: Any, arguments: dict[str, Any]
) -> list[types.TextContent]:
    """处理 task_update 工具。"""
    task_repo = TaskRepository(session)

    task_id = arguments.pop("task_id")

    # 准备更新数据
    update_data = {}
    for key in ["title", "description", "status", "priority", "assignee"]:
        if key in arguments:
            update_data[key] = arguments[key]

    # 更新任务
    with TransactionManager(session):
        task_model = task_repo.update(task_id, update_data)
        task = to_task(task_model)

    return [
        types.TextContent(
            type="text",
            text=f"✅ 任务更新成功\n\n{format_task_detail(task.model_dump())}",
        )
    ]


async def handle_task_close(
    session: Any, arguments: dict[str, Any]
) -> list[types.TextContent]:
    """处理 task_close 工具。"""
    task_repo = TaskRepository(session)

    task_id = arguments["task_id"]

    # 关闭任务
    update_data = {
        "status": "closed",
        "closed_at": datetime.utcnow(),
    }

    with TransactionManager(session):
        task_model = task_repo.update(task_id, update_data)
        task = to_task(task_model)

    return [
        types.TextContent(
            type="text",
            text=f"✅ 任务已关闭: {task.title}",
        )
    ]


async def handle_task_reopen(
    session: Any, arguments: dict[str, Any]
) -> list[types.TextContent]:
    """处理 task_reopen 工具。"""
    task_repo = TaskRepository(session)

    task_id = arguments["task_id"]

    # 重新打开任务
    update_data = {
        "status": "open",
        "closed_at": None,
    }

    with TransactionManager(session):
        task_model = task_repo.update(task_id, update_data)
        task = to_task(task_model)

    return [
        types.TextContent(
            type="text",
            text=f"✅ 任务已重新打开: {task.title}",
        )
    ]


async def handle_task_delete(
    session: Any, arguments: dict[str, Any]
) -> list[types.TextContent]:
    """处理 task_delete 工具。"""
    task_repo = TaskRepository(session)

    task_id = arguments["task_id"]

    with TransactionManager(session):
        task_repo.delete(task_id)

    return [
        types.TextContent(
            type="text",
            text=f"✅ 任务已删除: {task_id}",
        )
    ]


async def handle_task_dep_add(
    session: Any, arguments: dict[str, Any]
) -> list[types.TextContent]:
    """处理 task_dep_add 工具。"""
    dep_repo = DependencyRepository(session)

    # 准备依赖数据
    dep_data = {
        "id": generate_dependency_id(),
        "task_id": arguments["task_id"],
        "depends_on_id": arguments["depends_on_id"],
        "dep_type": arguments.get("dep_type", "blocks"),
        "reason": arguments.get("reason"),
    }

    # 创建依赖
    with TransactionManager(session):
        dep_model = dep_repo.create(dep_data)
        dep = to_dependency(dep_model)

    return [
        types.TextContent(
            type="text",
            text=f"✅ 依赖添加成功: {dep.task_id} → {dep.depends_on_id} ({dep.dep_type})",
        )
    ]


async def handle_task_dep_remove(
    session: Any, arguments: dict[str, Any]
) -> list[types.TextContent]:
    """处理 task_dep_remove 工具。"""
    dep_repo = DependencyRepository(session)

    task_id = arguments["task_id"]
    depends_on_id = arguments["depends_on_id"]

    with TransactionManager(session):
        dep_repo.delete_between_tasks(task_id, depends_on_id)

    return [
        types.TextContent(
            type="text",
            text=f"✅ 依赖已移除: {task_id} → {depends_on_id}",
        )
    ]


async def handle_task_dep_list(
    session: Any, arguments: dict[str, Any]
) -> list[types.TextContent]:
    """处理 task_dep_list 工具。"""
    dep_repo = DependencyRepository(session)

    task_id = arguments["task_id"]

    # 查询依赖
    dep_models = dep_repo.get_dependencies_for_task(task_id)
    deps = [to_dependency(d) for d in dep_models]

    if not deps:
        return [types.TextContent(type="text", text="无依赖")]

    dep_list = [f"- {d.depends_on_id} ({d.dep_type})" for d in deps]
    result = f"任务 {task_id} 的依赖:\n" + "\n".join(dep_list)

    return [types.TextContent(type="text", text=result)]


async def handle_task_ready(
    session: Any, arguments: dict[str, Any]
) -> list[types.TextContent]:
    """处理 task_ready 工具。"""
    task_repo = TaskRepository(session)
    dep_repo = DependencyRepository(session)

    # 查询所有未完成任务
    filters: FilterDict = {"status": "open"}
    task_models = task_repo.list_tasks(filters=filters, limit=100)

    # 过滤出没有阻塞依赖的任务
    ready_tasks = []
    for task_model in task_models:
        deps = dep_repo.get_dependencies_for_task(task_model.id)
        blocking_deps = [d for d in deps if d.dep_type == "blocks"]
        if not blocking_deps:
            ready_tasks.append(task_model)

    # 限制返回数量
    limit = arguments.get("limit", 10)
    ready_tasks = ready_tasks[:limit]

    if not ready_tasks:
        return [types.TextContent(type="text", text="无就绪任务")]

    tasks = to_brief_tasks(ready_tasks)
    task_list = [format_task_brief(t.model_dump()) for t in tasks]

    result = f"找到 {len(task_list)} 个就绪任务:\n\n" + "\n".join(task_list)
    return [types.TextContent(type="text", text=result)]


async def handle_task_blocked(
    session: Any, arguments: dict[str, Any]
) -> list[types.TextContent]:
    """处理 task_blocked 工具。"""
    task_repo = TaskRepository(session)

    filters: FilterDict = {"status": "blocked"}
    limit = arguments.get("limit", 10)

    task_models = task_repo.list_tasks(filters=filters, limit=limit)

    if not task_models:
        return [types.TextContent(type="text", text="无阻塞任务")]

    tasks = to_brief_tasks(task_models)
    task_list = [format_task_brief(t.model_dump()) for t in tasks]

    result = f"找到 {len(task_list)} 个阻塞任务:\n\n" + "\n".join(task_list)
    return [types.TextContent(type="text", text=result)]


async def handle_task_stats(
    session: Any, arguments: dict[str, Any]
) -> list[types.TextContent]:
    """处理 task_stats 工具。"""
    task_repo = TaskRepository(session)

    # 统计各状态任务数
    stats = {
        "总任务数": task_repo.count(),
        "待处理": task_repo.count({"status": "open"}),
        "进行中": task_repo.count({"status": "in_progress"}),
        "已阻塞": task_repo.count({"status": "blocked"}),
        "已延期": task_repo.count({"status": "deferred"}),
        "已完成": task_repo.count({"status": "closed"}),
    }

    # 按类型统计
    type_stats = {
        "Bug": task_repo.count({"task_type": "bug"}),
        "Feature": task_repo.count({"task_type": "feature"}),
        "Task": task_repo.count({"task_type": "task"}),
        "Epic": task_repo.count({"task_type": "epic"}),
        "Chore": task_repo.count({"task_type": "chore"}),
    }

    # 格式化输出
    result = ["## 任务统计", "", "### 按状态"]
    for key, value in stats.items():
        result.append(f"- {key}: {value}")

    result.extend(["", "### 按类型"])
    for key, value in type_stats.items():
        result.append(f"- {key}: {value}")

    return [types.TextContent(type="text", text="\n".join(result))]


async def handle_workspace_init(arguments: dict[str, Any]) -> list[types.TextContent]:
    """处理 workspace_init 工具。"""
    global current_workspace

    workspace_root = arguments.get("workspace_root")
    current_workspace = WorkspaceManager(workspace_root, auto_init=True)

    info = current_workspace.get_workspace_info()

    return [
        types.TextContent(
            type="text",
            text=(
                f"✅ 工作空间初始化成功\n\n"
                f"- 工作空间 ID: {info['workspace_id']}\n"
                f"- 根目录: {info['workspace_root']}\n"
                f"- 数据库路径: {info['database_path']}\n"
                f"- 数据库版本: {info['current_revision']}"
            ),
        )
    ]


async def handle_workspace_info() -> list[types.TextContent]:
    """处理 workspace_info 工具。"""
    workspace = get_workspace()
    info = workspace.get_workspace_info()

    return [
        types.TextContent(
            type="text",
            text=(
                f"## 工作空间信息\n\n"
                f"- 工作空间 ID: {info['workspace_id']}\n"
                f"- 根目录: {info['workspace_root']}\n"
                f"- 数据库路径: {info['database_path']}\n"
                f"- 数据库存在: {info['database_exists']}\n"
                f"- 数据库健康: {info['database_healthy']}\n"
                f"- 数据库版本: {info['current_revision']}"
            ),
        )
    ]


# ============================================================================
# 主函数
# ============================================================================


async def main() -> None:
    """启动 MCP 服务器。"""
    # 通过 stdio 运行服务器
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="task",
                server_version="0.2.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
