"""
数据模型定义

定义记忆系统的所有 ORM 模型。
"""

from enum import Enum

from lib.db import (
    Model,
    Integer,
    String,
    Text,
    DateTime,
    Float,
)


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
