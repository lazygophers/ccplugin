"""Workspace 层单元测试。

测试 WorkspaceManager 和工作空间管理功能。
"""

from pathlib import Path

import pytest

from task.workspace import WorkspaceError, WorkspaceManager, get_workspace, list_workspaces


class TestWorkspaceManager:
    """WorkspaceManager 测试类。"""

    def test_init_workspace(self, temp_dir: Path) -> None:
        """测试工作空间初始化。"""
        workspace = WorkspaceManager(temp_dir, auto_init=True)

        # 使用 resolve() 比较路径（处理符号链接）
        assert workspace.workspace_root.resolve() == temp_dir.resolve()
        assert workspace.workspace_id is not None
        assert workspace.database_path.exists()

        workspace.cleanup()

    def test_workspace_id_generation(self, temp_dir: Path) -> None:
        """测试工作空间 ID 生成。"""
        ws1 = WorkspaceManager(temp_dir, auto_init=False)
        ws2 = WorkspaceManager(temp_dir, auto_init=False)

        # 相同路径应生成相同 ID
        assert ws1.workspace_id == ws2.workspace_id

        ws1.cleanup()
        ws2.cleanup()

    def test_different_workspace_ids(self, temp_dir: Path) -> None:
        """测试不同路径生成不同 ID。"""
        dir1 = temp_dir / "workspace1"
        dir2 = temp_dir / "workspace2"

        ws1 = WorkspaceManager(dir1, auto_init=False)
        ws2 = WorkspaceManager(dir2, auto_init=False)

        # 不同路径应生成不同 ID
        assert ws1.workspace_id != ws2.workspace_id

        ws1.cleanup()
        ws2.cleanup()

    def test_get_database_manager(self, workspace: WorkspaceManager) -> None:
        """测试获取数据库管理器。"""
        db = workspace.get_database_manager()

        assert db is not None
        assert db.health_check() is True

    def test_get_workspace_info(self, workspace: WorkspaceManager) -> None:
        """测试获取工作空间信息。"""
        info = workspace.get_workspace_info()

        assert "workspace_id" in info
        assert "workspace_root" in info
        assert "database_path" in info
        assert "database_exists" in info
        assert "database_healthy" in info
        assert info["database_exists"] is True
        assert info["database_healthy"] is True

    def test_delete_workspace(self, temp_dir: Path) -> None:
        """测试删除工作空间。"""
        workspace = WorkspaceManager(temp_dir, auto_init=True)
        db_path = workspace.database_path

        assert db_path.exists()

        # 删除工作空间
        workspace.delete_workspace(confirm=True)

        # 验证数据库文件已删除
        assert not db_path.exists()

    def test_delete_workspace_requires_confirm(self, workspace: WorkspaceManager) -> None:
        """测试删除工作空间需要确认。"""
        with pytest.raises(WorkspaceError):
            workspace.delete_workspace(confirm=False)

    def test_context_manager(self, temp_dir: Path) -> None:
        """测试上下文管理器。"""
        with WorkspaceManager(temp_dir, auto_init=True) as workspace:
            assert workspace.workspace_root.resolve() == temp_dir.resolve()
            assert workspace.database_path.exists()

        # 退出上下文后资源应已清理

    def test_auto_init(self, temp_dir: Path) -> None:
        """测试自动初始化。"""
        workspace = WorkspaceManager(temp_dir, auto_init=True)

        # 数据库应已创建
        assert workspace.database_path.exists()
        assert workspace.get_database_manager().health_check() is True

        workspace.cleanup()

    def test_no_auto_init(self, temp_dir: Path) -> None:
        """测试禁用自动初始化。"""
        workspace = WorkspaceManager(temp_dir, auto_init=False)

        # 数据库文件应不存在（因为没有初始化）
        # 但目录应存在
        assert workspace.workspace_root.exists()

        workspace.cleanup()


class TestWorkspaceSecurity:
    """工作空间安全测试。"""

    def test_reject_unsafe_path_with_dotdot(self) -> None:
        """测试拒绝包含 .. 的路径。"""
        with pytest.raises(WorkspaceError):
            WorkspaceManager("/tmp/../etc", auto_init=False)

    def test_reject_sensitive_directory(self) -> None:
        """测试拒绝敏感目录。"""
        # 这个测试可能因系统而异，仅作示例
        # 在实际环境中可能需要 mock
        with pytest.raises(WorkspaceError):
            WorkspaceManager("/etc", auto_init=False)

    def test_accept_safe_path(self, temp_dir: Path) -> None:
        """测试接受安全路径。"""
        workspace = WorkspaceManager(temp_dir, auto_init=False)
        assert workspace.workspace_root.resolve() == temp_dir.resolve()
        workspace.cleanup()


class TestWorkspaceHelpers:
    """工作空间辅助函数测试。"""

    def test_get_workspace(self, temp_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试 get_workspace 函数。"""
        monkeypatch.chdir(temp_dir)

        workspace = get_workspace(temp_dir, auto_init=True)

        assert workspace is not None
        assert workspace.workspace_root.resolve() == temp_dir.resolve()

        workspace.cleanup()

    def test_list_workspaces(self, temp_dir: Path) -> None:
        """测试 list_workspaces 函数。"""
        # 创建多个工作空间
        ws1 = WorkspaceManager(temp_dir / "ws1", auto_init=True)
        ws2 = WorkspaceManager(temp_dir / "ws2", auto_init=True)

        # 列出工作空间
        workspaces = list_workspaces(temp_dir)

        assert len(workspaces) >= 2

        ws1.cleanup()
        ws2.cleanup()


class TestWorkspaceIsolation:
    """工作空间隔离测试。"""

    def test_independent_databases(self, temp_dir: Path) -> None:
        """测试独立的数据库。"""
        ws1 = WorkspaceManager(temp_dir / "ws1", auto_init=True)
        ws2 = WorkspaceManager(temp_dir / "ws2", auto_init=True)

        # 两个工作空间应有不同的数据库文件
        assert ws1.database_path != ws2.database_path

        # 两个数据库都应正常工作
        assert ws1.get_database_manager().health_check() is True
        assert ws2.get_database_manager().health_check() is True

        ws1.cleanup()
        ws2.cleanup()

    def test_data_isolation(self, temp_dir: Path) -> None:
        """测试数据隔离。"""
        from task.repository import TaskRepository

        # 创建两个工作空间
        ws1 = WorkspaceManager(temp_dir / "ws1", auto_init=True)
        ws2 = WorkspaceManager(temp_dir / "ws2", auto_init=True)

        # 在 ws1 中创建任务
        db1 = ws1.get_database_manager()
        session1 = db1.get_session()
        repo1 = TaskRepository(session1)
        task1 = repo1.create(
            {
                "id": "tk-test001",
                "title": "WS1 任务",
                "task_type": "task",
                "priority": 2,
                "status": "open",
            }
        )
        session1.commit()

        # 在 ws2 中查询，应查询不到
        db2 = ws2.get_database_manager()
        session2 = db2.get_session()
        repo2 = TaskRepository(session2)
        task2 = repo2.get_by_id("tk-test001")

        assert task2 is None  # ws2 不应看到 ws1 的数据

        session1.close()
        session2.close()
        ws1.cleanup()
        ws2.cleanup()
