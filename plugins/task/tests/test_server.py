"""MCP 服务器集成测试。

测试所有 MCP 工具的功能和错误处理。
"""

import pytest
from sqlalchemy.orm import Session

from task.repository import DependencyRepository, TaskRepository
from task.server import (
    generate_dependency_id,
    generate_task_id,
    handle_task_blocked,
    handle_task_close,
    handle_task_create,
    handle_task_delete,
    handle_task_dep_add,
    handle_task_dep_list,
    handle_task_dep_remove,
    handle_task_list,
    handle_task_ready,
    handle_task_reopen,
    handle_task_show,
    handle_task_stats,
    handle_task_update,
    handle_workspace_info,
    handle_workspace_init,
)


class TestIDGeneration:
    """ID 生成测试。"""

    def test_generate_task_id(self) -> None:
        """测试任务 ID 生成。"""
        task_id = generate_task_id()

        assert task_id.startswith("tk-")
        assert len(task_id) == 15  # tk- + 12 字符

    def test_generate_task_id_unique(self) -> None:
        """测试任务 ID 唯一性。"""
        ids = {generate_task_id() for _ in range(100)}
        assert len(ids) == 100  # 所有 ID 都应该不同

    def test_generate_dependency_id(self) -> None:
        """测试依赖 ID 生成。"""
        dep_id = generate_dependency_id()

        assert dep_id.startswith("dep-")
        assert len(dep_id) == 16  # dep- + 12 字符

    def test_generate_dependency_id_unique(self) -> None:
        """测试依赖 ID 唯一性。"""
        ids = {generate_dependency_id() for _ in range(100)}
        assert len(ids) == 100


class TestTaskCRUD:
    """任务 CRUD 操作测试。"""

    @pytest.mark.asyncio
    async def test_task_create(self, session: Session) -> None:
        """测试创建任务。"""
        arguments = {
            "title": "测试任务",
            "description": "测试描述",
            "task_type": "task",
            "priority": 2,
        }

        result = await handle_task_create(session, arguments)

        assert len(result) == 1
        assert "✅ 任务创建成功" in result[0].text
        assert "tk-" in result[0].text

    @pytest.mark.asyncio
    async def test_task_create_with_assignee(self, session: Session) -> None:
        """测试创建任务（带负责人）。"""
        arguments = {
            "title": "测试任务",
            "assignee": "developer",
            "priority": 1,
        }

        result = await handle_task_create(session, arguments)

        assert len(result) == 1
        assert "✅ 任务创建成功" in result[0].text
        assert "developer" in result[0].text

    @pytest.mark.asyncio
    async def test_task_list_empty(self, session: Session) -> None:
        """测试列出任务（空列表）。"""
        arguments = {}

        result = await handle_task_list(session, arguments)

        assert len(result) == 1
        assert "未找到任务" in result[0].text

    @pytest.mark.asyncio
    async def test_task_list_with_tasks(
        self, session: Session, sample_task_data: dict
    ) -> None:
        """测试列出任务（有任务）。"""
        # 创建测试任务
        task_repo = TaskRepository(session)
        task_repo.create(sample_task_data)
        session.commit()

        arguments = {"brief": True}
        result = await handle_task_list(session, arguments)

        assert len(result) == 1
        assert "找到 1 个任务" in result[0].text
        assert sample_task_data["id"] in result[0].text

    @pytest.mark.asyncio
    async def test_task_list_with_status_filter(
        self, session: Session, sample_task_data: dict
    ) -> None:
        """测试按状态过滤任务。"""
        # 创建不同状态的任务
        task_repo = TaskRepository(session)

        data1 = sample_task_data.copy()
        data1["id"] = "tk-test001"
        data1["status"] = "open"
        task_repo.create(data1)

        data2 = sample_task_data.copy()
        data2["id"] = "tk-test002"
        data2["status"] = "closed"
        task_repo.create(data2)

        session.commit()

        # 只查询 open 状态
        arguments = {"status": "open", "brief": True}
        result = await handle_task_list(session, arguments)

        assert "找到 1 个任务" in result[0].text
        assert "tk-test001" in result[0].text
        assert "tk-test002" not in result[0].text

    @pytest.mark.asyncio
    async def test_task_show(
        self, session: Session, sample_task_data: dict
    ) -> None:
        """测试显示任务详情。"""
        # 创建测试任务
        task_repo = TaskRepository(session)
        task_repo.create(sample_task_data)
        session.commit()

        arguments = {"task_id": sample_task_data["id"]}
        result = await handle_task_show(session, arguments)

        assert len(result) == 1
        assert sample_task_data["title"] in result[0].text
        assert sample_task_data["description"] in result[0].text

    @pytest.mark.asyncio
    async def test_task_show_not_found(self, session: Session) -> None:
        """测试显示不存在的任务。"""
        arguments = {"task_id": "tk-notexist"}
        result = await handle_task_show(session, arguments)

        assert len(result) == 1
        assert "❌ 任务不存在" in result[0].text

    @pytest.mark.asyncio
    async def test_task_update(
        self, session: Session, sample_task_data: dict
    ) -> None:
        """测试更新任务。"""
        # 创建测试任务
        task_repo = TaskRepository(session)
        task_repo.create(sample_task_data)
        session.commit()

        arguments = {
            "task_id": sample_task_data["id"],
            "title": "更新后的标题",
            "status": "in_progress",
        }
        result = await handle_task_update(session, arguments)

        assert len(result) == 1
        assert "✅ 任务更新成功" in result[0].text
        assert "更新后的标题" in result[0].text

    @pytest.mark.asyncio
    async def test_task_close(
        self, session: Session, sample_task_data: dict
    ) -> None:
        """测试关闭任务。"""
        # 创建测试任务
        task_repo = TaskRepository(session)
        task_repo.create(sample_task_data)
        session.commit()

        arguments = {"task_id": sample_task_data["id"]}
        result = await handle_task_close(session, arguments)

        assert len(result) == 1
        assert "✅ 任务已关闭" in result[0].text

    @pytest.mark.asyncio
    async def test_task_reopen(
        self, session: Session, sample_task_data: dict
    ) -> None:
        """测试重新打开任务。"""
        # 创建并关闭任务
        task_repo = TaskRepository(session)
        task = task_repo.create(sample_task_data)
        task_repo.update(task.id, {"status": "closed"})
        session.commit()

        arguments = {"task_id": sample_task_data["id"]}
        result = await handle_task_reopen(session, arguments)

        assert len(result) == 1
        assert "✅ 任务已重新打开" in result[0].text

    @pytest.mark.asyncio
    async def test_task_delete(
        self, session: Session, sample_task_data: dict
    ) -> None:
        """测试删除任务。"""
        # 创建测试任务
        task_repo = TaskRepository(session)
        task_repo.create(sample_task_data)
        session.commit()

        arguments = {"task_id": sample_task_data["id"]}
        result = await handle_task_delete(session, arguments)

        assert len(result) == 1
        assert "✅ 任务已删除" in result[0].text

        # 验证已删除
        assert task_repo.get_by_id(sample_task_data["id"]) is None


class TestDependencyManagement:
    """依赖管理测试。"""

    @pytest.mark.asyncio
    async def test_dep_add(
        self, session: Session, sample_task_data: dict
    ) -> None:
        """测试添加依赖。"""
        # 创建两个任务
        task_repo = TaskRepository(session)

        data1 = sample_task_data.copy()
        data1["id"] = "tk-test001"
        task_repo.create(data1)

        data2 = sample_task_data.copy()
        data2["id"] = "tk-test002"
        task_repo.create(data2)

        session.commit()

        # 添加依赖
        arguments = {
            "task_id": "tk-test001",
            "depends_on_id": "tk-test002",
            "dep_type": "blocks",
        }
        result = await handle_task_dep_add(session, arguments)

        assert len(result) == 1
        assert "✅ 依赖添加成功" in result[0].text

    @pytest.mark.asyncio
    async def test_dep_list(
        self, session: Session, sample_task_data: dict
    ) -> None:
        """测试列出依赖。"""
        # 创建任务和依赖
        task_repo = TaskRepository(session)
        dep_repo = DependencyRepository(session)

        for i in range(3):
            data = sample_task_data.copy()
            data["id"] = f"tk-test{i:03d}"
            task_repo.create(data)

        dep_repo.create(
            {
                "id": "dep-test001",
                "task_id": "tk-test000",
                "depends_on_id": "tk-test001",
                "dep_type": "blocks",
            }
        )
        session.commit()

        arguments = {"task_id": "tk-test000"}
        result = await handle_task_dep_list(session, arguments)

        assert len(result) == 1
        assert "任务 tk-test000 的依赖:" in result[0].text
        assert "tk-test001 (blocks)" in result[0].text

    @pytest.mark.asyncio
    async def test_dep_remove(
        self, session: Session, sample_task_data: dict
    ) -> None:
        """测试移除依赖。"""
        # 创建任务和依赖
        task_repo = TaskRepository(session)
        dep_repo = DependencyRepository(session)

        data1 = sample_task_data.copy()
        data1["id"] = "tk-test001"
        task_repo.create(data1)

        data2 = sample_task_data.copy()
        data2["id"] = "tk-test002"
        task_repo.create(data2)

        dep_repo.create(
            {
                "id": "dep-test001",
                "task_id": "tk-test001",
                "depends_on_id": "tk-test002",
                "dep_type": "blocks",
            }
        )
        session.commit()

        arguments = {
            "task_id": "tk-test001",
            "depends_on_id": "tk-test002",
        }
        result = await handle_task_dep_remove(session, arguments)

        assert len(result) == 1
        assert "✅ 依赖已移除" in result[0].text


class TestQueryTools:
    """查询工具测试。"""

    @pytest.mark.asyncio
    async def test_task_ready(
        self, session: Session, sample_task_data: dict
    ) -> None:
        """测试就绪任务查询。"""
        # 创建无依赖的任务
        task_repo = TaskRepository(session)

        data = sample_task_data.copy()
        data["status"] = "open"
        task_repo.create(data)
        session.commit()

        arguments = {}
        result = await handle_task_ready(session, arguments)

        assert len(result) == 1
        assert "找到 1 个就绪任务" in result[0].text

    @pytest.mark.asyncio
    async def test_task_blocked(
        self, session: Session, sample_task_data: dict
    ) -> None:
        """测试阻塞任务查询。"""
        # 创建阻塞状态的任务
        task_repo = TaskRepository(session)

        data = sample_task_data.copy()
        data["status"] = "blocked"
        task_repo.create(data)
        session.commit()

        arguments = {}
        result = await handle_task_blocked(session, arguments)

        assert len(result) == 1
        assert "找到 1 个阻塞任务" in result[0].text

    @pytest.mark.asyncio
    async def test_task_stats_empty(self, session: Session) -> None:
        """测试任务统计（无任务）。"""
        arguments = {}
        result = await handle_task_stats(session, arguments)

        assert len(result) == 1
        assert "总任务数: 0" in result[0].text

    @pytest.mark.asyncio
    async def test_task_stats_with_tasks(
        self, session: Session, sample_task_data: dict
    ) -> None:
        """测试任务统计（有任务）。"""
        task_repo = TaskRepository(session)

        # 创建不同状态的任务
        for i, status in enumerate(["open", "in_progress", "closed"]):
            data = sample_task_data.copy()
            data["id"] = f"tk-test{i:03d}"
            data["status"] = status
            task_repo.create(data)

        session.commit()

        arguments = {}
        result = await handle_task_stats(session, arguments)

        assert len(result) == 1
        assert "## 任务统计" in result[0].text
        assert "总任务数: 3" in result[0].text
        assert "待处理: 1" in result[0].text
        assert "进行中: 1" in result[0].text
        assert "已完成: 1" in result[0].text


class TestWorkspace:
    """工作空间测试。"""

    @pytest.mark.asyncio
    async def test_workspace_init(self) -> None:
        """测试工作空间初始化。"""
        arguments = {}
        result = await handle_workspace_init(arguments)

        assert len(result) == 1
        assert "✅ 工作空间初始化成功" in result[0].text
        assert "工作空间 ID:" in result[0].text

    @pytest.mark.asyncio
    async def test_workspace_info(self) -> None:
        """测试获取工作空间信息。"""
        result = await handle_workspace_info()

        assert len(result) == 1
        assert "## 工作空间信息" in result[0].text
        assert "工作空间 ID:" in result[0].text
        assert "数据库路径:" in result[0].text
