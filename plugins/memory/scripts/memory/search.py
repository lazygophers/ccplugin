"""
搜索模块

提供记忆的搜索和列表功能。
"""

from typing import List, Optional

from .models import Memory, MemoryStatus


async def search_memories(
    query: str,
    uri_prefix: Optional[str] = None,
    priority_min: Optional[int] = None,
    priority_max: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 10,
) -> List[Memory]:
    """
    搜索记忆内容
    
    根据关键词搜索记忆内容，支持多种过滤条件。
    搜索结果按优先级和更新时间排序。
    
    Args:
        query: 搜索关键词，使用 LIKE 模糊匹配
        uri_prefix: URI 前缀过滤，如 "project://"
        priority_min: 最小优先级（数值）
        priority_max: 最大优先级（数值）
        status: 状态过滤，默认排除 DELETED 状态
        limit: 返回结果数量限制，默认 10
        
    Returns:
        List[Memory]: 匹配的记忆列表
    """
    conditions = ["content LIKE ?"]
    params = [f"%{query}%"]
    
    if uri_prefix:
        conditions.append("uri LIKE ?")
        params.append(f"{uri_prefix}%")
    
    if priority_min is not None:
        conditions.append("priority >= ?")
        params.append(priority_min)
    
    if priority_max is not None:
        conditions.append("priority <= ?")
        params.append(priority_max)
    
    if status:
        conditions.append("status = ?")
        params.append(status)
    else:
        conditions.append("status != ?")
        params.append(MemoryStatus.DELETED.value)
    
    where_clause = " AND ".join(conditions)
    
    return await Memory.find(
        where=where_clause,
        params=tuple(params),
        order_by="priority DESC, updated_at DESC",
        limit=limit,
    )


async def list_memories(
    uri_prefix: str = "",
    priority_min: Optional[int] = None,
    priority_max: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Memory]:
    """
    列出记忆列表
    
    根据条件列出记忆，支持分页和多种过滤条件。
    
    Args:
        uri_prefix: URI 前缀过滤，如 "project://"
        priority_min: 最小优先级（数值）
        priority_max: 最大优先级（数值）
        status: 状态过滤，默认排除 DELETED 状态
        limit: 返回结果数量限制，默认 50
        offset: 分页偏移量，默认 0
        
    Returns:
        List[Memory]: 记忆列表
    """
    conditions = []
    params = []
    
    if uri_prefix:
        conditions.append("uri LIKE ?")
        params.append(f"{uri_prefix}%")
    
    if priority_min is not None:
        conditions.append("priority >= ?")
        params.append(priority_min)
    
    if priority_max is not None:
        conditions.append("priority <= ?")
        params.append(priority_max)
    
    if status:
        conditions.append("status = ?")
        params.append(status)
    else:
        conditions.append("status != ?")
        params.append(MemoryStatus.DELETED.value)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    return await Memory.find(
        where=where_clause,
        params=tuple(params) if params else None,
        order_by="priority DESC, updated_at DESC",
        limit=limit,
        offset=offset,
    )


async def get_memories_by_priority(max_priority: int = 3) -> List[Memory]:
    """
    获取高优先级记忆
    
    获取优先级数值小于等于指定值的活跃记忆，
    通常用于预加载核心记忆到上下文。
    
    Args:
        max_priority: 最大优先级数值，默认 3（即优先级 0-3 的记忆）
        
    Returns:
        List[Memory]: 高优先级记忆列表，按优先级升序排列
    """
    return await Memory.find(
        where="priority <= ? AND status = ?",
        params=(max_priority, MemoryStatus.ACTIVE.value),
        order_by="priority ASC",
    )
