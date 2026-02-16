"""
路径关联模块

提供记忆与文件路径的关联功能。
"""

from datetime import datetime
from typing import List

from .models import Memory, MemoryPath, MemoryStatus


async def add_memory_path(memory_id: int, path: str) -> MemoryPath:
    """
    添加记忆路径关联
    
    将记忆与文件路径关联，用于基于文件路径检索相关记忆。
    如果关联已存在，则返回现有记录。
    
    Args:
        memory_id: 记忆 ID
        path: 文件路径
        
    Returns:
        MemoryPath: 创建或现有的路径关联记录
    """
    existing = await MemoryPath.first(
        where="memory_id = ? AND path = ?",
        params=(memory_id, path),
    )
    if existing:
        return existing
    
    return await MemoryPath.create(
        memory_id=memory_id,
        path=path,
        created_at=datetime.now(),
    )


async def get_memory_paths(memory_id: int) -> List[MemoryPath]:
    """
    获取记忆关联的所有路径
    
    返回指定记忆关联的所有文件路径。
    
    Args:
        memory_id: 记忆 ID
        
    Returns:
        List[MemoryPath]: 路径关联列表
    """
    return await MemoryPath.find(where="memory_id = ?", params=(memory_id,))


async def find_memories_by_path(path: str) -> List[Memory]:
    """
    根据路径查找相关记忆
    
    查找与指定路径关联的所有活跃记忆。
    
    Args:
        path: 文件路径（支持模糊匹配）
        
    Returns:
        List[Memory]: 相关记忆列表
    """
    paths = await MemoryPath.find(where="path LIKE ?", params=(f"%{path}%",))
    memory_ids = [p.memory_id for p in paths]
    
    if not memory_ids:
        return []
    
    memories = []
    for mid in memory_ids:
        memory = await Memory.first(where="id = ? AND status = ?", params=(mid, MemoryStatus.ACTIVE.value))
        if memory:
            memories.append(memory)
    
    return memories
