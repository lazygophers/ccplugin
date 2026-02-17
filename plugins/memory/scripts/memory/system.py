"""
系统 URI 处理模块

提供特殊 URI 的处理功能：
- system://boot - 加载核心记忆（priority ≤ 2）
- system://index - 全量记忆索引
- system://recent - 最近修改的记忆
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .crud import get_memory
from .search import list_memories, get_memories_by_priority
from .stats import get_stats
from .models import Memory


async def handle_system_uri(uri: str, limit: int = 20) -> Optional[Dict[str, Any]]:
    """
    处理系统 URI
    
    Args:
        uri: 系统 URI
        limit: 返回数量限制
        
    Returns:
        处理结果字典，如果不是系统 URI 返回 None
    """
    if not uri.startswith("system://"):
        return None
    
    path = uri[9:]
    
    if path == "boot":
        return await _handle_boot()
    elif path == "index":
        return await _handle_index()
    elif path == "recent":
        return await _handle_recent(limit)
    elif path.startswith("recent/"):
        try:
            n = int(path.split("/")[1])
            return await _handle_recent(n)
        except (ValueError, IndexError):
            return await _handle_recent(limit)
    else:
        return None


async def _handle_boot() -> Dict[str, Any]:
    """
    处理 system://boot
    
    加载核心记忆（priority ≤ 2），用于会话启动时初始化 AI 身份。
    """
    core_memories = await get_memories_by_priority(max_priority=2)
    
    result = {
        "uri": "system://boot",
        "title": "核心记忆加载",
        "description": "以下记忆定义了 AI 的核心身份和关键知识",
        "memories": [],
        "loaded_count": len(core_memories),
        "timestamp": datetime.now().isoformat(),
    }
    
    for mem in core_memories:
        result["memories"].append({
            "uri": mem.uri,
            "priority": mem.priority,
            "disclosure": mem.disclosure,
            "content": mem.content,
            "access_count": mem.access_count,
        })
    
    return result


async def _handle_index() -> Dict[str, Any]:
    """
    处理 system://index
    
    显示全量记忆索引，按域名分组。
    """
    all_memories = await list_memories(limit=1000)
    stats = await get_stats()
    
    domains: Dict[str, List[Dict]] = {}
    
    for mem in all_memories:
        domain = mem.uri.split("://")[0] if "://" in mem.uri else "other"
        if domain not in domains:
            domains[domain] = []
        
        domains[domain].append({
            "uri": mem.uri,
            "priority": mem.priority,
            "status": mem.status,
            "content_preview": mem.content[:100] + "..." if len(mem.content) > 100 else mem.content,
        })
    
    return {
        "uri": "system://index",
        "title": "记忆索引",
        "description": "全量记忆概览，按域名分组",
        "stats": stats,
        "domains": domains,
        "total_count": len(all_memories),
        "timestamp": datetime.now().isoformat(),
    }


async def _handle_recent(limit: int = 10) -> Dict[str, Any]:
    """
    处理 system://recent
    
    显示最近修改的记忆。
    """
    all_memories = await list_memories(limit=100)
    
    sorted_memories = sorted(
        all_memories,
        key=lambda m: m.updated_at or "",
        reverse=True
    )[:limit]
    
    recent_memories = []
    for mem in sorted_memories:
        recent_memories.append({
            "uri": mem.uri,
            "priority": mem.priority,
            "status": mem.status,
            "content_preview": mem.content[:150] + "..." if len(mem.content) > 150 else mem.content,
            "updated_at": mem.updated_at,
            "access_count": mem.access_count,
        })
    
    return {
        "uri": "system://recent",
        "title": f"最近修改的记忆 (前 {limit} 条)",
        "description": "按更新时间倒序排列",
        "memories": recent_memories,
        "count": len(recent_memories),
        "timestamp": datetime.now().isoformat(),
    }


def is_system_uri(uri: str) -> bool:
    """检查是否为系统 URI"""
    return uri.startswith("system://")


def get_system_uri_description(uri: str) -> Optional[str]:
    """获取系统 URI 的描述"""
    if not uri.startswith("system://"):
        return None
    
    path = uri[9:]
    
    descriptions = {
        "boot": "加载核心记忆（priority ≤ 2），用于初始化 AI 身份",
        "index": "显示全量记忆索引，按域名分组",
        "recent": "显示最近修改的记忆（默认 10 条）",
    }
    
    if path in descriptions:
        return descriptions[path]
    
    if path.startswith("recent/"):
        return f"显示最近修改的记忆（指定数量）"
    
    return None
