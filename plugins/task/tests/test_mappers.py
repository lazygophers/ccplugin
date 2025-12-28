"""Mapper 层单元测试。

测试 Pydantic 模型和 SQLAlchemy 模型之间的转换。
"""

from datetime import datetime

import pytest

from task.mappers import (
    MappingError,
    to_brief_task,
    to_brief_tasks,
    to_dependencies,
    to_dependency,
    to_dependency_model,
    to_task,
    to_task_model,
    to_tasks,
    to_task_with_dependencies,
)
from task.models import DependencyModel, TaskModel
from task.repository import DependencyRepository, TaskRepository
from task.types import (
    Dependency,
    DependencyType,
    Priority,
    Task,
    TaskStatus,
    TaskType,
)


class TestTaskMapping:
    """Task 映射测试类。"""

    def test_to_task(self, task_repo: TaskRepository, sample_task_data: dict) -> None:
        """测试 TaskModel → Task 转换。"""
        # 创建 TaskModel
        task_model = task_repo.create(sample_task_data)

        # 转换为 Task
        task = to_task(task_model)

        assert isinstance(task, Task)
        assert task.id == task_model.id
        assert task.title == task_model.title
        assert task.description == task_model.description
        assert task.task_type == TaskType(task_model.task_type)
        assert task.status == TaskStatus(task_model.status)
        assert task.priority == Priority(task_model.priority)

    def test_to_task_with_tags(self, task_repo: TaskRepository, sample_task_data: dict) -> None:
        """测试带标签的任务转换。"""
        task_model = task_repo.create(sample_task_data)
        task = to_task(task_model)

        assert isinstance(task.tags, list)
        assert "test" in task.tags
        assert "sample" in task.tags

    def test_to_task_model(self) -> None:
        """测试 Task → TaskModel 数据字典转换。"""
        task = Task(
            id="tk-test001",
            title="测试任务",
            description="测试描述",
            task_type=TaskType.TASK,
            status=TaskStatus.OPEN,
            priority=Priority.MEDIUM,
        )

        task_dict = to_task_model(task)

        assert task_dict["id"] == task.id
        assert task_dict["title"] == task.title
        assert task_dict["description"] == task.description
        # 枚举可能已经是字符串值
        assert task_dict["task_type"] == (
            task.task_type.value if isinstance(task.task_type, TaskType) else task.task_type
        )
        assert task_dict["status"] == (
            task.status.value if isinstance(task.status, TaskStatus) else task.status
        )
        assert task_dict["priority"] == (
            task.priority.value if isinstance(task.priority, Priority) else task.priority
        )

    def test_to_brief_task(self, task_repo: TaskRepository, sample_task_data: dict) -> None:
        """测试 TaskModel → BriefTask 转换。"""
        task_model = task_repo.create(sample_task_data)
        brief_task = to_brief_task(task_model)

        assert brief_task.id == task_model.id
        assert brief_task.title == task_model.title
        assert brief_task.status == TaskStatus(task_model.status)
        assert brief_task.priority == Priority(task_model.priority)
        assert isinstance(brief_task.tags, list)

    def test_to_tasks_batch(self, task_repo: TaskRepository, sample_task_data: dict) -> None:
        """测试批量 TaskModel → Task 转换。"""
        # 创建多个任务
        task_models = []
        for i in range(3):
            data = sample_task_data.copy()
            data["id"] = f"tk-test{i:03d}"
            task_models.append(task_repo.create(data))

        # 批量转换
        tasks = to_tasks(task_models)

        assert len(tasks) == 3
        assert all(isinstance(t, Task) for t in tasks)

    def test_to_brief_tasks_batch(self, task_repo: TaskRepository, sample_task_data: dict) -> None:
        """测试批量 TaskModel → BriefTask 转换。"""
        # 创建多个任务
        task_models = []
        for i in range(3):
            data = sample_task_data.copy()
            data["id"] = f"tk-test{i:03d}"
            task_models.append(task_repo.create(data))

        # 批量转换
        brief_tasks = to_brief_tasks(task_models)

        assert len(brief_tasks) == 3
        for bt in brief_tasks:
            assert hasattr(bt, "id")
            assert hasattr(bt, "title")
            assert hasattr(bt, "status")
            assert hasattr(bt, "priority")


class TestDependencyMapping:
    """Dependency 映射测试类。"""

    def test_to_dependency(
        self,
        dep_repo: DependencyRepository,
        task_repo: TaskRepository,
        sample_task_data: dict,
        sample_dependency_data: dict,
    ) -> None:
        """测试 DependencyModel → Dependency 转换。"""
        # 创建任务
        for task_id in ["tk-test001", "tk-test002"]:
            data = sample_task_data.copy()
            data["id"] = task_id
            task_repo.create(data)

        # 创建依赖
        dep_model = dep_repo.create(sample_dependency_data)

        # 转换
        dep = to_dependency(dep_model)

        assert isinstance(dep, Dependency)
        assert dep.id == dep_model.id
        assert dep.task_id == dep_model.task_id
        assert dep.depends_on_id == dep_model.depends_on_id
        assert dep.dep_type == DependencyType(dep_model.dep_type)

    def test_to_dependency_model(self) -> None:
        """测试 Dependency → DependencyModel 数据字典转换。"""
        dep = Dependency(
            id="dep-test001",
            task_id="tk-test001",
            depends_on_id="tk-test002",
            dep_type=DependencyType.BLOCKS,
            created_at=datetime.utcnow(),
            reason="测试原因",
        )

        dep_dict = to_dependency_model(dep)

        assert dep_dict["id"] == dep.id
        assert dep_dict["task_id"] == dep.task_id
        assert dep_dict["depends_on_id"] == dep.depends_on_id
        # 枚举可能已经是字符串值
        assert dep_dict["dep_type"] == (
            dep.dep_type.value if isinstance(dep.dep_type, DependencyType) else dep.dep_type
        )
        assert dep_dict["reason"] == dep.reason

    def test_to_dependencies_batch(
        self,
        dep_repo: DependencyRepository,
        task_repo: TaskRepository,
        sample_task_data: dict,
    ) -> None:
        """测试批量 DependencyModel → Dependency 转换。"""
        # 创建任务
        for i in range(3):
            data = sample_task_data.copy()
            data["id"] = f"tk-test{i:03d}"
            task_repo.create(data)

        # 创建依赖
        dep_models = []
        for i in range(2):
            dep_data = {
                "id": f"dep-test{i:03d}",
                "task_id": "tk-test000",
                "depends_on_id": f"tk-test{i+1:03d}",
                "dep_type": "blocks",
            }
            dep_models.append(dep_repo.create(dep_data))

        # 批量转换
        deps = to_dependencies(dep_models)

        assert len(deps) == 2
        assert all(isinstance(d, Dependency) for d in deps)


class TestTaskWithDependencies:
    """带依赖关系的任务转换测试。"""

    def test_to_task_with_dependencies(
        self,
        task_repo: TaskRepository,
        dep_repo: DependencyRepository,
        sample_task_data: dict,
    ) -> None:
        """测试带依赖信息的任务转换。"""
        # 创建 3 个任务
        for i in range(3):
            data = sample_task_data.copy()
            data["id"] = f"tk-test{i:03d}"
            task_repo.create(data)

        # 创建依赖: task000 依赖 task001 和 task002
        dep_repo.create(
            {
                "id": "dep-test001",
                "task_id": "tk-test000",
                "depends_on_id": "tk-test001",
                "dep_type": "blocks",
            }
        )
        dep_repo.create(
            {
                "id": "dep-test002",
                "task_id": "tk-test000",
                "depends_on_id": "tk-test002",
                "dep_type": "blocks",
            }
        )

        # 获取任务（预加载依赖）
        task_model = task_repo.get_by_id_with_relations("tk-test000")
        assert task_model is not None

        # 转换
        task = to_task_with_dependencies(task_model)

        assert len(task.dependencies) == 2
        assert "tk-test001" in task.dependencies
        assert "tk-test002" in task.dependencies


class TestEnumConversion:
    """枚举类型转换测试。"""

    def test_task_type_conversion(self) -> None:
        """测试 TaskType 枚举转换。"""
        task = Task(
            id="tk-test001",
            title="测试",
            task_type=TaskType.BUG,
            status=TaskStatus.OPEN,
            priority=Priority.HIGH,
        )

        task_dict = to_task_model(task)

        # 枚举应转换为字符串值
        assert task_dict["task_type"] == "bug"
        assert isinstance(task_dict["task_type"], str)

    def test_status_conversion(self) -> None:
        """测试 TaskStatus 枚举转换。"""
        task = Task(
            id="tk-test001",
            title="测试",
            task_type=TaskType.TASK,
            status=TaskStatus.IN_PROGRESS,
            priority=Priority.MEDIUM,
        )

        task_dict = to_task_model(task)
        assert task_dict["status"] == "in_progress"

    def test_priority_conversion(self) -> None:
        """测试 Priority 枚举转换。"""
        task = Task(
            id="tk-test001",
            title="测试",
            task_type=TaskType.TASK,
            status=TaskStatus.OPEN,
            priority=Priority.CRITICAL,
        )

        task_dict = to_task_model(task)
        assert task_dict["priority"] == 0
        assert isinstance(task_dict["priority"], int)


class TestEdgeCases:
    """边界情况测试。"""

    def test_empty_tags_conversion(self, task_repo: TaskRepository, sample_task_data: dict) -> None:
        """测试空标签列表转换。"""
        data = sample_task_data.copy()
        data["tags"] = []
        task_model = task_repo.create(data)

        task = to_task(task_model)
        assert task.tags == []

    def test_null_fields_conversion(self, task_repo: TaskRepository, sample_task_data: dict) -> None:
        """测试 NULL 字段转换。"""
        data = sample_task_data.copy()
        data["assignee"] = None
        data["reporter"] = None
        task_model = task_repo.create(data)

        task = to_task(task_model)
        assert task.assignee is None
        assert task.reporter is None

    def test_metadata_conversion(self, task_repo: TaskRepository, sample_task_data: dict) -> None:
        """测试元数据字段转换。"""
        data = sample_task_data.copy()
        data["extra_metadata"] = {"key1": "value1", "key2": 123}
        task_model = task_repo.create(data)

        task = to_task(task_model)
        assert isinstance(task.extra_metadata, dict)
        assert task.extra_metadata["key1"] == "value1"
        assert task.extra_metadata["key2"] == 123
