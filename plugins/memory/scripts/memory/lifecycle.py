"""
生命周期管理模块

提供记忆优先级和状态管理功能。
"""

import json
from datetime import datetime
from typing import Optional

from .models import Memory, MemoryStatus
from .crud import get_memory


async def set_priority(uri: str, priority: int) -> Optional[Memory]:
    """
    设置记忆优先级
    
    修改记忆的优先级数值。优先级范围为 0-10，
    数值越小优先级越高，越容易被加载到上下文。
    
    Args:
        uri: 记忆的唯一标识符
        priority: 新优先级，范围 0-10
        
    Returns:
        Optional[Memory]: 更新后的记忆对象，不存在则返回 None
        
    Raises:
        ValueError: 优先级超出范围时抛出
    """
    if priority < 0 or priority > 10:
        raise ValueError("优先级必须在 0-10 之间")
    
    memory = await get_memory(uri, increment_access=False)
    if not memory:
        return None
    
    memory.priority = priority
    memory.updated_at = datetime.now()
    await memory.save()
    
    return memory


async def deprecate_memory(uri: str, reason: str = "") -> Optional[Memory]:
    """
    废弃记忆
    
    将记忆状态标记为 DEPRECATED，表示不再推荐使用但保留记录。
    可记录废弃原因到元数据中。
    
    Args:
        uri: 记忆的唯一标识符
        reason: 废弃原因描述
        
    Returns:
        Optional[Memory]: 更新后的记忆对象，不存在则返回 None
    """
    memory = await get_memory(uri, increment_access=False)
    if not memory:
        return None
    
    memory.status = MemoryStatus.DEPRECATED.value
    memory.deprecated_at = datetime.now()
    memory.updated_at = datetime.now()
    
    if reason:
        meta = json.loads(memory.metadata or "{}")
        meta["deprecation_reason"] = reason
        memory.metadata = json.dumps(meta)
    
    await memory.save()
    return memory


async def archive_memory(uri: str) -> Optional[Memory]:
    """
    归档记忆
    
    将记忆状态标记为 ARCHIVED，用于长期存储不活跃的记忆。
    归档后的记忆不会在常规搜索中出现，但仍可通过状态过滤查询。
    
    Args:
        uri: 记忆的唯一标识符
        
    Returns:
        Optional[Memory]: 更新后的记忆对象，不存在则返回 None
    """
    memory = await get_memory(uri, increment_access=False)
    if not memory:
        return None
    
    memory.status = MemoryStatus.ARCHIVED.value
    memory.updated_at = datetime.now()
    await memory.save()
    
    return memory


async def restore_memory(uri: str) -> Optional[Memory]:
    """
    恢复记忆
    
    将记忆状态恢复为 ACTIVE，清除废弃时间戳。
    可用于恢复软删除、废弃或归档的记忆。
    
    Args:
        uri: 记忆的唯一标识符
        
    Returns:
        Optional[Memory]: 恢复后的记忆对象，不存在则返回 None
    """
    memory = await Memory.first(where="uri = ?", params=(uri,))
    if not memory:
        return None
    
    memory.status = MemoryStatus.ACTIVE.value
    memory.deprecated_at = None
    memory.updated_at = datetime.now()
    await memory.save()
    
    return memory
