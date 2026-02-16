"""
CRUD 操作模块

提供记忆的创建、读取、更新、删除功能。
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional

from lib import logging

from .models import Memory, MemoryStatus, MemoryVersion
from .database import compute_hash


async def create_version(
    memory_id: int,
    content: str,
    changed_at: datetime,
    change_reason: str,
    changed_by: str,
) -> MemoryVersion:
    """
    创建记忆版本记录（内部函数）
    
    在记忆内容变更时自动创建版本快照，用于版本历史追踪和回滚。
    
    Args:
        memory_id: 记忆 ID
        content: 变更前的内容快照
        changed_at: 变更时间
        change_reason: 变更原因描述
        changed_by: 变更来源标识
        
    Returns:
        MemoryVersion: 创建的版本记录
    """
    last_version = await MemoryVersion.first(
        where="memory_id = ?",
        params=(memory_id,),
        order_by="version DESC",
    )
    
    version_num = (last_version.version + 1) if last_version else 1
    
    return await MemoryVersion.create(
        memory_id=memory_id,
        version=version_num,
        content=content,
        changed_at=changed_at,
        change_reason=change_reason,
        changed_by=changed_by,
    )


async def create_memory(
    uri: str,
    content: str,
    priority: int = 5,
    disclosure: str = "",
    metadata: Optional[Dict[str, Any]] = None,
    changed_by: str = "user",
) -> Memory:
    """
    创建或更新记忆
    
    如果 URI 已存在，则更新现有记忆并创建版本记录；
    如果 URI 不存在，则创建新记忆。
    
    Args:
        uri: 记忆的唯一标识符，格式如 "project://name"
        content: 记忆内容
        priority: 优先级 0-10，默认 5，数值越小优先级越高
        disclosure: 触发条件，描述何时加载此记忆
        metadata: 可选的元数据字典
        changed_by: 变更来源标识 (user/auto/hook/import)
        
    Returns:
        Memory: 创建或更新后的记忆对象
    """
    now = datetime.now()
    content_hash = compute_hash(content)
    
    existing = await Memory.first(where="uri = ?", params=(uri,))
    
    if existing:
        if existing.content != content:
            await create_version(existing.id, existing.content, existing.updated_at, "content_update", changed_by)
        
        existing.content = content
        existing.content_hash = content_hash
        existing.priority = priority
        existing.disclosure = disclosure
        existing.updated_at = now
        existing.metadata = json.dumps(metadata or {})
        await existing.save()
        return existing
    
    memory = await Memory.create(
        uri=uri,
        content=content,
        content_hash=content_hash,
        priority=priority,
        disclosure=disclosure,
        status=MemoryStatus.ACTIVE.value,
        access_count=0,
        created_at=now,
        updated_at=now,
        metadata=json.dumps(metadata or {}),
    )
    
    return memory


async def get_memory(uri: str, increment_access: bool = True) -> Optional[Memory]:
    """
    获取指定 URI 的记忆
    
    根据 URI 查找记忆，可选择是否增加访问计数。
    不会返回已删除状态的记忆。
    
    Args:
        uri: 记忆的唯一标识符
        increment_access: 是否增加访问计数，默认 True
        
    Returns:
        Optional[Memory]: 记忆对象，如不存在则返回 None
    """
    memory = await Memory.first(where="uri = ? AND status != ?", params=(uri, MemoryStatus.DELETED.value))
    
    if memory and increment_access:
        memory.access_count += 1
        memory.last_accessed_at = datetime.now()
        await memory.save()
    
    return memory


async def update_memory(
    uri: str,
    content: Optional[str] = None,
    priority: Optional[int] = None,
    disclosure: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    append: bool = False,
    old_text: Optional[str] = None,
    new_text: Optional[str] = None,
    changed_by: str = "user",
) -> Optional[Memory]:
    """
    更新记忆内容或属性
    
    支持多种更新模式：直接替换、追加、文本替换。
    内容变化时会自动创建版本记录。
    
    Args:
        uri: 记忆的唯一标识符
        content: 新内容，如提供则替换或追加
        priority: 新优先级
        disclosure: 新触发条件
        metadata: 要合并的元数据
        append: 是否追加模式，将 content 追加到现有内容后
        old_text: 要替换的旧文本（与 new_text 配合使用）
        new_text: 替换后的新文本（与 old_text 配合使用）
        changed_by: 变更来源标识
        
    Returns:
        Optional[Memory]: 更新后的记忆对象，如不存在则返回 None
    """
    memory = await get_memory(uri, increment_access=False)
    if not memory:
        return None
    
    now = datetime.now()
    
    if old_text and new_text:
        new_content = memory.content.replace(old_text, new_text)
        if new_content != memory.content:
            await create_version(memory.id, memory.content, memory.updated_at, "content_update", changed_by)
            memory.content = new_content
            memory.content_hash = compute_hash(new_content)
    elif content is not None:
        if append:
            new_content = memory.content + "\n" + content
        else:
            new_content = content
        
        if new_content != memory.content:
            await create_version(memory.id, memory.content, memory.updated_at, "content_update", changed_by)
            memory.content = new_content
            memory.content_hash = compute_hash(new_content)
    
    if priority is not None:
        memory.priority = priority
    
    if disclosure is not None:
        memory.disclosure = disclosure
    
    if metadata is not None:
        current_meta = json.loads(memory.metadata or "{}")
        current_meta.update(metadata)
        memory.metadata = json.dumps(current_meta)
    
    memory.updated_at = now
    await memory.save()
    
    return memory


async def delete_memory(uri: str, soft: bool = True) -> bool:
    """
    删除记忆
    
    支持软删除和硬删除两种模式。软删除将状态标记为 DELETED，
    硬删除则从数据库中彻底移除。
    
    Args:
        uri: 记忆的唯一标识符
        soft: 是否软删除，默认 True。软删除可恢复，硬删除不可恢复
        
    Returns:
        bool: 删除成功返回 True，记忆不存在返回 False
    """
    memory = await Memory.first(where="uri = ?", params=(uri,))
    
    if not memory:
        return False
    
    if soft:
        memory.status = MemoryStatus.DELETED.value
        memory.updated_at = datetime.now()
        await memory.save()
    else:
        await Memory.delete(where="uri = ?", params=(uri,))
    
    return True
