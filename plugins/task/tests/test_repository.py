"""Repository 层单元测试。

测试 TaskRepository, DependencyRepository, QueryBuilder 和 TransactionManager。
"""

from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from task.repository import (
    DependencyError,
    DependencyRepository,
    QueryBuilder,
    TaskNotFoundError,
    TaskRepository,
    TransactionManager,
)


class TestTaskRepository:
    """TaskRepository 测试类。"""

    def test_create_task(self, task_repo: TaskRepository, sample_task_data: dict) -> None:
        """测试创建任务。"""
        task = task_repo.create(sample_task_data)

        assert task.id == sample_task_data["id"]
        assert task.title == sample_task_data["title"]
        assert task.description == sample_task_data["description"]
        assert task.task_type == sample_task_data["task_type"]
        assert task.priority == sample_task_data["priority"]
        assert task.status == sample_task_data["status"]

    def test_create_task_duplicate_id(
        self, task_repo: TaskRepository, sample_task_data: dict
    ) -> None:
        """测试创建重复 ID 的任务。"""
        task_repo.create(sample_task_data)

        # 尝试创建相同 ID 的任务应失败
        with pytest.raises(Exception):  # RepositoryError or IntegrityError
            task_repo.create(sample_task_data)

    def test_get_by_id(self, task_repo: TaskRepository, sample_task_data: dict) -> None:
        """测试根据 ID 获取任务。"""
        created = task_repo.create(sample_task_data)

        task = task_repo.get_by_id(created.id)
        assert task is not None
        assert task.id == created.id
        assert task.title == created.title

    def test_get_by_id_not_found(self, task_repo: TaskRepository) -> None:
        """测试获取不存在的任务。"""
        task = task_repo.get_by_id("tk-notexist")
        assert task is None

    def test_list_tasks_all(self, task_repo: TaskRepository, sample_task_data: dict) -> None:
        """测试列出所有任务。"""
        # 创建多个任务
        for i in range(5):
            data = sample_task_data.copy()
            data["id"] = f"tk-test{i:03d}"
            data["title"] = f"任务 {i}"
            task_repo.create(data)

        tasks = task_repo.list_tasks()
        assert len(tasks) == 5

    def test_list_tasks_with_filters(
        self, task_repo: TaskRepository, sample_task_data: dict
    ) -> None:
        """测试带过滤条件的任务列表。"""
        # 创建不同状态的任务
        for i, status in enumerate(["open", "in_progress", "closed"]):
            data = sample_task_data.copy()
            data["id"] = f"tk-test{i:03d}"
            data["status"] = status
            task_repo.create(data)

        # 测试状态过滤
        open_tasks = task_repo.list_tasks(filters={"status": "open"})
        assert len(open_tasks) == 1
        assert open_tasks[0].status == "open"

        in_progress_tasks = task_repo.list_tasks(filters={"status": "in_progress"})
        assert len(in_progress_tasks) == 1

    def test_list_tasks_with_limit(
        self, task_repo: TaskRepository, sample_task_data: dict
    ) -> None:
        """测试任务列表限制数量。"""
        # 创建 10 个任务
        for i in range(10):
            data = sample_task_data.copy()
            data["id"] = f"tk-test{i:03d}"
            task_repo.create(data)

        tasks = task_repo.list_tasks(limit=5)
        assert len(tasks) == 5

    def test_update_task(self, task_repo: TaskRepository, sample_task_data: dict) -> None:
        """测试更新任务。"""
        created = task_repo.create(sample_task_data)

        # 更新任务
        update_data = {
            "title": "更新后的标题",
            "status": "in_progress",
            "priority": 0,
        }
        updated = task_repo.update(created.id, update_data)

        assert updated.title == "更新后的标题"
        assert updated.status == "in_progress"
        assert updated.priority == 0
        # 允许相等，因为可能在同一毫秒内完成
        assert updated.updated_at >= created.updated_at

    def test_update_task_not_found(self, task_repo: TaskRepository) -> None:
        """测试更新不存在的任务。"""
        with pytest.raises(TaskNotFoundError):
            task_repo.update("tk-notexist", {"title": "测试"})

    def test_delete_task(self, task_repo: TaskRepository, sample_task_data: dict) -> None:
        """测试删除任务。"""
        created = task_repo.create(sample_task_data)

        task_repo.delete(created.id)

        # 确认删除成功
        task = task_repo.get_by_id(created.id)
        assert task is None

    def test_delete_task_not_found(self, task_repo: TaskRepository) -> None:
        """测试删除不存在的任务。"""
        with pytest.raises(TaskNotFoundError):
            task_repo.delete("tk-notexist")

    def test_count_tasks(self, task_repo: TaskRepository, sample_task_data: dict) -> None:
        """测试统计任务数量。"""
        # 创建任务
        for i in range(3):
            data = sample_task_data.copy()
            data["id"] = f"tk-test{i:03d}"
            task_repo.create(data)

        count = task_repo.count()
        assert count == 3

        # 测试带过滤的计数
        count_open = task_repo.count(filters={"status": "open"})
        assert count_open == 3


class TestDependencyRepository:
    """DependencyRepository 测试类。"""

    def test_create_dependency(
        self,
        dep_repo: DependencyRepository,
        task_repo: TaskRepository,
        sample_task_data: dict,
        sample_dependency_data: dict,
    ) -> None:
        """测试创建依赖。"""
        # 先创建两个任务
        task1_data = sample_task_data.copy()
        task1_data["id"] = "tk-test001"
        task_repo.create(task1_data)

        task2_data = sample_task_data.copy()
        task2_data["id"] = "tk-test002"
        task_repo.create(task2_data)

        # 创建依赖
        dep = dep_repo.create(sample_dependency_data)

        assert dep.id == sample_dependency_data["id"]
        assert dep.task_id == sample_dependency_data["task_id"]
        assert dep.depends_on_id == sample_dependency_data["depends_on_id"]
        assert dep.dep_type == sample_dependency_data["dep_type"]

    def test_create_duplicate_dependency(
        self,
        dep_repo: DependencyRepository,
        task_repo: TaskRepository,
        sample_task_data: dict,
        sample_dependency_data: dict,
    ) -> None:
        """测试创建重复依赖。"""
        # 创建任务
        for task_id in ["tk-test001", "tk-test002"]:
            data = sample_task_data.copy()
            data["id"] = task_id
            task_repo.create(data)

        # 创建依赖
        dep_repo.create(sample_dependency_data)

        # 尝试创建相同依赖应失败（唯一约束）
        with pytest.raises(DependencyError):
            dep_repo.create(sample_dependency_data)

    def test_get_dependencies_for_task(
        self,
        dep_repo: DependencyRepository,
        task_repo: TaskRepository,
        sample_task_data: dict,
    ) -> None:
        """测试获取任务的依赖列表。"""
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

        # 查询依赖
        deps = dep_repo.get_dependencies_for_task("tk-test000")
        assert len(deps) == 2

    def test_get_dependents_for_task(
        self,
        dep_repo: DependencyRepository,
        task_repo: TaskRepository,
        sample_task_data: dict,
    ) -> None:
        """测试获取依赖某任务的任务列表。"""
        # 创建 3 个任务
        for i in range(3):
            data = sample_task_data.copy()
            data["id"] = f"tk-test{i:03d}"
            task_repo.create(data)

        # 创建依赖: task001 和 task002 都依赖 task000
        dep_repo.create(
            {
                "id": "dep-test001",
                "task_id": "tk-test001",
                "depends_on_id": "tk-test000",
                "dep_type": "blocks",
            }
        )
        dep_repo.create(
            {
                "id": "dep-test002",
                "task_id": "tk-test002",
                "depends_on_id": "tk-test000",
                "dep_type": "blocks",
            }
        )

        # 查询依赖此任务的任务
        dependents = dep_repo.get_dependents_for_task("tk-test000")
        assert len(dependents) == 2

    def test_delete_dependency(
        self,
        dep_repo: DependencyRepository,
        task_repo: TaskRepository,
        sample_task_data: dict,
        sample_dependency_data: dict,
    ) -> None:
        """测试删除依赖。"""
        # 创建任务和依赖
        for task_id in ["tk-test001", "tk-test002"]:
            data = sample_task_data.copy()
            data["id"] = task_id
            task_repo.create(data)

        dep = dep_repo.create(sample_dependency_data)

        # 删除依赖
        dep_repo.delete(dep.id)

        # 确认删除成功
        deps = dep_repo.get_dependencies_for_task(sample_dependency_data["task_id"])
        assert len(deps) == 0

    def test_delete_between_tasks(
        self,
        dep_repo: DependencyRepository,
        task_repo: TaskRepository,
        sample_task_data: dict,
    ) -> None:
        """测试删除两任务间的依赖。"""
        # 创建任务
        for i in range(2):
            data = sample_task_data.copy()
            data["id"] = f"tk-test{i:03d}"
            task_repo.create(data)

        # 创建依赖
        dep_repo.create(
            {
                "id": "dep-test001",
                "task_id": "tk-test000",
                "depends_on_id": "tk-test001",
                "dep_type": "blocks",
            }
        )

        # 删除依赖
        dep_repo.delete_between_tasks("tk-test000", "tk-test001")

        # 确认删除成功
        deps = dep_repo.get_dependencies_for_task("tk-test000")
        assert len(deps) == 0


class TestQueryBuilder:
    """QueryBuilder 测试类。"""

    def test_filter_by(self, session: Session, task_repo: TaskRepository, sample_task_data: dict) -> None:
        """测试按字段过滤。"""
        # 创建任务
        for i, status in enumerate(["open", "closed"]):
            data = sample_task_data.copy()
            data["id"] = f"tk-test{i:03d}"
            data["status"] = status
            task_repo.create(data)

        # 使用 QueryBuilder 查询
        from task.models import TaskModel

        builder = QueryBuilder(TaskModel)
        stmt = builder.filter_by(status="open").build()
        result = session.execute(stmt)
        tasks = result.scalars().all()

        assert len(tasks) == 1
        assert tasks[0].status == "open"

    def test_order_by(self, session: Session, task_repo: TaskRepository, sample_task_data: dict) -> None:
        """测试排序。"""
        # 创建不同优先级的任务
        for i in range(3):
            data = sample_task_data.copy()
            data["id"] = f"tk-test{i:03d}"
            data["priority"] = i
            task_repo.create(data)

        # 按优先级升序
        from task.models import TaskModel

        builder = QueryBuilder(TaskModel)
        stmt = builder.order_by("priority").build()
        result = session.execute(stmt)
        tasks = result.scalars().all()

        assert tasks[0].priority == 0
        assert tasks[1].priority == 1
        assert tasks[2].priority == 2

    def test_limit_offset(self, session: Session, task_repo: TaskRepository, sample_task_data: dict) -> None:
        """测试分页。"""
        # 创建 10 个任务
        for i in range(10):
            data = sample_task_data.copy()
            data["id"] = f"tk-test{i:03d}"
            task_repo.create(data)

        # 测试 limit
        from task.models import TaskModel

        builder = QueryBuilder(TaskModel)
        stmt = builder.limit(5).build()
        result = session.execute(stmt)
        tasks = result.scalars().all()

        assert len(tasks) == 5

        # 测试 offset
        builder2 = QueryBuilder(TaskModel)
        stmt2 = builder2.offset(5).limit(5).build()
        result2 = session.execute(stmt2)
        tasks2 = result2.scalars().all()

        assert len(tasks2) == 5


class TestTransactionManager:
    """TransactionManager 测试类。"""

    def test_auto_commit(self, session: Session, task_repo: TaskRepository, sample_task_data: dict) -> None:
        """测试自动提交。"""
        with TransactionManager(session, auto_commit=True):
            task_repo.create(sample_task_data)

        # 事务应已提交
        task = task_repo.get_by_id(sample_task_data["id"])
        assert task is not None

    def test_manual_commit(self, session: Session, task_repo: TaskRepository, sample_task_data: dict) -> None:
        """测试手动提交。"""
        tx = TransactionManager(session, auto_commit=False)

        with tx:
            task_repo.create(sample_task_data)
            tx.commit()

        # 事务应已提交
        task = task_repo.get_by_id(sample_task_data["id"])
        assert task is not None

    def test_rollback_on_exception(
        self, session: Session, task_repo: TaskRepository, sample_task_data: dict
    ) -> None:
        """测试异常时自动回滚。"""
        try:
            with TransactionManager(session):
                task_repo.create(sample_task_data)
                raise ValueError("测试异常")
        except ValueError:
            pass

        # 事务应已回滚
        task = task_repo.get_by_id(sample_task_data["id"])
        assert task is None
