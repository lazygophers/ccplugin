"""
导入导出模块

提供记忆数据的导入导出功能。
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from lib import logging

from .crud import create_memory, update_memory
from .models import Memory, MemoryStatus
from .search import list_memories
from .version import get_versions
from .relation import get_relations


async def export_memories(
    uri_prefix: Optional[str] = None,
    include_versions: bool = False,
    include_relations: bool = False,
) -> Dict[str, Any]:
    """
    导出记忆数据
    
    将记忆数据导出为 JSON 格式，支持选择性导出版本历史和关系。
    
    Args:
        uri_prefix: URI 前缀过滤，如不指定则导出所有
        include_versions: 是否包含版本历史
        include_relations: 是否包含关系数据
        
    Returns:
        Dict[str, Any]: 导出的数据结构
    """
    memories = await list_memories(uri_prefix=uri_prefix or "", limit=10000)
    
    export_data = {
        "exported_at": datetime.now().isoformat(),
        "version": "1.0",
        "memories": [],
    }
    
    for memory in memories:
        mem_data = {
            "uri": memory.uri,
            "content": memory.content,
            "priority": memory.priority,
            "disclosure": memory.disclosure,
            "status": memory.status,
            "metadata": json.loads(memory.metadata or "{}"),
            "created_at": memory.created_at,
            "updated_at": memory.updated_at,
        }
        
        if include_versions:
            versions = await get_versions(memory.uri, limit=100)
            mem_data["versions"] = [
                {
                    "version": v.version,
                    "content": v.content,
                    "changed_at": v.changed_at,
                    "change_reason": v.change_reason,
                    "changed_by": v.changed_by,
                }
                for v in versions
            ]
        
        if include_relations:
            relations = await get_relations(memory.uri)
            mem_data["relations"] = relations
        
        export_data["memories"].append(mem_data)
    
    return export_data


async def import_memories(
    data: Dict[str, Any],
    strategy: str = "skip",
    changed_by: str = "import",
) -> Dict[str, int]:
    """
    导入记忆数据
    
    从 JSON 格式数据导入记忆，支持多种冲突处理策略。
    
    Args:
        data: 导入数据，格式同 export_memories 输出
        strategy: 冲突处理策略
            - "skip": 跳过已存在的记忆（默认）
            - "overwrite": 覆盖已存在的记忆
            - "merge": 合并内容（追加到现有内容后）
        changed_by: 变更来源标识
        
    Returns:
        Dict[str, int]: 导入统计
    """
    stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}
    
    for mem_data in data.get("memories", []):
        try:
            uri = mem_data["uri"]
            content = mem_data["content"]
            
            existing = await Memory.first(where="uri = ?", params=(uri,))
            
            if existing:
                if strategy == "skip":
                    stats["skipped"] += 1
                    continue
                elif strategy == "overwrite":
                    await update_memory(uri, content=content, changed_by=changed_by)
                    stats["updated"] += 1
                elif strategy == "merge":
                    new_content = existing.content + "\n" + content
                    await update_memory(uri, content=new_content, changed_by=changed_by)
                    stats["updated"] += 1
            else:
                await create_memory(
                    uri=uri,
                    content=content,
                    priority=mem_data.get("priority", 5),
                    disclosure=mem_data.get("disclosure", ""),
                    metadata=mem_data.get("metadata"),
                    changed_by=changed_by,
                )
                stats["created"] += 1
        except Exception as e:
            logging.error(f"导入记忆失败: {e}")
            stats["errors"] += 1
    
    return stats
