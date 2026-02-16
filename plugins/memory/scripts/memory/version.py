"""
版本控制模块

提供记忆版本历史管理功能。
"""

from datetime import datetime
from typing import List, Optional, Tuple

from .models import Memory, MemoryVersion
from .database import compute_hash
from .crud import get_memory, create_version


async def get_versions(uri: str, limit: int = 10) -> List[MemoryVersion]:
    """
    获取记忆的版本历史
    
    返回指定记忆的所有历史版本，按版本号降序排列。
    
    Args:
        uri: 记忆的唯一标识符
        limit: 返回版本数量限制，默认 10
        
    Returns:
        List[MemoryVersion]: 版本历史列表，最新版本在前
    """
    memory = await Memory.first(where="uri = ?", params=(uri,))
    if not memory:
        return []
    
    return await MemoryVersion.find(
        where="memory_id = ?",
        params=(memory.id,),
        order_by="version DESC",
        limit=limit,
    )


async def get_version(uri: str, version: int) -> Optional[MemoryVersion]:
    """
    获取记忆的特定版本
    
    返回指定记忆的特定版本号的内容快照。
    
    Args:
        uri: 记忆的唯一标识符
        version: 版本号
        
    Returns:
        Optional[MemoryVersion]: 版本记录，不存在则返回 None
    """
    memory = await Memory.first(where="uri = ?", params=(uri,))
    if not memory:
        return None
    
    return await MemoryVersion.first(
        where="memory_id = ? AND version = ?",
        params=(memory.id, version),
    )


async def rollback_to_version(uri: str, version: int, changed_by: str = "user") -> Optional[Memory]:
    """
    回滚记忆到指定版本
    
    将记忆内容恢复到指定版本，同时创建新的版本记录。
    
    Args:
        uri: 记忆的唯一标识符
        version: 目标版本号
        changed_by: 变更来源标识
        
    Returns:
        Optional[Memory]: 回滚后的记忆对象，失败则返回 None
    """
    memory = await get_memory(uri, increment_access=False)
    if not memory:
        return None
    
    target_version = await get_version(uri, version)
    if not target_version:
        return None
    
    await create_version(memory.id, memory.content, memory.updated_at, f"rollback_to_v{version}", changed_by)
    
    memory.content = target_version.content
    memory.content_hash = compute_hash(target_version.content)
    memory.updated_at = datetime.now()
    await memory.save()
    
    return memory


async def diff_versions(uri: str, version1: int, version2: int) -> Optional[Tuple[str, str]]:
    """
    对比两个版本的内容
    
    获取指定记忆的两个版本内容，用于差异比较。
    
    Args:
        uri: 记忆的唯一标识符
        version1: 第一个版本号
        version2: 第二个版本号
        
    Returns:
        Optional[Tuple[str, str]]: (版本1内容, 版本2内容)，任一版本不存在则返回 None
    """
    v1 = await get_version(uri, version1)
    v2 = await get_version(uri, version2)
    
    if not v1 or not v2:
        return None
    
    return (v1.content, v2.content)
