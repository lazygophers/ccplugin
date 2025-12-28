"""任务管理插件的类型定义。

本模块定义了任务管理系统的核心数据类型，包括任务、依赖关系、统计信息等。
所有类型都使用 Pydantic 进行数据验证，确保类型安全。
"""

from datetime import datetime
from enum import Enum
from typing import TypeAlias

from pydantic import BaseModel, Field, field_validator


# 类型别名
TaskID: TypeAlias = str
MetadataDict: TypeAlias = dict[str, str | int | float | bool]
FilterDict: TypeAlias = dict[str, str | int | list[str] | None]


class TaskType(str, Enum):
    """任务类型枚举。

    定义了系统支持的所有任务类型。
    """

    BUG = "bug"
    FEATURE = "feature"
    TASK = "task"
    EPIC = "epic"
    CHORE = "chore"


class TaskStatus(str, Enum):
    """任务状态枚举。

    定义了任务的生命周期状态。
    """

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DEFERRED = "deferred"
    CLOSED = "closed"


class Priority(int, Enum):
    """优先级枚举。

    0-4 五级优先级，数字越小优先级越高。
    """

    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    BACKLOG = 4


class DependencyType(str, Enum):
    """依赖类型枚举。

    定义了任务间依赖关系的类型。
    """

    BLOCKS = "blocks"  # 硬阻塞
    RELATED = "related"  # 软关联
    PARENT_CHILD = "parent-child"  # 层级关系
    DISCOVERED_FROM = "discovered-from"  # 发现关系


class Task(BaseModel):
    """任务完整模型。

    包含任务的所有属性和验证规则。

    Attributes:
        id: 任务唯一标识（格式: tk-xxx）
        title: 任务标题（1-200 字符）
        description: 任务描述
        acceptance_criteria: 验收标准
        task_type: 任务类型
        tags: 标签列表（最多 20 个）
        status: 任务状态
        priority: 优先级（0-4）
        assignee: 负责人
        reporter: 报告人
        created_at: 创建时间
        updated_at: 更新时间
        started_at: 开始时间
        closed_at: 完成时间
        parent_id: 父任务 ID
        dependencies: 依赖任务 ID 列表
        extra_metadata: 扩展元数据
    """

    # 身份
    id: str = Field(
        ..., description="任务唯一标识 (tk-xxx)", pattern=r"^tk-[a-zA-Z0-9]+$"
    )
    title: str = Field(..., min_length=1, max_length=200, description="任务标题")

    # 内容
    description: str = Field(default="", max_length=10000, description="任务描述")
    acceptance_criteria: str | None = Field(default=None, description="验收标准")

    # 分类
    task_type: TaskType = Field(default=TaskType.TASK, description="任务类型")
    tags: list[str] = Field(default_factory=list, max_length=20, description="标签列表")

    # 状态
    status: TaskStatus = Field(default=TaskStatus.OPEN, description="任务状态")
    priority: Priority = Field(default=Priority.MEDIUM, description="优先级")

    # 人员
    assignee: str | None = Field(default=None, max_length=100, description="负责人")
    reporter: str | None = Field(default=None, max_length=100, description="报告人")

    # 时间
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="创建时间"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="更新时间"
    )
    started_at: datetime | None = Field(default=None, description="开始时间")
    closed_at: datetime | None = Field(default=None, description="完成时间")

    # 关系
    parent_id: str | None = Field(
        default=None, pattern=r"^tk-[a-zA-Z0-9]+$", description="父任务 ID"
    )
    dependencies: list[str] = Field(
        default_factory=list, description="依赖任务 ID 列表"
    )

    # 元数据
    extra_metadata: MetadataDict = Field(default_factory=dict, description="扩展元数据")

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """验证标签格式。

        Args:
            v: 标签列表

        Returns:
            清理后的标签列表（去重、转小写、去空）
        """
        return list(set(tag.lower().strip() for tag in v if tag.strip()))

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """验证标题非空。

        Args:
            v: 标题字符串

        Returns:
            清理后的标题

        Raises:
            ValueError: 如果标题为空
        """
        title = v.strip()
        if not title:
            raise ValueError("任务标题不能为空")
        return title

    @field_validator("dependencies", mode="before")
    @classmethod
    def validate_dependencies(cls, v: list[str] | None) -> list[str]:
        """验证依赖列表。

        Args:
            v: 依赖 ID 列表

        Returns:
            验证后的依赖列表
        """
        if v is None:
            return []
        return v

    model_config = {
        "validate_assignment": True,
        "use_enum_values": True,
    }


class BriefTask(BaseModel):
    """任务简化模型。

    用于减少上下文消耗，只包含核心字段。

    Attributes:
        id: 任务 ID
        title: 任务标题
        status: 任务状态
        priority: 优先级
        tags: 标签列表
    """

    id: str
    title: str
    status: TaskStatus
    priority: Priority
    tags: list[str] = Field(default_factory=list)

    @classmethod
    def from_task(cls, task: Task) -> "BriefTask":
        """从完整任务转换。

        Args:
            task: 完整任务对象

        Returns:
            简化任务对象
        """
        return cls(
            id=task.id,
            title=task.title,
            status=task.status,
            priority=task.priority,
            tags=task.tags,
        )


class Dependency(BaseModel):
    """依赖关系模型。

    表示任务间的依赖关系。

    Attributes:
        id: 依赖关系 ID
        task_id: 任务 ID
        depends_on_id: 依赖的任务 ID
        dep_type: 依赖类型
        created_at: 创建时间
        reason: 依赖原因说明
    """

    id: str = Field(..., description="依赖关系 ID", pattern=r"^dep-[a-zA-Z0-9]+$")
    task_id: str = Field(..., description="任务 ID", pattern=r"^tk-[a-zA-Z0-9]+$")
    depends_on_id: str = Field(
        ..., description="依赖的任务 ID", pattern=r"^tk-[a-zA-Z0-9]+$"
    )
    dep_type: DependencyType = Field(
        default=DependencyType.BLOCKS, description="依赖类型"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="创建时间"
    )
    reason: str | None = Field(default=None, max_length=500, description="依赖原因说明")

    model_config = {
        "validate_assignment": True,
        "use_enum_values": True,
    }


class TaskStatistics(BaseModel):
    """任务统计模型。

    提供任务的统计信息和性能指标。

    Attributes:
        total_count: 总任务数
        open_count: 待处理任务数
        in_progress_count: 进行中任务数
        blocked_count: 阻塞任务数
        deferred_count: 延期任务数
        closed_count: 已完成任务数
        bug_count: Bug 数量
        feature_count: 功能数量
        task_count: 任务数量
        epic_count: Epic 数量
        chore_count: 维护任务数量
        critical_count: Critical 任务数
        high_count: High 任务数
        medium_count: Medium 任务数
        low_count: Low 任务数
        backlog_count: Backlog 任务数
        avg_completion_time: 平均完成时间（秒）
        completion_rate: 完成率
        generated_at: 统计生成时间
    """

    # 总览
    total_count: int = Field(..., ge=0, description="总任务数")

    # 状态分布
    open_count: int = Field(default=0, ge=0, description="待处理任务数")
    in_progress_count: int = Field(default=0, ge=0, description="进行中任务数")
    blocked_count: int = Field(default=0, ge=0, description="阻塞任务数")
    deferred_count: int = Field(default=0, ge=0, description="延期任务数")
    closed_count: int = Field(default=0, ge=0, description="已完成任务数")

    # 类型分布
    bug_count: int = Field(default=0, ge=0, description="Bug 数量")
    feature_count: int = Field(default=0, ge=0, description="功能数量")
    task_count: int = Field(default=0, ge=0, description="任务数量")
    epic_count: int = Field(default=0, ge=0, description="Epic 数量")
    chore_count: int = Field(default=0, ge=0, description="维护任务数量")

    # 优先级分布
    critical_count: int = Field(default=0, ge=0, description="Critical 任务数")
    high_count: int = Field(default=0, ge=0, description="High 任务数")
    medium_count: int = Field(default=0, ge=0, description="Medium 任务数")
    low_count: int = Field(default=0, ge=0, description="Low 任务数")
    backlog_count: int = Field(default=0, ge=0, description="Backlog 任务数")

    # 性能指标
    avg_completion_time: float | None = Field(
        default=None, ge=0, description="平均完成时间（秒）"
    )
    completion_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="完成率")

    # 时间范围
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="统计生成时间"
    )


class OperationResult(BaseModel):
    """操作结果模型。

    用于返回简化的操作结果。

    Attributes:
        id: 对象 ID
        action: 操作类型
        message: 操作消息
        changes: 变更列表
    """

    id: str = Field(..., description="对象 ID")
    action: str = Field(..., description="操作类型")
    message: str | None = Field(default=None, description="操作消息")
    changes: list[str] = Field(default_factory=list, description="变更列表")
