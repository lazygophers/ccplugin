"""Database 层单元测试。

测试 DatabaseManager 和数据库初始化功能。
"""

from pathlib import Path

import pytest

from task.database import DatabaseManager


class TestDatabaseManager:
    """DatabaseManager 测试类。"""

    def test_init_database(self, temp_dir: Path) -> None:
        """测试数据库初始化。"""
        db_path = temp_dir / "test.db"
        db_url = f"sqlite:///{db_path}"

        db = DatabaseManager(db_url)
        db.init_database(run_migrations=False)  # 测试中直接创建表

        # 验证数据库文件已创建
        assert db_path.exists()

        # 验证可以获取会话
        session = db.get_session()
        assert session is not None
        session.close()

        db.close()

    def test_health_check(self, db_manager: DatabaseManager) -> None:
        """测试数据库健康检查。"""
        assert db_manager.health_check() is True

    def test_get_session(self, db_manager: DatabaseManager) -> None:
        """测试获取数据库会话。"""
        session = db_manager.get_session()

        assert session is not None
        # 验证可以执行查询
        from sqlalchemy import text

        result = session.execute(text("SELECT 1"))
        assert result.scalar() == 1

        session.close()

    def test_context_manager(self, temp_dir: Path) -> None:
        """测试上下文管理器。"""
        db_path = temp_dir / "test.db"
        db_url = f"sqlite:///{db_path}"

        with DatabaseManager(db_url) as db:
            db.init_database(run_migrations=False)
            assert db.health_check() is True

        # 退出上下文后连接应已关闭
        # （无法直接验证，但不应抛出异常）

    def test_default_url(self, temp_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """测试默认数据库 URL。"""
        # 设置环境变量
        test_url = f"sqlite:///{temp_dir}/custom.db"
        monkeypatch.setenv("TASK_DATABASE_URL", test_url)

        db = DatabaseManager()
        assert db.database_url == test_url
        db.close()

    def test_multiple_sessions(self, db_manager: DatabaseManager) -> None:
        """测试获取多个会话。"""
        session1 = db_manager.get_session()
        session2 = db_manager.get_session()

        assert session1 is not session2

        session1.close()
        session2.close()


class TestSQLiteOptimization:
    """SQLite 优化测试。"""

    def test_wal_mode_enabled(self, db_manager: DatabaseManager) -> None:
        """测试 WAL 模式是否启用。"""
        session = db_manager.get_session()

        from sqlalchemy import text

        result = session.execute(text("PRAGMA journal_mode"))
        mode = result.scalar()

        assert mode.lower() == "wal"

        session.close()

    def test_foreign_keys_enabled(self, db_manager: DatabaseManager) -> None:
        """测试外键约束是否启用。"""
        session = db_manager.get_session()

        from sqlalchemy import text

        result = session.execute(text("PRAGMA foreign_keys"))
        enabled = result.scalar()

        assert enabled == 1

        session.close()
