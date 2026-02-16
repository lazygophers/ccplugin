"""
记忆管理模块

使用 lib/db ORM 管理记忆存储，提供完整的记忆生命周期管理。

功能模块:
- CRUD 操作: create_memory, get_memory, update_memory, delete_memory
- 搜索检索: search_memories, list_memories, get_memories_by_priority
- 生命周期: set_priority, deprecate_memory, archive_memory, restore_memory
- 版本控制: get_versions, rollback_to_version, diff_versions
- 关系管理: add_relation, get_relations, remove_relation
- 导入导出: export_memories, import_memories
- 统计清理: get_stats, clean_memories
- 会话管理: create_session, end_session
- 错误解决: record_error_solution, find_error_solution, mark_solution_success
"""

import hashlib
import json
import os
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from lib import logging
from lib.db import (
    DatabaseConfig,
    DatabaseConnection,
    DatabaseType,
    Model,
    Integer,
    String,
    Text,
    DateTime,
    Float,
    Boolean,
)
from lib.utils import get_project_plugins_dir


class MemoryStatus(str, Enum):
    """
    记忆状态枚举
    
    Attributes:
        ACTIVE: 活跃状态，正常使用中
        DEPRECATED: 已废弃，不再推荐使用但保留
        ARCHIVED: 已归档，长期存储不活跃记忆
        DELETED: 已删除，软删除状态可恢复
    """
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"
    DELETED = "deleted"


class RelationType(str, Enum):
    """
    记忆关系类型枚举
    
    Attributes:
        RELATES_TO: 相关关系，两条记忆内容相关
        DEPENDS_ON: 依赖关系，源记忆依赖目标记忆
        CONTRADICTS: 矛盾关系，两条记忆内容冲突
        EVOLVES_FROM: 演化关系，源记忆由目标记忆演化而来
    """
    RELATES_TO = "relates_to"
    DEPENDS_ON = "depends_on"
    CONTRADICTS = "contradicts"
    EVOLVES_FROM = "evolves_from"


class Memory(Model):
    """
    记忆模型
    
    存储记忆的核心信息，包括 URI 标识、内容、优先级、状态等。
    
    Attributes:
        id: 主键，自增
        uri: URI 标识，唯一，格式如 project://name
        content: 记忆内容
        content_hash: 内容 SHA256 哈希，用于快速比较
        priority: 优先级 0-10，数值越小优先级越高
        disclosure: 触发条件，描述何时加载此记忆
        status: 状态，参见 MemoryStatus
        access_count: 访问次数统计
        last_accessed_at: 最后访问时间
        created_at: 创建时间
        updated_at: 更新时间
        deprecated_at: 废弃时间
        metadata: JSON 格式的元数据
    """
    __tablename__ = "memories"
    
    id = Integer(primary_key=True, auto_increment=True)
    uri = String(255, unique=True, index=True, nullable=False)
    content = Text(nullable=False)
    content_hash = String(64, index=True)
    priority = Integer(default=5)
    disclosure = Text(default="")
    status = String(20, default=MemoryStatus.ACTIVE.value, index=True)
    access_count = Integer(default=0)
    last_accessed_at = DateTime()
    created_at = DateTime(nullable=False)
    updated_at = DateTime(nullable=False)
    deprecated_at = DateTime()
    metadata = Text(default="{}")


class MemoryPath(Model):
    """
    记忆路径模型
    
    关联记忆与文件路径，用于基于文件路径检索相关记忆。
    
    Attributes:
        id: 主键，自增
        memory_id: 关联的记忆 ID
        path: 文件路径，支持模糊匹配
        created_at: 创建时间
    """
    __tablename__ = "memory_paths"
    
    id = Integer(primary_key=True, auto_increment=True)
    memory_id = Integer(nullable=False)
    path = String(512, index=True, nullable=False)
    created_at = DateTime(nullable=False)


class MemoryVersion(Model):
    """
    记忆版本模型
    
    存储记忆的历史版本，支持版本回滚和对比。
    
    Attributes:
        id: 主键，自增
        memory_id: 关联的记忆 ID
        version: 版本号，从 1 开始递增
        content: 该版本的内容快照
        changed_at: 变更时间
        change_reason: 变更原因描述
        changed_by: 变更来源 (user/auto/hook/import)
    """
    __tablename__ = "memory_versions"
    
    id = Integer(primary_key=True, auto_increment=True)
    memory_id = Integer(nullable=False, index=True)
    version = Integer(nullable=False)
    content = Text(nullable=False)
    changed_at = DateTime(nullable=False)
    change_reason = Text(default="")
    changed_by = String(20, default="user")


class MemoryRelation(Model):
    """
    记忆关系模型
    
    存储记忆之间的关系，构建知识图谱。
    
    Attributes:
        id: 主键，自增
        source_memory_id: 源记忆 ID
        target_memory_id: 目标记忆 ID
        relation_type: 关系类型，参见 RelationType
        strength: 关系强度 0-1
        created_at: 创建时间
    """
    __tablename__ = "memory_relations"
    
    id = Integer(primary_key=True, auto_increment=True)
    source_memory_id = Integer(nullable=False, index=True)
    target_memory_id = Integer(nullable=False, index=True)
    relation_type = String(30, nullable=False)
    strength = Float(default=0.5)
    created_at = DateTime(nullable=False)


class Session(Model):
    """
    会话记录模型
    
    记录 Claude Code 会话信息，用于会话级别的记忆管理。
    
    Attributes:
        id: 主键，自增
        session_id: 会话唯一标识
        project_dir: 项目目录路径
        project_name: 项目名称
        started_at: 会话开始时间
        ended_at: 会话结束时间
        summary: 会话摘要
        memories_created: 本次会话创建的记忆数
        memories_accessed: 本次会话访问的记忆数
        operations_count: 本次会话的操作次数
    """
    __tablename__ = "sessions"
    
    id = Integer(primary_key=True, auto_increment=True)
    session_id = String(64, unique=True, nullable=False)
    project_dir = String(512)
    project_name = String(255)
    started_at = DateTime(nullable=False)
    ended_at = DateTime()
    summary = Text()
    memories_created = Integer(default=0)
    memories_accessed = Integer(default=0)
    operations_count = Integer(default=0)


class ErrorSolution(Model):
    """
    错误解决方案模型
    
    存储错误模式及其解决方案，支持错误自动匹配和学习。
    
    Attributes:
        id: 主键，自增
        error_pattern: 错误模式，支持正则表达式
        error_type: 错误类型分类
        solution: 解决方案描述
        source: 来源 (learned/manual/imported)
        success_count: 成功应用次数
        failure_count: 应用失败次数
        created_at: 创建时间
        updated_at: 更新时间
    """
    __tablename__ = "error_solutions"
    
    id = Integer(primary_key=True, auto_increment=True)
    error_pattern = Text(nullable=False)
    error_type = String(100)
    solution = Text(nullable=False)
    source = String(20, default="learned")
    success_count = Integer(default=0)
    failure_count = Integer(default=0)
    created_at = DateTime(nullable=False)
    updated_at = DateTime(nullable=False)


_db_initialized = False


def get_db_path() -> str:
    return os.path.join(get_project_plugins_dir(), "memory", "memory.db")

def _compute_hash(content: str) -> str:
    """
    计算内容的 SHA256 哈希值
    
    用于快速比较内容是否变化，避免不必要的版本记录。
    
    Args:
        content: 需要计算哈希的内容字符串
        
    Returns:
        str: 64 位十六进制哈希字符串
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


async def init_db() -> None:
    """
    初始化数据库连接和表结构
    
    创建数据库文件目录（如不存在），初始化数据库连接，
    并创建所有必要的表结构。此函数是幂等的，多次调用不会重复创建。
    
    注意:
        必须在使用任何数据库操作前调用此函数。
        
    Example:
        >>> await init_db()
        >>> # 现在可以安全地进行数据库操作
    """
    global _db_initialized
    
    if _db_initialized:
        return
    
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    config = DatabaseConfig.sqlite(path=db_path)
    await DatabaseConnection.initialize(config)
    
    await Memory.create_table(if_not_exists=True)
    await MemoryPath.create_table(if_not_exists=True)
    await MemoryVersion.create_table(if_not_exists=True)
    await MemoryRelation.create_table(if_not_exists=True)
    await Session.create_table(if_not_exists=True)
    await ErrorSolution.create_table(if_not_exists=True)
    
    _db_initialized = True
    logging.info(f"数据库初始化完成: {db_path}")


async def close_db() -> None:
    """
    关闭数据库连接
    
    释放数据库资源，重置初始化状态。
    通常在程序退出前调用。
    
    Example:
        >>> await close_db()
    """
    global _db_initialized
    if _db_initialized:
        await DatabaseConnection.close()
        _db_initialized = False


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
        
    Example:
        >>> memory = await create_memory(
        ...     uri="project://structure",
        ...     content="项目采用 monorepo 结构",
        ...     priority=1,
        ...     disclosure="When navigating project files"
        ... )
    """
    now = datetime.now()
    content_hash = _compute_hash(content)
    
    existing = await Memory.first(where="uri = ?", params=(uri,))
    
    if existing:
        if existing.content != content:
            await _create_version(existing.id, existing.content, existing.updated_at, "content_update", changed_by)
        
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
        
    Example:
        >>> memory = await get_memory("project://structure")
        >>> if memory:
        ...     print(memory.content)
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
        
    Example:
        >>> # 直接替换内容
        >>> await update_memory("project://config", content="新配置内容")
        
        >>> # 追加内容
        >>> await update_memory("workflow://steps", content="新步骤", append=True)
        
        >>> # 文本替换
        >>> await update_memory("project://config", old_text="旧值", new_text="新值")
    """
    memory = await get_memory(uri, increment_access=False)
    if not memory:
        return None
    
    now = datetime.now()
    
    if content is not None:
        if append:
            new_content = memory.content + "\n" + content
        elif old_text and new_text:
            new_content = memory.content.replace(old_text, new_text)
        else:
            new_content = content
        
        if new_content != memory.content:
            await _create_version(memory.id, memory.content, memory.updated_at, "content_update", changed_by)
            memory.content = new_content
            memory.content_hash = _compute_hash(new_content)
    
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
        
    Example:
        >>> # 软删除（可恢复）
        >>> await delete_memory("task://old-task")
        
        >>> # 硬删除（不可恢复）
        >>> await delete_memory("task://old-task", soft=False)
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
        
    Example:
        >>> # 搜索包含 "config" 的记忆
        >>> memories = await search_memories("config")
        
        >>> # 搜索项目级高优先级记忆
        >>> memories = await search_memories(
        ...     "error",
        ...     uri_prefix="project://",
        ...     priority_max=3
        ... )
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
        
    Example:
        >>> # 列出所有项目级记忆
        >>> memories = await list_memories(uri_prefix="project://")
        
        >>> # 分页获取
        >>> page1 = await list_memories(limit=20, offset=0)
        >>> page2 = await list_memories(limit=20, offset=20)
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
        
    Example:
        >>> # 获取核心记忆（优先级 0-3）
        >>> core_memories = await get_memories_by_priority(3)
        >>> for mem in core_memories:
        ...     print(f"[{mem.priority}] {mem.uri}: {mem.content[:50]}")
    """
    return await Memory.find(
        where="priority <= ? AND status = ?",
        params=(max_priority, MemoryStatus.ACTIVE.value),
        order_by="priority ASC",
    )


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
        
    Example:
        >>> # 设置为核心记忆
        >>> await set_priority("project://structure", 1)
        
        >>> # 设置为普通记忆
        >>> await set_priority("task://notes", 5)
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
        
    Example:
        >>> await deprecate_memory(
        ...     "project://old-config",
        ...     reason="已迁移到新配置系统"
        ... )
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
        
    Example:
        >>> await archive_memory("session://2024-01-15")
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
        
    Example:
        >>> # 恢复已废弃的记忆
        >>> await restore_memory("project://old-config")
    """
    memory = await Memory.first(where="uri = ?", params=(uri,))
    if not memory:
        return None
    
    memory.status = MemoryStatus.ACTIVE.value
    memory.deprecated_at = None
    memory.updated_at = datetime.now()
    await memory.save()
    
    return memory


async def _create_version(
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


async def get_versions(uri: str, limit: int = 10) -> List[MemoryVersion]:
    """
    获取记忆的版本历史
    
    返回指定记忆的所有历史版本，按版本号降序排列。
    
    Args:
        uri: 记忆的唯一标识符
        limit: 返回版本数量限制，默认 10
        
    Returns:
        List[MemoryVersion]: 版本历史列表，最新版本在前
        
    Example:
        >>> versions = await get_versions("project://config")
        >>> for v in versions:
        ...     print(f"v{v.version}: {v.changed_at} - {v.change_reason}")
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
        
    Example:
        >>> v3 = await get_version("project://config", 3)
        >>> if v3:
        ...     print(f"版本 3 内容: {v3.content[:100]}")
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
        
    Example:
        >>> # 回滚到版本 2
        >>> memory = await rollback_to_version("project://config", 2)
        >>> if memory:
        ...     print(f"已回滚，当前内容: {memory.content[:100]}")
    """
    memory = await get_memory(uri, increment_access=False)
    if not memory:
        return None
    
    target_version = await get_version(uri, version)
    if not target_version:
        return None
    
    await _create_version(memory.id, memory.content, memory.updated_at, f"rollback_to_v{version}", changed_by)
    
    memory.content = target_version.content
    memory.content_hash = _compute_hash(target_version.content)
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
        
    Example:
        >>> diff = await diff_versions("project://config", 1, 3)
        >>> if diff:
        ...     v1_content, v3_content = diff
        ...     print(f"版本1: {v1_content[:50]}")
        ...     print(f"版本3: {v3_content[:50]}")
    """
    v1 = await get_version(uri, version1)
    v2 = await get_version(uri, version2)
    
    if not v1 or not v2:
        return None
    
    return (v1.content, v2.content)


async def add_relation(
    source_uri: str,
    target_uri: str,
    relation_type: RelationType,
    strength: float = 0.5,
) -> Optional[MemoryRelation]:
    """
    添加记忆关系
    
    在两条记忆之间建立关系，构建知识图谱。
    如果关系已存在，则更新关系强度。
    
    Args:
        source_uri: 源记忆 URI
        target_uri: 目标记忆 URI
        relation_type: 关系类型，参见 RelationType
        strength: 关系强度 0-1，默认 0.5
        
    Returns:
        Optional[MemoryRelation]: 创建或更新的关系对象，
                                  任一记忆不存在则返回 None
        
    Example:
        >>> # 建立依赖关系
        >>> await add_relation(
        ...     "project://config",
        ...     "project://dependencies",
        ...     RelationType.DEPENDS_ON,
        ...     strength=0.8
        ... )
    """
    source = await Memory.first(where="uri = ?", params=(source_uri,))
    target = await Memory.first(where="uri = ?", params=(target_uri,))
    
    if not source or not target:
        return None
    
    existing = await MemoryRelation.first(
        where="source_memory_id = ? AND target_memory_id = ? AND relation_type = ?",
        params=(source.id, target.id, relation_type.value),
    )
    
    if existing:
        existing.strength = strength
        await existing.save()
        return existing
    
    return await MemoryRelation.create(
        source_memory_id=source.id,
        target_memory_id=target.id,
        relation_type=relation_type.value,
        strength=strength,
        created_at=datetime.now(),
    )


async def get_relations(uri: str, direction: str = "both") -> List[Dict[str, Any]]:
    """
    获取记忆的关系列表
    
    返回与指定记忆相关的所有关系，可选择方向。
    
    Args:
        uri: 记忆的唯一标识符
        direction: 关系方向
            - "out": 只返回出向关系（该记忆指向其他记忆）
            - "in": 只返回入向关系（其他记忆指向该记忆）
            - "both": 返回所有关系（默认）
        
    Returns:
        List[Dict[str, Any]]: 关系信息列表，每项包含:
            - relation_type: 关系类型
            - strength: 关系强度
            - target_uri/source_uri: 相关记忆 URI
            - direction: 方向标识
            
    Example:
        >>> # 获取所有关系
        >>> relations = await get_relations("project://config")
        >>> for rel in relations:
        ...     if rel["direction"] == "out":
        ...         print(f"→ [{rel['relation_type']}] {rel['target_uri']}")
        ...     else:
        ...         print(f"← [{rel['relation_type']}] {rel['source_uri']}")
    """
    memory = await Memory.first(where="uri = ?", params=(uri,))
    if not memory:
        return []
    
    results = []
    
    if direction in ("out", "both"):
        outgoing = await MemoryRelation.find(
            where="source_memory_id = ?",
            params=(memory.id,),
        )
        for rel in outgoing:
            target = await Memory.first(where="id = ?", params=(rel.target_memory_id,))
            if target:
                results.append({
                    "relation_type": rel.relation_type,
                    "strength": rel.strength,
                    "target_uri": target.uri,
                    "direction": "out",
                })
    
    if direction in ("in", "both"):
        incoming = await MemoryRelation.find(
            where="target_memory_id = ?",
            params=(memory.id,),
        )
        for rel in incoming:
            source = await Memory.first(where="id = ?", params=(rel.source_memory_id,))
            if source:
                results.append({
                    "relation_type": rel.relation_type,
                    "strength": rel.strength,
                    "source_uri": source.uri,
                    "direction": "in",
                })
    
    return results


async def remove_relation(source_uri: str, target_uri: str, relation_type: Optional[RelationType] = None) -> bool:
    """
    移除记忆关系
    
    删除两条记忆之间的关系。可指定关系类型，或删除所有关系类型。
    
    Args:
        source_uri: 源记忆 URI
        target_uri: 目标记忆 URI
        relation_type: 可选的关系类型，如不指定则删除所有类型的关系
        
    Returns:
        bool: 成功删除返回 True，关系不存在返回 False
        
    Example:
        >>> # 删除特定类型的关系
        >>> await remove_relation(
        ...     "project://config",
        ...     "project://old-dep",
        ...     RelationType.DEPENDS_ON
        ... )
        
        >>> # 删除所有关系
        >>> await remove_relation("project://config", "project://old-dep")
    """
    source = await Memory.first(where="uri = ?", params=(source_uri,))
    target = await Memory.first(where="uri = ?", params=(target_uri,))
    
    if not source or not target:
        return False
    
    if relation_type:
        count = await MemoryRelation.delete(
            where="source_memory_id = ? AND target_memory_id = ? AND relation_type = ?",
            params=(source.id, target.id, relation_type.value),
        )
    else:
        count = await MemoryRelation.delete(
            where="source_memory_id = ? AND target_memory_id = ?",
            params=(source.id, target.id),
        )
    
    return count > 0


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
        
    Example:
        >>> memory = await create_memory("file://config", "配置说明")
        >>> await add_memory_path(memory.id, "/project/config.yaml")
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
        
    Example:
        >>> paths = await get_memory_paths(memory.id)
        >>> for p in paths:
        ...     print(f"关联路径: {p.path}")
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
        
    Example:
        >>> memories = await find_memories_by_path("config.yaml")
        >>> for mem in memories:
        ...     print(f"相关记忆: {mem.uri}")
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
        Dict[str, Any]: 导出的数据结构，包含:
            - exported_at: 导出时间
            - version: 数据格式版本
            - memories: 记忆列表
            
    Example:
        >>> # 导出所有记忆
        >>> data = await export_memories()
        
        >>> # 导出项目级记忆，包含版本和关系
        >>> data = await export_memories(
        ...     uri_prefix="project://",
        ...     include_versions=True,
        ...     include_relations=True
        ... )
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
            "created_at": memory.created_at.isoformat() if memory.created_at else None,
            "updated_at": memory.updated_at.isoformat() if memory.updated_at else None,
        }
        
        if include_versions:
            versions = await get_versions(memory.uri, limit=100)
            mem_data["versions"] = [
                {
                    "version": v.version,
                    "content": v.content,
                    "changed_at": v.changed_at.isoformat() if v.changed_at else None,
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
            - created: 新创建数量
            - updated: 更新数量
            - skipped: 跳过数量
            - errors: 错误数量
            
    Example:
        >>> with open("backup.json") as f:
        ...     data = json.load(f)
        >>> stats = await import_memories(data, strategy="merge")
        >>> print(f"导入完成: {stats}")
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


async def get_stats() -> Dict[str, Any]:
    """
    获取记忆统计信息
    
    返回记忆系统的整体统计数据，包括数量分布等。
    
    Returns:
        Dict[str, Any]: 统计数据
            - total: 总数（不含已删除）
            - active: 活跃数量
            - deprecated: 已废弃数量
            - archived: 已归档数量
            - by_priority: 按优先级分布
            - by_uri_prefix: 按 URI 前缀分布
            - versions_count: 版本总数
            - relations_count: 关系总数
            
    Example:
        >>> stats = await get_stats()
        >>> print(f"总记忆数: {stats['total']}")
        >>> print(f"活跃记忆: {stats['active']}")
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
            - cleaned: 清理数量
            - archived: 归档数量
            
    Example:
        >>> # 预览清理 30 天未访问的记忆
        >>> stats = await clean_memories(unused_days=30, dry_run=True)
        >>> print(f"将归档 {stats['archived']} 条记忆")
        
        >>> # 执行清理
        >>> stats = await clean_memories(unused_days=30, deprecated_days=7)
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


async def create_session(
    session_id: str,
    project_dir: Optional[str] = None,
    project_name: Optional[str] = None,
) -> Session:
    """
    创建会话记录
    
    创建新的会话记录，用于追踪会话级别的记忆操作。
    
    Args:
        session_id: 会话唯一标识
        project_dir: 项目目录路径
        project_name: 项目名称
        
    Returns:
        Session: 创建的会话记录
        
    Example:
        >>> session = await create_session(
        ...     session_id="session-2024-01-15-001",
        ...     project_dir="/project/path",
        ...     project_name="my-project"
        ... )
    """
    return await Session.create(
        session_id=session_id,
        project_dir=project_dir,
        project_name=project_name,
        started_at=datetime.now(),
        memories_created=0,
        memories_accessed=0,
        operations_count=0,
    )


async def end_session(session_id: str, summary: Optional[str] = None) -> Optional[Session]:
    """
    结束会话记录
    
    结束指定会话，记录结束时间和摘要。
    
    Args:
        session_id: 会话唯一标识
        summary: 会话摘要描述
        
    Returns:
        Optional[Session]: 更新后的会话记录，不存在则返回 None
        
    Example:
        >>> session = await end_session(
        ...     "session-2024-01-15-001",
        ...     summary="完成了配置文件的修改和测试"
        ... )
    """
    session = await Session.first(where="session_id = ?", params=(session_id,))
    if not session:
        return None
    
    session.ended_at = datetime.now()
    session.summary = summary
    await session.save()
    
    return session


async def record_error_solution(
    error_pattern: str,
    solution: str,
    error_type: Optional[str] = None,
    source: str = "learned",
) -> ErrorSolution:
    """
    记录错误解决方案
    
    保存错误模式及其解决方案，用于错误自动匹配和学习。
    如果错误模式已存在，则更新解决方案。
    
    Args:
        error_pattern: 错误模式，支持正则表达式
        solution: 解决方案描述
        error_type: 错误类型分类
        source: 来源标识 (learned/manual/imported)
        
    Returns:
        ErrorSolution: 创建或更新的解决方案记录
        
    Example:
        >>> await record_error_solution(
        ...     error_pattern="ModuleNotFoundError: No module named '(.+)'",
        ...     solution="运行 uv add $1 安装缺失的模块",
        ...     error_type="ImportError",
        ...     source="learned"
        ... )
    """
    existing = await ErrorSolution.first(where="error_pattern = ?", params=(error_pattern,))
    
    if existing:
        existing.solution = solution
        existing.error_type = error_type or existing.error_type
        existing.updated_at = datetime.now()
        await existing.save()
        return existing
    
    return await ErrorSolution.create(
        error_pattern=error_pattern,
        error_type=error_type,
        solution=solution,
        source=source,
        success_count=0,
        failure_count=0,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


async def find_error_solution(error_message: str) -> Optional[ErrorSolution]:
    """
    查找错误解决方案
    
    根据错误信息匹配已记录的解决方案。
    优先返回成功次数最多的匹配方案。
    
    Args:
        error_message: 错误信息文本
        
    Returns:
        Optional[ErrorSolution]: 匹配的解决方案，无匹配则返回 None
        
    Example:
        >>> solution = await find_error_solution(
        ...     "ModuleNotFoundError: No module named 'requests'"
        ... )
        >>> if solution:
        ...     print(f"解决方案: {solution.solution}")
    """
    solutions = await ErrorSolution.find(order_by="success_count DESC")
    
    for solution in solutions:
        import re
        try:
            if re.search(solution.error_pattern, error_message, re.IGNORECASE):
                return solution
        except re.error:
            if solution.error_pattern.lower() in error_message.lower():
                return solution
    
    return None


async def mark_solution_success(solution_id: int, success: bool) -> None:
    """
    标记解决方案的成功或失败
    
    更新解决方案的成功/失败计数，用于评估方案有效性。
    
    Args:
        solution_id: 解决方案 ID
        success: True 表示成功，False 表示失败
        
    Example:
        >>> solution = await find_error_solution(error_msg)
        >>> if solution:
        ...     # 应用解决方案...
        ...     await mark_solution_success(solution.id, success=True)
    """
    solution = await ErrorSolution.first(where="id = ?", params=(solution_id,))
    if solution:
        if success:
            solution.success_count += 1
        else:
            solution.failure_count += 1
        solution.updated_at = datetime.now()
        await solution.save()
