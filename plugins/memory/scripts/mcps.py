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
- detect_patterns: 检测操作模式
- detect_conflicts: 检测冲突
- resolve_conflict: 解决冲突
- generate_report: 生成分析报告
- get_recommendations: 获取推荐
"""

import json
import os
import sys
from datetime import datetime
from dataclasses import dataclass
from typing import Any, Dict, List


class DateTimeEncoder(json.JSONEncoder):
	"""自定义 JSON 编码器，处理 datetime 对象。"""
	def default(self, o):
		if isinstance(o, datetime):
			return o.isoformat()
		try:
			return super().default(o)
		except TypeError:
			return str(o)


def json_dumps(obj: Any) -> str:
	"""使用自定义编码器序列化 JSON。"""
	return json.dumps(obj, cls=DateTimeEncoder, ensure_ascii=False, indent=2)

# 设置路径以便导入本地模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))




class MemoryMCPServer:
	"""MCP Server for Memory operations."""

	def __init__(self) -> None:
		self.server = object()
		self._db_initialized = False

	async def _ensure_db(self) -> None:
		if self._db_initialized:
			return
		from memory.database import init_db

		await init_db()
		self._db_initialized = True

	def _text(self, payload: Any) -> List["TextContent"]:
		if isinstance(payload, str):
			return [TextContent(text=payload)]
		return [TextContent(text=json_dumps(payload))]

	async def _read_memory(self, args: Dict[str, Any]) -> List["TextContent"]:
		await self._ensure_db()
		uri = str(args.get("uri", ""))
		from memory import get_memory, handle_system_uri, is_system_uri

		if is_system_uri(uri):
			data = await handle_system_uri(uri)
			if data is None:
				return self._text(f"未找到: {uri}")
			return self._text(data)

		memory = await get_memory(uri)
		if not memory:
			return self._text(f"未找到: {uri}")

		return self._text(
			{
				"uri": str(memory.uri),
				"content": str(memory.content),
				"priority": memory.priority,
				"disclosure": str(memory.disclosure),
				"status": str(memory.status),
				"updated_at": memory.updated_at,
			}
		)

	async def _create_memory(self, args: Dict[str, Any]) -> List["TextContent"]:
		await self._ensure_db()
		uri = str(args.get("uri", ""))
		content = str(args.get("content", ""))
		priority = int(args.get("priority", 5))
		disclosure = str(args.get("disclosure", ""))
		from memory import create_memory

		memory = await create_memory(uri=uri, content=content, priority=priority, disclosure=disclosure)
		return self._text({"success": True, "uri": str(memory.uri)})

	async def _update_memory(self, args: Dict[str, Any]) -> List["TextContent"]:
		await self._ensure_db()
		uri = str(args.get("uri", ""))
		content = args.get("content")
		priority = args.get("priority")
		disclosure = args.get("disclosure")
		append = bool(args.get("append", False))
		from memory import update_memory

		memory = await update_memory(
			uri=uri,
			content=str(content) if content is not None else None,
			priority=int(priority) if priority is not None else None,
			disclosure=str(disclosure) if disclosure is not None else None,
			append=append,
		)
		if not memory:
			return self._text(f"未找到: {uri}")
		return self._text({"success": True, "uri": str(memory.uri)})

	async def _delete_memory(self, args: Dict[str, Any]) -> List["TextContent"]:
		await self._ensure_db()
		uri = str(args.get("uri", ""))
		from memory import delete_memory

		ok = await delete_memory(uri)
		if not ok:
			return self._text(f"未找到: {uri}")
		return self._text({"success": True, "uri": uri, "deleted": True})

	async def _search_memory(self, args: Dict[str, Any]) -> List["TextContent"]:
		await self._ensure_db()
		query = str(args.get("query", ""))
		domain = args.get("domain")
		limit = int(args.get("limit", 20))
		from memory import search_memories

		uri_prefix = f"{domain}://" if domain else None
		memories = await search_memories(query=query, uri_prefix=uri_prefix, limit=limit)
		return self._text(
			{
				"query": query,
				"count": len(memories),
				"memories": [{"uri": str(m.uri), "priority": m.priority} for m in memories],
			}
		)

	async def _preload_memory(self, args: Dict[str, Any]) -> List["TextContent"]:
		await self._ensure_db()
		return self._text({"context_type": args.get("context_type"), "context_data": args.get("context_data")})

	async def _save_session(self, args: Dict[str, Any]) -> List["TextContent"]:
		await self._ensure_db()
		title = str(args.get("title", ""))
		summary = str(args.get("summary", ""))
		from memory import create_session, end_session

		session = await create_session(session_id=title or "session")
		session_id = str(session.session_id)
		await end_session(session_id, summary=summary)
		return self._text({"success": True, "session_id": session_id})

	async def _list_memories(self, args: Dict[str, Any]) -> List["TextContent"]:
		await self._ensure_db()
		uri_prefix = str(args.get("uri_prefix", ""))
		limit = int(args.get("limit", 50))
		from memory import list_memories

		memories = await list_memories(uri_prefix=uri_prefix, limit=limit)
		return self._text(
			{
				"count": len(memories),
				"memories": [{"uri": str(m.uri), "priority": m.priority} for m in memories],
			}
		)

	async def _get_memory_stats(self, args: Dict[str, Any]) -> List["TextContent"]:
		await self._ensure_db()
		from memory import get_stats

		stats = await get_stats()
		return self._text(stats)

	async def _export_memories(self, args: Dict[str, Any]) -> List["TextContent"]:
		await self._ensure_db()
		from memory import export_memories

		data = await export_memories(
			uri_prefix=args.get("uri_prefix"),
			include_versions=bool(args.get("include_versions", False)),
			include_relations=bool(args.get("include_relations", False)),
		)
		return self._text(data)

	async def _import_memories(self, args: Dict[str, Any]) -> List["TextContent"]:
		await self._ensure_db()
		from memory import import_memories

		data = args.get("data") or {}
		strategy = str(args.get("strategy", "skip"))
		stats = await import_memories(data=data, strategy=strategy)
		return self._text({"success": True, "stats": stats})

	async def _add_alias(self, args: Dict[str, Any]) -> List["TextContent"]:
		await self._ensure_db()
		target_uri = str(args.get("target_uri", ""))
		alias_uri = str(args.get("alias_uri", ""))
		from memory import create_memory, get_memory

		target = await get_memory(target_uri, increment_access=False)
		if not target:
			return self._text(f"未找到: {target_uri}")
		alias = await create_memory(uri=alias_uri, content=str(target.content), priority=5)
		return self._text({"success": True, "alias": str(alias.uri), "target": target_uri})

	async def _get_memory_versions(self, args: Dict[str, Any]) -> List["TextContent"]:
		await self._ensure_db()
		uri = str(args.get("uri", ""))
		limit = int(args.get("limit", 10))
		from memory import get_versions

		versions = await get_versions(uri, limit=limit)
		return self._text(
			{
				"uri": uri,
				"count": len(versions),
				"versions": [{"version": v.version, "changed_at": v.changed_at} for v in versions],
			}
		)

	async def _rollback_memory(self, args: Dict[str, Any]) -> List["TextContent"]:
		await self._ensure_db()
		uri = str(args.get("uri", ""))
		version = int(args.get("version", 0))
		from memory import rollback_to_version

		memory = await rollback_to_version(uri, version)
		if not memory:
			return self._text(f"未找到: {uri}")
		return self._text({"success": True, "uri": uri, "version": version})

	async def _diff_versions(self, args: Dict[str, Any]) -> List["TextContent"]:
		await self._ensure_db()
		uri = str(args.get("uri", ""))
		version1 = int(args.get("version1", 0))
		version2 = int(args.get("version2", 0))
		from memory import diff_versions

		pair = await diff_versions(uri, version1, version2)
		if not pair:
			return self._text("无法对比")
		content1, content2 = pair
		return self._text({"uri": uri, "version1": version1, "version2": version2, "content1": content1, "content2": content2})

	async def _list_rollbacks(self, args: Dict[str, Any]) -> List["TextContent"]:
		await self._ensure_db()
		uri = str(args.get("uri", ""))
		from memory import get_versions

		versions = await get_versions(uri, limit=50)
		return self._text({"uri": uri, "rollback_versions": [v.version for v in versions]})


@dataclass
class TextContent:
	text: str
