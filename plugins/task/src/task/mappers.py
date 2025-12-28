"""数据映射器。

本模块实现 Pydantic 模型和 SQLAlchemy 模型之间的双向转换。
确保数据在不同层之间传递时的类型安全和数据完整性。

映射关系：
- TaskModel (SQLAlchemy) ↔ Task (Pydantic)
- DependencyModel (SQLAlchemy) ↔ Dependency (Pydantic)
- TaskModel (SQLAlchemy) → BriefTask (Pydantic)

主要函数：
- to_task: TaskModel → Task
- to_task_model: Task → TaskModel
- to_dependency: DependencyModel → Dependency
- to_dependency_model: Dependency → DependencyModel
- to_brief_task: TaskModel → BriefTask
"""

from typing import Any, Sequence

from .models import DependencyModel, TaskModel
from .types import (
    BriefTask,
    Dependency,
    DependencyType,
    MetadataDict,
    Priority,
    Task,
    TaskStatus,
    TaskType,
)


class MappingError(Exception):
    """映射错误。"""

    pass


# ============================================================================
# Task 映射
# ============================================================================


def to_task(task_model: TaskModel) -> Task:
    """将 TaskModel 转换为 Task。

    Args:
        task_model: SQLAlchemy TaskModel 实例

    Returns:
        Pydantic Task 实例

    Raises:
        MappingError: 转换失败
    """
    try:
        # 处理 tags（SQLite JSON 存储为 list 或 dict）
        tags = task_model.tags
        if isinstance(tags, dict):
            # 如果是 dict，尝试提取列表
            tags = list(tags.values()) if tags else []
        elif not isinstance(tags, list):
            tags = []

        # 处理 extra_metadata
        extra_metadata: MetadataDict = (
            task_model.extra_metadata
            if isinstance(task_model.extra_metadata, dict)
            else {}
        )

        return Task(
            # 身份
            id=task_model.id,
            title=task_model.title,
            # 内容
            description=task_model.description,
            acceptance_criteria=task_model.acceptance_criteria,
            # 分类
            task_type=TaskType(task_model.task_type),
            tags=tags,
            # 状态
            status=TaskStatus(task_model.status),
            priority=Priority(task_model.priority),
            # 人员
            assignee=task_model.assignee,
            reporter=task_model.reporter,
            # 时间
            created_at=task_model.created_at,
            updated_at=task_model.updated_at,
            started_at=task_model.started_at,
            closed_at=task_model.closed_at,
            # 关系
            parent_id=task_model.parent_id,
            dependencies=[],  # 依赖关系需要单独查询
            # 元数据
            extra_metadata=extra_metadata,
        )
    except Exception as e:
        raise MappingError(f"TaskModel → Task 转换失败: {e}") from e


def to_task_with_dependencies(task_model: TaskModel) -> Task:
    """将 TaskModel 转换为 Task（含依赖信息）。

    Args:
        task_model: SQLAlchemy TaskModel 实例（需预加载依赖）

    Returns:
        Pydantic Task 实例（含依赖列表）

    Raises:
        MappingError: 转换失败
    """
    try:
        task = to_task(task_model)

        # 提取依赖任务 ID
        if hasattr(task_model, "dependencies_from"):
            task.dependencies = [
                dep.depends_on_id for dep in task_model.dependencies_from
            ]

        return task
    except Exception as e:
        raise MappingError(f"TaskModel → Task 转换失败（含依赖）: {e}") from e


def to_task_model(task: Task) -> dict[str, Any]:
    """将 Task 转换为 TaskModel 数据字典。

    注意：返回字典而非 TaskModel 实例，以便 Repository 层灵活使用。

    Args:
        task: Pydantic Task 实例

    Returns:
        TaskModel 数据字典

    Raises:
        MappingError: 转换失败
    """
    try:
        return {
            # 身份
            "id": task.id,
            "title": task.title,
            # 内容
            "description": task.description,
            "acceptance_criteria": task.acceptance_criteria,
            # 分类
            "task_type": (
                task.task_type.value
                if isinstance(task.task_type, TaskType)
                else task.task_type
            ),
            "tags": task.tags,  # 直接存储为 JSON 数组
            # 状态
            "status": (
                task.status.value
                if isinstance(task.status, TaskStatus)
                else task.status
            ),
            "priority": (
                task.priority.value
                if isinstance(task.priority, Priority)
                else task.priority
            ),
            # 人员
            "assignee": task.assignee,
            "reporter": task.reporter,
            # 时间
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "started_at": task.started_at,
            "closed_at": task.closed_at,
            # 关系
            "parent_id": task.parent_id,
            # dependencies 字段不存储在 tasks 表
            # 元数据
            "extra_metadata": task.extra_metadata,
        }
    except Exception as e:
        raise MappingError(f"Task → TaskModel 转换失败: {e}") from e


def to_brief_task(task_model: TaskModel) -> BriefTask:
    """将 TaskModel 转换为 BriefTask。

    用于减少上下文消耗，只返回核心字段。

    Args:
        task_model: SQLAlchemy TaskModel 实例

    Returns:
        Pydantic BriefTask 实例

    Raises:
        MappingError: 转换失败
    """
    try:
        # 处理 tags
        tags = task_model.tags
        if isinstance(tags, dict):
            tags = list(tags.values()) if tags else []
        elif not isinstance(tags, list):
            tags = []

        return BriefTask(
            id=task_model.id,
            title=task_model.title,
            status=TaskStatus(task_model.status),
            priority=Priority(task_model.priority),
            tags=tags,
        )
    except Exception as e:
        raise MappingError(f"TaskModel → BriefTask 转换失败: {e}") from e


# ============================================================================
# Dependency 映射
# ============================================================================


def to_dependency(dep_model: DependencyModel) -> Dependency:
    """将 DependencyModel 转换为 Dependency。

    Args:
        dep_model: SQLAlchemy DependencyModel 实例

    Returns:
        Pydantic Dependency 实例

    Raises:
        MappingError: 转换失败
    """
    try:
        return Dependency(
            id=dep_model.id,
            task_id=dep_model.task_id,
            depends_on_id=dep_model.depends_on_id,
            dep_type=DependencyType(dep_model.dep_type),
            created_at=dep_model.created_at,
            reason=dep_model.reason,
        )
    except Exception as e:
        raise MappingError(f"DependencyModel → Dependency 转换失败: {e}") from e


def to_dependency_model(dependency: Dependency) -> dict[str, Any]:
    """将 Dependency 转换为 DependencyModel 数据字典。

    注意：返回字典而非 DependencyModel 实例，以便 Repository 层灵活使用。

    Args:
        dependency: Pydantic Dependency 实例

    Returns:
        DependencyModel 数据字典

    Raises:
        MappingError: 转换失败
    """
    try:
        return {
            "id": dependency.id,
            "task_id": dependency.task_id,
            "depends_on_id": dependency.depends_on_id,
            "dep_type": (
                dependency.dep_type.value
                if isinstance(dependency.dep_type, DependencyType)
                else dependency.dep_type
            ),
            "created_at": dependency.created_at,
            "reason": dependency.reason,
        }
    except Exception as e:
        raise MappingError(f"Dependency → DependencyModel 转换失败: {e}") from e


# ============================================================================
# 批量转换工具
# ============================================================================


def to_tasks(task_models: Sequence[TaskModel]) -> list[Task]:
    """批量将 TaskModel 转换为 Task。

    Args:
        task_models: TaskModel 实例序列

    Returns:
        Task 列表

    Raises:
        MappingError: 转换失败
    """
    try:
        return [to_task(task_model) for task_model in task_models]
    except Exception as e:
        raise MappingError(f"批量 TaskModel → Task 转换失败: {e}") from e


def to_brief_tasks(task_models: Sequence[TaskModel]) -> list[BriefTask]:
    """批量将 TaskModel 转换为 BriefTask。

    Args:
        task_models: TaskModel 实例序列

    Returns:
        BriefTask 列表

    Raises:
        MappingError: 转换失败
    """
    try:
        return [to_brief_task(task_model) for task_model in task_models]
    except Exception as e:
        raise MappingError(f"批量 TaskModel → BriefTask 转换失败: {e}") from e


def to_dependencies(dep_models: Sequence[DependencyModel]) -> list[Dependency]:
    """批量将 DependencyModel 转换为 Dependency。

    Args:
        dep_models: DependencyModel 实例序列

    Returns:
        Dependency 列表

    Raises:
        MappingError: 转换失败
    """
    try:
        return [to_dependency(dep_model) for dep_model in dep_models]
    except Exception as e:
        raise MappingError(f"批量 DependencyModel → Dependency 转换失败: {e}") from e


# ============================================================================
# 辅助函数
# ============================================================================


def update_task_model_from_dict(
    task_model: TaskModel,
    update_data: dict[str, Any],
) -> None:
    """从字典更新 TaskModel 实例。

    Args:
        task_model: 要更新的 TaskModel 实例
        update_data: 更新数据字典

    Raises:
        MappingError: 更新失败
    """
    try:
        # 仅更新允许的字段
        allowed_fields = {
            "title",
            "description",
            "acceptance_criteria",
            "task_type",
            "tags",
            "status",
            "priority",
            "assignee",
            "reporter",
            "started_at",
            "closed_at",
            "parent_id",
            "extra_metadata",
        }

        for key, value in update_data.items():
            if key in allowed_fields:
                # 枚举类型需要转换为值
                if key in ["task_type", "status", "priority"]:
                    if isinstance(value, (TaskType, TaskStatus, Priority)):
                        value = value.value
                setattr(task_model, key, value)

    except Exception as e:
        raise MappingError(f"更新 TaskModel 失败: {e}") from e


def extract_dependency_ids(task: Task) -> list[str]:
    """从 Task 提取依赖任务 ID 列表。

    Args:
        task: Pydantic Task 实例

    Returns:
        依赖任务 ID 列表
    """
    return task.dependencies if task.dependencies else []


def merge_task_updates(
    original: Task,
    updates: dict[str, Any],
) -> dict[str, Any]:
    """合并任务更新数据。

    将部分更新数据与原始任务合并，返回完整的数据字典。

    Args:
        original: 原始 Task 实例
        updates: 更新数据字典

    Returns:
        合并后的数据字典
    """
    # 先转换原始数据为字典
    base_data = to_task_model(original)

    # 合并更新
    base_data.update(updates)

    return base_data
