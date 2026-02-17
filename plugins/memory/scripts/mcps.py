"""
MCP Server for Memory Plugin

提供 MCP 协议接口，让 AI Agent 能直接操作记忆系统。

工具列表:
- read_memory: 读取记忆
- create_memory: 创建记忆
- update_memory: 更新记忆
- delete_memory: 删除记忆
- search_memory: 搜索记忆
- preload_memory: 预加载记忆
- save_session: 保存会话
- list_memories: 列出记忆
- get_memory_stats: 获取统计
- export_memories: 导出记忆
- import_memories: 导入记忆
- add_alias: 添加别名
- get_memory_versions: 获取版本历史
- rollback_memory: 回滚记忆
- diff_versions: 对比版本
- list_rollbacks: 列出可回滚版本
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional


class DateTimeEncoder(json.JSONEncoder):
    """自定义 JSON 编码器，处理 datetime 对象。"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def json_dumps(obj: Any) -> str:
    """使用自定义编码器序列化 JSON。"""
    return json.dumps(obj, cls=DateTimeEncoder, ensure_ascii=False, indent=2)

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from memory import (
    init_db,
    close_db,
    create_memory,
    get_memory,
    update_memory,
    delete_memory,
    search_memories,
    list_memories,
    get_memories_by_priority,
    get_versions,
    get_version,
    get_relations,
    get_stats,
    export_memories,
    import_memories,
    handle_system_uri,
    is_system_uri,
    create_session,
    end_session,
    add_memory_path,
    find_memories_by_path,
)
from memory.version import rollback_to_version, diff_versions


class MemoryMCPServer:
    """MCP Server for Memory operations."""
    
    def __init__(self):
        self.server = Server("memory-plugin")
        self._db_initialized = False
        self._register_handlers()
    
    def _register_handlers(self):
        """Register MCP request handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="read_memory",
                    description="""读取指定 URI 的记忆内容。

特殊 URI:
- system://boot - 加载核心记忆（priority ≤ 2）
- system://index - 显示全量记忆索引
- system://recent - 显示最近修改的记忆
- system://recent/N - 显示最近 N 条修改

返回记忆内容和元数据。""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "uri": {"type": "string", "description": "记忆 URI"}
                        },
                        "required": ["uri"]
                    }
                ),
                Tool(
                    name="create_memory",
                    description="""创建新记忆。

参数:
- uri: 记忆 URI（如 project://config）
- content: 记忆内容
- priority: 优先级 0-10，默认 5（数字越小优先级越高）
- disclosure: 触发条件（何时加载此记忆）

优先级建议:
- 0-2: 核心身份、关键事实
- 3-5: 一般记忆
- 6-10: 低优先级记忆""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "uri": {"type": "string", "description": "记忆 URI"},
                            "content": {"type": "string", "description": "记忆内容"},
                            "priority": {"type": "integer", "description": "优先级 0-10，默认 5", "default": 5},
                            "disclosure": {"type": "string", "description": "触发条件"}
                        },
                        "required": ["uri", "content"]
                    }
                ),
                Tool(
                    name="update_memory",
                    description="""更新现有记忆。

模式:
- Patch 模式: 提供 old_string 和 new_string 替换指定文本
- Append 模式: 提供 append 为 true 追加内容
- 全量替换: 只提供 content

修改前会自动创建版本快照，支持回滚。""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "uri": {"type": "string", "description": "记忆 URI"},
                            "content": {"type": "string", "description": "新内容（全量替换或追加）"},
                            "old_string": {"type": "string", "description": "要替换的文本"},
                            "new_string": {"type": "string", "description": "替换后的文本"},
                            "append": {"type": "boolean", "description": "是否追加模式", "default": False},
                            "priority": {"type": "integer", "description": "新优先级"},
                            "disclosure": {"type": "string", "description": "新触发条件"}
                        },
                        "required": ["uri"]
                    }
                ),
                Tool(
                    name="delete_memory",
                    description="""删除记忆。

行为:
- 软删除（标记为 deleted）
- 保留版本历史
- 可通过恢复功能找回""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "uri": {"type": "string", "description": "记忆 URI"},
                            "force": {"type": "boolean", "description": "硬删除（不可恢复）", "default": False}
                        },
                        "required": ["uri"]
                    }
                ),
                Tool(
                    name="search_memory",
                    description="""搜索记忆。

搜索范围:
- URI 路径
- 记忆内容
- disclosure 字段

支持按域名、优先级范围过滤。""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "搜索关键词"},
                            "domain": {"type": "string", "description": "限定域名（如 project）"},
                            "limit": {"type": "integer", "description": "返回数量限制，默认 10", "default": 10},
                            "priority_min": {"type": "integer", "description": "最小优先级"},
                            "priority_max": {"type": "integer", "description": "最大优先级"}
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="preload_memory",
                    description="""预加载相关记忆。

根据上下文类型预加载相关记忆:
- file: 根据文件路径查找相关记忆
- directory: 根据目录路径查找项目结构记忆
- error: 根据错误信息查找解决方案
- intent: 根据用户意图预加载相关记忆""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "context_type": {"type": "string", "description": "上下文类型: file/directory/error/intent"},
                            "context_data": {"type": "string", "description": "上下文数据"}
                        },
                        "required": ["context_type", "context_data"]
                    }
                ),
                Tool(
                    name="save_session",
                    description="""保存当前会话。

行为:
- 分析会话操作记录
- 提取重要信息
- 创建会话摘要记忆""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "会话记忆标题"},
                            "summary": {"type": "string", "description": "会话摘要内容"}
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="list_memories",
                    description="""列出记忆。

支持按域名、状态、优先级过滤。""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "domain": {"type": "string", "description": "限定域名"},
                            "status": {"type": "string", "description": "限定状态: active/deprecated/archived"},
                            "limit": {"type": "integer", "description": "返回数量限制，默认 20", "default": 20},
                            "priority_min": {"type": "integer", "description": "最小优先级"},
                            "priority_max": {"type": "integer", "description": "最大优先级"}
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="get_memory_stats",
                    description="""获取记忆统计信息。

返回:
- 总记忆数
- 各状态数量
- 各域名数量
- 访问统计""",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="export_memories",
                    description="""导出记忆到 JSON 格式。

支持按域名过滤，可选择包含版本历史和关系。""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "domain": {"type": "string", "description": "限定域名"},
                            "include_versions": {"type": "boolean", "description": "包含版本历史", "default": False},
                            "include_relations": {"type": "boolean", "description": "包含关系", "default": False}
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="import_memories",
                    description="""导入记忆。

合并策略:
- skip: 跳过已存在的记忆
- overwrite: 覆盖已存在的记忆
- merge: 合并内容""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "data": {"type": "object", "description": "导入数据（JSON 格式）"},
                            "strategy": {"type": "string", "description": "合并策略: skip/overwrite/merge", "default": "skip"}
                        },
                        "required": ["data"]
                    }
                ),
                Tool(
                    name="add_alias",
                    description="""为现有记忆添加别名（新 URI 路径）。

用途:
- 同一记忆可以有多个访问入口
- 不同上下文使用不同名称
- 构建联想网络

示例:
- core://agent/my_user -> user://profile
- project://config -> config://main""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "target_uri": {"type": "string", "description": "目标记忆 URI"},
                            "alias_uri": {"type": "string", "description": "新别名 URI"}
                        },
                        "required": ["target_uri", "alias_uri"]
                    }
                ),
                Tool(
                    name="get_memory_versions",
                    description="""获取记忆的版本历史。

返回:
- 所有历史版本列表
- 每个版本的时间戳和变更说明
- 支持限制返回数量""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "uri": {"type": "string", "description": "记忆 URI"},
                            "limit": {"type": "integer", "description": "返回版本数量限制，默认 10", "default": 10}
                        },
                        "required": ["uri"]
                    }
                ),
                Tool(
                    name="rollback_memory",
                    description="""将记忆回滚到指定版本。

行为:
- 恢复到指定版本的内容
- 创建新的版本记录
- 保留回滚历史

警告: 回滚操作不可撤销，但会创建新版本记录。""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "uri": {"type": "string", "description": "记忆 URI"},
                            "version": {"type": "integer", "description": "目标版本号"}
                        },
                        "required": ["uri", "version"]
                    }
                ),
                Tool(
                    name="diff_versions",
                    description="""对比记忆的两个版本内容。

返回:
- 两个版本的完整内容
- 用于手动或自动比较差异""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "uri": {"type": "string", "description": "记忆 URI"},
                            "version1": {"type": "integer", "description": "第一个版本号"},
                            "version2": {"type": "integer", "description": "第二个版本号"}
                        },
                        "required": ["uri", "version1", "version2"]
                    }
                ),
                Tool(
                    name="list_rollbacks",
                    description="""列出可回滚的版本。

返回:
- 当前版本号
- 可回滚版本列表
- 每个版本的摘要信息""",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "uri": {"type": "string", "description": "记忆 URI"},
                            "limit": {"type": "integer", "description": "返回数量限制，默认 10", "default": 10}
                        },
                        "required": ["uri"]
                    }
                ),
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
            if not self._db_initialized:
                await init_db()
                self._db_initialized = True
            
            try:
                if name == "read_memory":
                    return await self._read_memory(arguments)
                elif name == "create_memory":
                    return await self._create_memory(arguments)
                elif name == "update_memory":
                    return await self._update_memory(arguments)
                elif name == "delete_memory":
                    return await self._delete_memory(arguments)
                elif name == "search_memory":
                    return await self._search_memory(arguments)
                elif name == "preload_memory":
                    return await self._preload_memory(arguments)
                elif name == "save_session":
                    return await self._save_session(arguments)
                elif name == "list_memories":
                    return await self._list_memories(arguments)
                elif name == "get_memory_stats":
                    return await self._get_memory_stats(arguments)
                elif name == "export_memories":
                    return await self._export_memories(arguments)
                elif name == "import_memories":
                    return await self._import_memories(arguments)
                elif name == "add_alias":
                    return await self._add_alias(arguments)
                elif name == "get_memory_versions":
                    return await self._get_memory_versions(arguments)
                elif name == "rollback_memory":
                    return await self._rollback_memory(arguments)
                elif name == "diff_versions":
                    return await self._diff_versions(arguments)
                elif name == "list_rollbacks":
                    return await self._list_rollbacks(arguments)
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def _read_memory(self, args: dict) -> list[TextContent]:
        """读取记忆。"""
        uri = args["uri"]
        
        if is_system_uri(uri):
            result = await handle_system_uri(uri)
            if result:
                return [TextContent(type="text", text=json_dumps(result))]
            return [TextContent(type="text", text=f"未知的系统 URI: {uri}")]
        
        memory = await get_memory(uri)
        if not memory:
            return [TextContent(type="text", text=f"未找到记忆: {uri}")]
        
        result = {
            "uri": memory.uri,
            "content": memory.content,
            "priority": memory.priority,
            "status": memory.status,
            "disclosure": memory.disclosure,
            "access_count": memory.access_count,
            "created_at": memory.created_at,
            "updated_at": memory.updated_at,
        }
        
        versions = await get_versions(uri, limit=5)
        if versions:
            result["recent_versions"] = [
                {"version": v.version, "changed_at": v.changed_at}
                for v in versions
            ]
        
        relations = await get_relations(uri)
        if relations:
            result["relations"] = relations
        
        return [TextContent(type="text", text=json_dumps(result))]
    
    async def _create_memory(self, args: dict) -> list[TextContent]:
        """创建记忆。"""
        uri = args["uri"]
        content = args["content"]
        priority = args.get("priority", 5)
        disclosure = args.get("disclosure", "")
        
        memory = await create_memory(
            uri=uri,
            content=content,
            priority=priority,
            disclosure=disclosure,
        )
        
        result = {
            "success": True,
            "uri": memory.uri,
            "id": memory.id,
            "priority": memory.priority,
            "created_at": memory.created_at,
        }
        
        return [TextContent(type="text", text=json_dumps(result))]
    
    async def _update_memory(self, args: dict) -> list[TextContent]:
        """更新记忆。"""
        uri = args["uri"]
        content = args.get("content")
        old_string = args.get("old_string")
        new_string = args.get("new_string")
        append = args.get("append", False)
        priority = args.get("priority")
        disclosure = args.get("disclosure")
        
        memory = await update_memory(
            uri=uri,
            content=content,
            priority=priority,
            disclosure=disclosure,
            append=append,
            old_text=old_string,
            new_text=new_string,
        )
        
        if not memory:
            return [TextContent(type="text", text=f"未找到记忆: {uri}")]
        
        result = {
            "success": True,
            "uri": memory.uri,
            "priority": memory.priority,
            "updated_at": memory.updated_at,
        }
        
        return [TextContent(type="text", text=json_dumps(result))]
    
    async def _delete_memory(self, args: dict) -> list[TextContent]:
        """删除记忆。"""
        uri = args["uri"]
        force = args.get("force", False)
        
        success = await delete_memory(uri, soft=not force)
        
        if not success:
            return [TextContent(type="text", text=f"未找到记忆: {uri}")]
        
        action = "硬删除" if force else "软删除"
        result = {"success": True, "uri": uri, "action": action}
        
        return [TextContent(type="text", text=json_dumps(result))]
    
    async def _search_memory(self, args: dict) -> list[TextContent]:
        """搜索记忆。"""
        query = args["query"]
        domain = args.get("domain")
        limit = args.get("limit", 10)
        priority_min = args.get("priority_min")
        priority_max = args.get("priority_max")
        
        uri_prefix = f"{domain}://" if domain else None
        
        memories = await search_memories(
            query=query,
            uri_prefix=uri_prefix,
            priority_min=priority_min,
            priority_max=priority_max,
            limit=limit,
        )
        
        result = {
            "query": query,
            "count": len(memories),
            "memories": [
                {
                    "uri": m.uri,
                    "priority": m.priority,
                    "content_preview": m.content[:200] + "..." if len(m.content) > 200 else m.content,
                    "disclosure": m.disclosure,
                }
                for m in memories
            ],
        }
        
        return [TextContent(type="text", text=json_dumps(result))]
    
    async def _preload_memory(self, args: dict) -> list[TextContent]:
        """预加载相关记忆。"""
        context_type = args["context_type"]
        context_data = args["context_data"]
        
        memories = []
        
        if context_type == "file":
            memories = await find_memories_by_path(context_data)
            file_ext = os.path.splitext(context_data)[1]
            if file_ext:
                ext_memories = await search_memories(file_ext, limit=5)
                memories.extend(ext_memories)
        
        elif context_type == "directory":
            memories = await search_memories(context_data, limit=10)
        
        elif context_type == "error":
            memories = await search_memories(context_data, limit=5)
        
        elif context_type == "intent":
            memories = await search_memories(context_data, limit=10)
        
        core_memories = await get_memories_by_priority(max_priority=2)
        
        result = {
            "context_type": context_type,
            "context_data": context_data,
            "core_memories": [
                {"uri": m.uri, "priority": m.priority, "content": m.content}
                for m in core_memories
            ],
            "related_memories": [
                {"uri": m.uri, "priority": m.priority, "content_preview": m.content[:200]}
                for m in memories[:10]
            ],
        }
        
        return [TextContent(type="text", text=json_dumps(result))]
    
    async def _save_session(self, args: dict) -> list[TextContent]:
        """保存会话。"""
        title = args.get("title", "")
        summary = args.get("summary", "")
        
        session_id = datetime.now().strftime("%Y%m%d%H%M%S")
        
        session = await create_session(session_id=session_id)
        
        if summary:
            uri = f"session://{session_id}"
            if title:
                uri = f"session://{title}"
            
            await create_memory(
                uri=uri,
                content=summary,
                priority=3,
            )
        
        result = {
            "success": True,
            "session_id": session_id,
            "message": "会话已保存",
        }
        
        return [TextContent(type="text", text=json_dumps(result))]
    
    async def _list_memories(self, args: dict) -> list[TextContent]:
        """列出记忆。"""
        domain = args.get("domain")
        status = args.get("status")
        limit = args.get("limit", 20)
        priority_min = args.get("priority_min")
        priority_max = args.get("priority_max")
        
        uri_prefix = f"{domain}://" if domain else ""
        
        memories = await list_memories(
            uri_prefix=uri_prefix,
            status=status,
            limit=limit,
            priority_min=priority_min,
            priority_max=priority_max,
        )
        
        result = {
            "count": len(memories),
            "memories": [
                {
                    "uri": m.uri,
                    "priority": m.priority,
                    "status": m.status,
                    "content_preview": m.content[:100] + "..." if len(m.content) > 100 else m.content,
                    "access_count": m.access_count,
                }
                for m in memories
            ],
        }
        
        return [TextContent(type="text", text=json_dumps(result))]
    
    async def _get_memory_stats(self, args: dict) -> list[TextContent]:
        """获取统计信息。"""
        stats = await get_stats()
        
        return [TextContent(type="text", text=json_dumps(stats))]
    
    async def _export_memories(self, args: dict) -> list[TextContent]:
        """导出记忆。"""
        domain = args.get("domain")
        include_versions = args.get("include_versions", False)
        include_relations = args.get("include_relations", False)
        
        uri_prefix = f"{domain}://" if domain else None
        
        data = await export_memories(
            uri_prefix=uri_prefix,
            include_versions=include_versions,
            include_relations=include_relations,
        )
        
        return [TextContent(type="text", text=json_dumps(data))]
    
    async def _import_memories(self, args: dict) -> list[TextContent]:
        """导入记忆。"""
        data = args["data"]
        strategy = args.get("strategy", "skip")
        
        stats = await import_memories(data, strategy)
        
        result = {
            "success": True,
            "stats": stats,
        }
        
        return [TextContent(type="text", text=json_dumps(result))]
    
    async def _add_alias(self, args: dict) -> list[TextContent]:
        """添加别名。"""
        target_uri = args["target_uri"]
        alias_uri = args["alias_uri"]
        
        target_memory = await get_memory(target_uri)
        if not target_memory:
            return [TextContent(type="text", text=f"未找到目标记忆: {target_uri}")]
        
        existing = await get_memory(alias_uri)
        if existing:
            return [TextContent(type="text", text=f"别名 URI 已存在: {alias_uri}")]
        
        success = await add_memory_path(target_memory.id, alias_uri)
        
        if not success:
            return [TextContent(type="text", text=f"添加别名失败")]
        
        result = {
            "success": True,
            "target_uri": target_uri,
            "alias_uri": alias_uri,
            "memory_id": target_memory.id,
        }
        
        return [TextContent(type="text", text=json_dumps(result))]
    
    async def _get_memory_versions(self, args: dict) -> list[TextContent]:
        """获取版本历史。"""
        uri = args["uri"]
        limit = args.get("limit", 10)
        
        memory = await get_memory(uri, increment_access=False)
        if not memory:
            return [TextContent(type="text", text=f"未找到记忆: {uri}")]
        
        versions = await get_versions(uri, limit=limit)
        
        result = {
            "uri": uri,
            "current_version": len(versions) if versions else 0,
            "versions": [
                {
                    "version": v.version,
                    "content_preview": v.content[:100] + "..." if len(v.content) > 100 else v.content,
                    "changed_at": v.changed_at,
                    "changed_by": v.changed_by,
                    "change_reason": v.change_reason,
                }
                for v in versions
            ],
        }
        
        return [TextContent(type="text", text=json_dumps(result))]
    
    async def _rollback_memory(self, args: dict) -> list[TextContent]:
        """回滚记忆。"""
        uri = args["uri"]
        version = args["version"]
        
        memory = await rollback_to_version(uri, version)
        
        if not memory:
            return [TextContent(type="text", text=f"回滚失败: 未找到记忆 {uri} 或版本 {version}")]
        
        result = {
            "success": True,
            "uri": uri,
            "rolled_back_to_version": version,
            "current_content_preview": memory.content[:100] + "..." if len(memory.content) > 100 else memory.content,
            "updated_at": memory.updated_at,
        }
        
        return [TextContent(type="text", text=json_dumps(result))]
    
    async def _diff_versions(self, args: dict) -> list[TextContent]:
        """对比版本。"""
        uri = args["uri"]
        version1 = args["version1"]
        version2 = args["version2"]
        
        diff_result = await diff_versions(uri, version1, version2)
        
        if not diff_result:
            return [TextContent(type="text", text=f"无法对比: 未找到版本 {version1} 或 {version2}")]
        
        content1, content2 = diff_result
        
        result = {
            "uri": uri,
            "version1": version1,
            "version2": version2,
            "content1": content1,
            "content2": content2,
        }
        
        return [TextContent(type="text", text=json_dumps(result))]
    
    async def _list_rollbacks(self, args: dict) -> list[TextContent]:
        """列出可回滚版本。"""
        uri = args["uri"]
        limit = args.get("limit", 10)
        
        memory = await get_memory(uri, increment_access=False)
        if not memory:
            return [TextContent(type="text", text=f"未找到记忆: {uri}")]
        
        versions = await get_versions(uri, limit=limit)
        
        result = {
            "uri": uri,
            "current_version": versions[0].version if versions else 0,
            "can_rollback_to": [
                {
                    "version": v.version,
                    "changed_at": v.changed_at,
                    "changed_by": v.changed_by,
                    "change_reason": v.change_reason,
                    "content_preview": v.content[:100] + "..." if len(v.content) > 100 else v.content,
                }
                for v in versions[1:]
            ],
        }
        
        return [TextContent(type="text", text=json_dumps(result))]
    
    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Entry point for MCP server."""
    server = MemoryMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
