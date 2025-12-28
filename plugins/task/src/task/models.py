"""任务管理插件的 SQLAlchemy 数据库模型。

本模块定义了任务管理系统的数据库模型，使用 SQLAlchemy 2.0 的声明式映射。
所有模型都遵循严格的类型注解要求，支持 mypy --strict 检查。

主要模型：
- TaskModel: 任务表模型
- DependencyModel: 依赖关系表模型
- TaskHistoryModel: 任务历史记录表模型（可选）

索引策略：
- 为常用查询字段创建组合索引
- 支持按状态、优先级、负责人等维度快速查询
"""

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from .types import DependencyType, Priority, TaskStatus, TaskType


class Base(DeclarativeBase):
    """所有模型的基类。

    使用 SQLAlchemy 2.0 的声明式基类。
    """

    pass


class TaskModel(Base):
    """任务表模型。

    对应 Task Pydantic 模型，存储任务的所有核心字段。

    表名: tasks
    主键: id (VARCHAR(50))
    索引:
        - idx_status_priority: (status, priority) - 优先级排序查询
        - idx_assignee_status: (assignee, status) - 负责人任务查询
        - idx_type_status: (task_type, status) - 类型过滤查询
        - idx_created_at: (created_at) - 时间范围查询
        - idx_parent_id: (parent_id) - 子任务查询

    约束:
        - id 格式必须为 tk-xxx
        - title 长度 1-200
        - description 最大 10000
        - priority 范围 0-4
        - assignee/reporter 最大 100
    """

    __tablename__ = "tasks"

    # 身份字段
    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        comment="任务唯一标识 (tk-xxx)",
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="任务标题",
    )

    # 内容字段
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
        comment="任务描述",
    )
    acceptance_criteria: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="验收标准",
    )

    # 分类字段
    task_type: Mapped[str] = mapped_column(
        Enum(TaskType, native_enum=False),
        nullable=False,
        default=TaskType.TASK.value,
        comment="任务类型",
    )
    tags: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=lambda: [],
        comment="标签列表 (JSON 数组)",
    )

    # 状态字段
    status: Mapped[str] = mapped_column(
        Enum(TaskStatus, native_enum=False),
        nullable=False,
        default=TaskStatus.OPEN.value,
        comment="任务状态",
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=Priority.MEDIUM.value,
        comment="优先级 (0-4)",
    )

    # 人员字段
    assignee: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="负责人",
    )
    reporter: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="报告人",
    )

    # 时间字段
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment="更新时间",
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="开始时间",
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        comment="完成时间",
    )

    # 关系字段
    parent_id: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=True,
        comment="父任务 ID",
    )

    # 元数据字段
    extra_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="扩展元数据",
    )

    # 关系定义
    # 父子关系
    parent: Mapped["TaskModel | None"] = relationship(
        "TaskModel",
        remote_side=[id],
        back_populates="children",
        lazy="select",
    )
    children: Mapped[list["TaskModel"]] = relationship(
        "TaskModel",
        back_populates="parent",
        lazy="select",
        cascade="all, delete-orphan",
    )

    # 依赖关系
    dependencies_from: Mapped[list["DependencyModel"]] = relationship(
        "DependencyModel",
        foreign_keys="DependencyModel.task_id",
        back_populates="task",
        lazy="select",
        cascade="all, delete-orphan",
    )
    dependencies_to: Mapped[list["DependencyModel"]] = relationship(
        "DependencyModel",
        foreign_keys="DependencyModel.depends_on_id",
        back_populates="depends_on_task",
        lazy="select",
    )

    # 约束
    __table_args__ = (
        # 格式约束
        CheckConstraint(
            "id LIKE 'tk-%'",
            name="ck_task_id_format",
        ),
        CheckConstraint(
            "length(title) >= 1 AND length(title) <= 200",
            name="ck_task_title_length",
        ),
        CheckConstraint(
            "length(description) <= 10000",
            name="ck_task_description_length",
        ),
        # 优先级约束
        CheckConstraint(
            "priority >= 0 AND priority <= 4",
            name="ck_task_priority_range",
        ),
        # 人员字段长度约束
        CheckConstraint(
            "assignee IS NULL OR length(assignee) <= 100",
            name="ck_task_assignee_length",
        ),
        CheckConstraint(
            "reporter IS NULL OR length(reporter) <= 100",
            name="ck_task_reporter_length",
        ),
        # 组合索引（常用查询优化）
        Index("idx_status_priority", "status", "priority"),
        Index("idx_assignee_status", "assignee", "status"),
        Index("idx_type_status", "task_type", "status"),
        Index("idx_created_at", "created_at"),
        Index("idx_parent_id", "parent_id"),
    )

    def __repr__(self) -> str:
        """返回模型的字符串表示。

        Returns:
            格式化的字符串，包含 id, title, status
        """
        return (
            f"<TaskModel(id={self.id!r}, title={self.title!r}, status={self.status!r})>"
        )


class DependencyModel(Base):
    """依赖关系表模型。

    对应 Dependency Pydantic 模型，存储任务间的依赖关系。

    表名: dependencies
    主键: id (VARCHAR(50))
    外键:
        - task_id -> tasks.id (级联删除)
        - depends_on_id -> tasks.id (级联删除)
    索引:
        - idx_task_id: (task_id) - 查询任务的依赖
        - idx_depends_on_id: (depends_on_id) - 查询被依赖的任务
        - idx_dep_type: (dep_type) - 按类型过滤
    唯一约束:
        - uq_dependency_pair: (task_id, depends_on_id, dep_type) - 防止重复依赖

    约束:
        - id 格式必须为 dep-xxx
        - reason 最大 500 字符
        - 禁止自依赖 (task_id != depends_on_id)
    """

    __tablename__ = "dependencies"

    # 身份字段
    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        comment="依赖关系 ID (dep-xxx)",
    )

    # 关系字段
    task_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        comment="任务 ID",
    )
    depends_on_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        comment="依赖的任务 ID",
    )

    # 类型字段
    dep_type: Mapped[str] = mapped_column(
        Enum(DependencyType, native_enum=False),
        nullable=False,
        default=DependencyType.BLOCKS.value,
        comment="依赖类型",
    )

    # 时间字段
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="创建时间",
    )

    # 说明字段
    reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="依赖原因说明",
    )

    # 关系定义
    task: Mapped["TaskModel"] = relationship(
        "TaskModel",
        foreign_keys=[task_id],
        back_populates="dependencies_from",
        lazy="select",
    )
    depends_on_task: Mapped["TaskModel"] = relationship(
        "TaskModel",
        foreign_keys=[depends_on_id],
        back_populates="dependencies_to",
        lazy="select",
    )

    # 约束
    __table_args__ = (
        # 格式约束
        CheckConstraint(
            "id LIKE 'dep-%'",
            name="ck_dependency_id_format",
        ),
        CheckConstraint(
            "reason IS NULL OR length(reason) <= 500",
            name="ck_dependency_reason_length",
        ),
        # 禁止自依赖
        CheckConstraint(
            "task_id != depends_on_id",
            name="ck_dependency_no_self_reference",
        ),
        # 唯一性约束
        UniqueConstraint(
            "task_id",
            "depends_on_id",
            "dep_type",
            name="uq_dependency_pair",
        ),
        # 索引
        Index("idx_task_id", "task_id"),
        Index("idx_depends_on_id", "depends_on_id"),
        Index("idx_dep_type", "dep_type"),
    )

    def __repr__(self) -> str:
        """返回模型的字符串表示。

        Returns:
            格式化的字符串，包含 id, task_id, depends_on_id, dep_type
        """
        return (
            f"<DependencyModel(id={self.id!r}, "
            f"task_id={self.task_id!r}, "
            f"depends_on_id={self.depends_on_id!r}, "
            f"dep_type={self.dep_type!r})>"
        )


class TaskHistoryModel(Base):
    """任务历史记录表模型（可选功能）。

    记录任务的所有变更历史，用于审计和回溯。

    表名: task_history
    主键: id (自增整数)
    外键: task_id -> tasks.id (级联删除)
    索引:
        - idx_task_id_created_at: (task_id, created_at) - 按时间查询历史

    字段:
        - id: 历史记录 ID
        - task_id: 任务 ID
        - field_name: 变更字段名
        - old_value: 旧值 (JSON)
        - new_value: 新值 (JSON)
        - changed_by: 变更人
        - created_at: 变更时间
        - reason: 变更原因
    """

    __tablename__ = "task_history"

    # 身份字段
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="历史记录 ID",
    )

    # 关系字段
    task_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        comment="任务 ID",
    )

    # 变更字段
    field_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="变更字段名",
    )
    old_value: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="旧值",
    )
    new_value: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        comment="新值",
    )

    # 元信息
    changed_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="变更人",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="变更时间",
    )
    reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="变更原因",
    )

    # 关系定义
    task: Mapped["TaskModel"] = relationship(
        "TaskModel",
        lazy="select",
    )

    # 约束
    __table_args__ = (
        # 索引
        Index("idx_task_id_created_at", "task_id", "created_at"),
        Index("idx_changed_by", "changed_by"),
    )

    def __repr__(self) -> str:
        """返回模型的字符串表示。

        Returns:
            格式化的字符串，包含 id, task_id, field_name
        """
        return (
            f"<TaskHistoryModel(id={self.id}, "
            f"task_id={self.task_id!r}, "
            f"field_name={self.field_name!r})>"
        )


# 统计视图模型（可选，用于优化统计查询）
class TaskStatisticsView(Base):
    """任务统计视图模型（可选）。

    基于数据库视图的统计查询优化。
    在 v0.5.0 调度与报表阶段可能使用。

    注意：这是一个只读视图，不支持 INSERT/UPDATE/DELETE。
    """

    __tablename__ = "task_statistics_view"
    __table_args__ = {"info": {"is_view": True}}

    # 聚合字段
    status: Mapped[str] = mapped_column(String(50), primary_key=True)
    task_type: Mapped[str] = mapped_column(String(50), primary_key=True)
    priority: Mapped[int] = mapped_column(Integer, primary_key=True)
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_completion_time: Mapped[float | None] = mapped_column(Float, nullable=True)

    def __repr__(self) -> str:
        """返回模型的字符串表示。

        Returns:
            格式化的字符串，包含统计维度和计数
        """
        return (
            f"<TaskStatisticsView(status={self.status!r}, "
            f"type={self.task_type!r}, "
            f"priority={self.priority}, "
            f"count={self.count})>"
        )
