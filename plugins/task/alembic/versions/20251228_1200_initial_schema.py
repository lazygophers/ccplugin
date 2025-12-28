"""Initial database schema.

创建任务管理系统的初始数据库架构。

包含表：
- tasks: 任务表
- dependencies: 依赖关系表
- task_history: 任务历史记录表

Revision ID: initial_schema
Revises:
Create Date: 2025-12-28 12:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import JSON

# revision identifiers, used by Alembic.
revision: str = "initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """应用迁移：创建初始数据库架构。

    创建所有核心表和索引。
    """
    # 创建 tasks 表
    op.create_table(
        "tasks",
        # 身份字段
        sa.Column("id", sa.String(50), primary_key=True, comment="任务唯一标识 (tk-xxx)"),
        sa.Column("title", sa.String(200), nullable=False, comment="任务标题"),
        # 内容字段
        sa.Column("description", sa.Text(), nullable=False, default="", comment="任务描述"),
        sa.Column("acceptance_criteria", sa.Text(), nullable=True, comment="验收标准"),
        # 分类字段
        sa.Column(
            "task_type",
            sa.String(20),
            nullable=False,
            default="task",
            comment="任务类型",
        ),
        sa.Column("tags", JSON, nullable=False, default=list, comment="标签列表"),
        # 状态字段
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            default="open",
            comment="任务状态",
        ),
        sa.Column("priority", sa.Integer(), nullable=False, default=2, comment="优先级 (0-4)"),
        # 人员字段
        sa.Column("assignee", sa.String(100), nullable=True, comment="负责人"),
        sa.Column("reporter", sa.String(100), nullable=True, comment="报告人"),
        # 时间字段
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            comment="创建时间",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            comment="更新时间",
        ),
        sa.Column("started_at", sa.DateTime(), nullable=True, comment="开始时间"),
        sa.Column("closed_at", sa.DateTime(), nullable=True, comment="完成时间"),
        # 关系字段
        sa.Column("parent_id", sa.String(50), nullable=True, comment="父任务 ID"),
        # 元数据字段
        sa.Column("extra_metadata", JSON, nullable=False, default=dict, comment="扩展元数据"),
        # 约束
        sa.CheckConstraint("id LIKE 'tk-%'", name="ck_task_id_format"),
        sa.CheckConstraint(
            "length(title) >= 1 AND length(title) <= 200",
            name="ck_task_title_length",
        ),
        sa.CheckConstraint(
            "length(description) <= 10000",
            name="ck_task_description_length",
        ),
        sa.CheckConstraint("priority >= 0 AND priority <= 4", name="ck_task_priority_range"),
        sa.CheckConstraint(
            "assignee IS NULL OR length(assignee) <= 100",
            name="ck_task_assignee_length",
        ),
        sa.CheckConstraint(
            "reporter IS NULL OR length(reporter) <= 100",
            name="ck_task_reporter_length",
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["tasks.id"],
            name="fk_tasks_parent_id",
            ondelete="CASCADE",
        ),
    )

    # 创建 tasks 表索引
    op.create_index("idx_status_priority", "tasks", ["status", "priority"])
    op.create_index("idx_assignee_status", "tasks", ["assignee", "status"])
    op.create_index("idx_type_status", "tasks", ["task_type", "status"])
    op.create_index("idx_created_at", "tasks", ["created_at"])
    op.create_index("idx_parent_id", "tasks", ["parent_id"])

    # 创建 dependencies 表
    op.create_table(
        "dependencies",
        # 身份字段
        sa.Column("id", sa.String(50), primary_key=True, comment="依赖关系 ID (dep-xxx)"),
        # 关系字段
        sa.Column("task_id", sa.String(50), nullable=False, comment="任务 ID"),
        sa.Column("depends_on_id", sa.String(50), nullable=False, comment="依赖的任务 ID"),
        # 类型字段
        sa.Column(
            "dep_type",
            sa.String(20),
            nullable=False,
            default="blocks",
            comment="依赖类型",
        ),
        # 时间字段
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            comment="创建时间",
        ),
        # 说明字段
        sa.Column("reason", sa.String(500), nullable=True, comment="依赖原因说明"),
        # 约束
        sa.CheckConstraint("id LIKE 'dep-%'", name="ck_dependency_id_format"),
        sa.CheckConstraint(
            "reason IS NULL OR length(reason) <= 500",
            name="ck_dependency_reason_length",
        ),
        sa.CheckConstraint(
            "task_id != depends_on_id",
            name="ck_dependency_no_self_reference",
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            name="fk_dependencies_task_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["depends_on_id"],
            ["tasks.id"],
            name="fk_dependencies_depends_on_id",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "task_id",
            "depends_on_id",
            "dep_type",
            name="uq_dependency_pair",
        ),
    )

    # 创建 dependencies 表索引
    op.create_index("idx_task_id", "dependencies", ["task_id"])
    op.create_index("idx_depends_on_id", "dependencies", ["depends_on_id"])
    op.create_index("idx_dep_type", "dependencies", ["dep_type"])

    # 创建 task_history 表
    op.create_table(
        "task_history",
        # 身份字段
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
            comment="历史记录 ID",
        ),
        # 关系字段
        sa.Column("task_id", sa.String(50), nullable=False, comment="任务 ID"),
        # 变更字段
        sa.Column("field_name", sa.String(100), nullable=False, comment="变更字段名"),
        sa.Column("old_value", JSON, nullable=True, comment="旧值"),
        sa.Column("new_value", JSON, nullable=True, comment="新值"),
        # 元信息
        sa.Column("changed_by", sa.String(100), nullable=True, comment="变更人"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            comment="变更时间",
        ),
        sa.Column("reason", sa.String(500), nullable=True, comment="变更原因"),
        # 约束
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["tasks.id"],
            name="fk_task_history_task_id",
            ondelete="CASCADE",
        ),
    )

    # 创建 task_history 表索引
    op.create_index("idx_task_id_created_at", "task_history", ["task_id", "created_at"])
    op.create_index("idx_changed_by", "task_history", ["changed_by"])


def downgrade() -> None:
    """回滚迁移：删除所有表。

    删除顺序：先删除依赖表，再删除主表。
    """
    # 删除 task_history 表
    op.drop_index("idx_changed_by", "task_history")
    op.drop_index("idx_task_id_created_at", "task_history")
    op.drop_table("task_history")

    # 删除 dependencies 表
    op.drop_index("idx_dep_type", "dependencies")
    op.drop_index("idx_depends_on_id", "dependencies")
    op.drop_index("idx_task_id", "dependencies")
    op.drop_table("dependencies")

    # 删除 tasks 表
    op.drop_index("idx_parent_id", "tasks")
    op.drop_index("idx_created_at", "tasks")
    op.drop_index("idx_type_status", "tasks")
    op.drop_index("idx_assignee_status", "tasks")
    op.drop_index("idx_status_priority", "tasks")
    op.drop_table("tasks")
