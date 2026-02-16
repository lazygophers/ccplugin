"""
统计和清理模块

提供记忆统计和清理功能。
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from .models import Memory, MemoryVersion, MemoryRelation, MemoryStatus
from .lifecycle import archive_memory
from .crud import delete_memory


async def get_stats() -> Dict[str, Any]:
    """
    获取记忆统计信息
    
    返回记忆系统的整体统计数据，包括数量分布等。
    
    Returns:
        Dict[str, Any]: 统计数据
    """
    total = await Memory.count(where="status != ?", params=(MemoryStatus.DELETED.value,))
    active = await Memory.count(where="status = ?", params=(MemoryStatus.ACTIVE.value,))
    deprecated = await Memory.count(where="status = ?", params=(MemoryStatus.DEPRECATED.value,))
    archived = await Memory.count(where="status = ?", params=(MemoryStatus.ARCHIVED.value,))
    
    by_priority = {}
    for p in range(11):
        count = await Memory.count(where="priority = ? AND status = ?", params=(p, MemoryStatus.ACTIVE.value))
        if count > 0:
            by_priority[p] = count
    
    by_uri_prefix = {}
    for prefix in ["project://", "workflow://", "user://", "task://", "system://", "session://", "file://", "error://"]:
        count = await Memory.count(where="uri LIKE ? AND status = ?", params=(f"{prefix}%", MemoryStatus.ACTIVE.value))
        if count > 0:
            by_uri_prefix[prefix.rstrip("://")] = count
    
    versions_count = await MemoryVersion.count()
    relations_count = await MemoryRelation.count()
    
    return {
        "total": total,
        "active": active,
        "deprecated": deprecated,
        "archived": archived,
        "by_priority": by_priority,
        "by_uri_prefix": by_uri_prefix,
        "versions_count": versions_count,
        "relations_count": relations_count,
    }


async def clean_memories(
    unused_days: Optional[int] = None,
    deprecated_days: Optional[int] = None,
    dry_run: bool = False,
) -> Dict[str, int]:
    """
    清理记忆
    
    根据条件清理不活跃或已废弃的记忆。
    
    Args:
        unused_days: 清理超过指定天数未访问的活跃记忆（归档处理）
        deprecated_days: 清理超过指定天数已废弃的记忆（软删除处理）
        dry_run: 预览模式，只统计不执行
        
    Returns:
        Dict[str, int]: 清理统计
    """
    stats = {"cleaned": 0, "archived": 0}
    
    if unused_days:
        cutoff = datetime.now() - timedelta(days=unused_days)
        memories = await Memory.find(
            where="last_accessed_at < ? AND status = ?",
            params=(cutoff.isoformat(), MemoryStatus.ACTIVE.value),
        )
        
        for memory in memories:
            if dry_run:
                stats["cleaned"] += 1
            else:
                await archive_memory(memory.uri)
                stats["archived"] += 1
    
    if deprecated_days:
        cutoff = datetime.now() - timedelta(days=deprecated_days)
        memories = await Memory.find(
            where="deprecated_at < ? AND status = ?",
            params=(cutoff.isoformat(), MemoryStatus.DEPRECATED.value),
        )
        
        for memory in memories:
            if dry_run:
                stats["cleaned"] += 1
            else:
                await delete_memory(memory.uri, soft=True)
                stats["cleaned"] += 1
    
    return stats
