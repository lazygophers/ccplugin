"""数据库初始化和管理工具。

本模块提供数据库初始化、连接管理和迁移工具。
使用 SQLAlchemy 2.0 和 Alembic 进行数据库管理。

主要功能：
- 数据库初始化
- 连接池管理
- Alembic 迁移集成
- 健康检查
"""

import os
from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base


# SQLite 优化配置
@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_conn: Any, _connection_record: Any) -> None:
    """为 SQLite 连接设置性能优化参数。

    Args:
        dbapi_conn: 数据库连接对象
        _connection_record: 连接记录（未使用）
    """
    if "sqlite" in str(type(dbapi_conn)):
        cursor = dbapi_conn.cursor()
        # 性能优化
        cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        cursor.execute("PRAGMA synchronous=NORMAL")  # 平衡性能和安全
        cursor.execute("PRAGMA cache_size=10000")  # 增加缓存大小
        cursor.execute("PRAGMA foreign_keys=ON")  # 启用外键约束
        cursor.execute("PRAGMA temp_store=MEMORY")  # 临时表存储在内存
        cursor.close()


class DatabaseManager:
    """数据库管理器。

    负责数据库连接、会话管理和迁移操作。

    Attributes:
        database_url: 数据库连接 URL
        engine: SQLAlchemy 引擎
        session_factory: 会话工厂
    """

    def __init__(self, database_url: str | None = None) -> None:
        """初始化数据库管理器。

        Args:
            database_url: 数据库连接 URL，为 None 则使用默认路径
        """
        self.database_url = database_url or self._get_default_url()
        self.engine = create_engine(
            self.database_url,
            echo=False,  # 生产环境关闭 SQL 日志
            pool_pre_ping=True,  # 连接池健康检查
            pool_recycle=3600,  # 1 小时回收连接
        )
        self.session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    def _get_default_url(self) -> str:
        """获取默认数据库 URL。

        优先级：
        1. 环境变量 TASK_DATABASE_URL
        2. 默认路径 .task_data/tasks.db

        Returns:
            数据库连接 URL
        """
        # 从环境变量获取
        url = os.getenv("TASK_DATABASE_URL")
        if url:
            return url

        # 默认路径
        db_path = Path(".task_data/tasks.db")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path}"

    def init_database(self, run_migrations: bool = True) -> None:
        """初始化数据库。

        Args:
            run_migrations: 是否运行 Alembic 迁移（默认 True）

        Raises:
            RuntimeError: 数据库初始化失败
        """
        try:
            if run_migrations:
                # 使用 Alembic 创建表（推荐）
                self.upgrade_database()
            else:
                # 直接使用 SQLAlchemy 创建表（仅开发/测试）
                Base.metadata.create_all(self.engine)
        except Exception as e:
            raise RuntimeError(f"数据库初始化失败: {e}") from e

    def upgrade_database(self, revision: str = "head") -> None:
        """运行 Alembic 迁移升级。

        Args:
            revision: 目标版本（默认 "head"，即最新版本）

        Raises:
            RuntimeError: 迁移失败
        """
        try:
            alembic_cfg = self._get_alembic_config()
            command.upgrade(alembic_cfg, revision)
        except Exception as e:
            raise RuntimeError(f"数据库迁移失败: {e}") from e

    def downgrade_database(self, revision: str = "-1") -> None:
        """回滚 Alembic 迁移。

        Args:
            revision: 目标版本（默认 "-1"，即回滚一个版本）

        Raises:
            RuntimeError: 回滚失败
        """
        try:
            alembic_cfg = self._get_alembic_config()
            command.downgrade(alembic_cfg, revision)
        except Exception as e:
            raise RuntimeError(f"数据库回滚失败: {e}") from e

    def get_current_revision(self) -> str | None:
        """获取当前数据库版本。

        Returns:
            当前版本号，如果未初始化则返回 None
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT version_num FROM alembic_version LIMIT 1")
                )
                row = result.fetchone()
                return row[0] if row else None
        except Exception:
            return None

    def health_check(self) -> bool:
        """数据库健康检查。

        Returns:
            True 表示数据库正常，False 表示异常
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    def get_session(self) -> Session:
        """获取数据库会话。

        Returns:
            SQLAlchemy 会话对象

        Usage:
            >>> db = DatabaseManager()
            >>> session = db.get_session()
            >>> try:
            ...     # 使用 session 进行数据库操作
            ...     session.commit()
            ... except Exception:
            ...     session.rollback()
            ...     raise
            ... finally:
            ...     session.close()
        """
        return self.session_factory()

    def _get_alembic_config(self) -> Config:
        """获取 Alembic 配置。

        Returns:
            Alembic 配置对象
        """
        # 获取包的根目录（绝对路径）
        package_root = Path(__file__).parent.parent.parent.resolve()

        # 查找 alembic.ini 文件（绝对路径）
        alembic_ini = package_root / "alembic.ini"
        if not alembic_ini.exists():
            raise FileNotFoundError(f"找不到 alembic.ini: {alembic_ini}")

        # 查找 alembic 目录（绝对路径）
        alembic_dir = package_root / "alembic"
        if not alembic_dir.exists():
            raise FileNotFoundError(f"找不到 alembic 目录: {alembic_dir}")

        # 创建 Alembic 配置
        alembic_cfg = Config(str(alembic_ini))

        # 覆盖脚本位置为绝对路径（关键修复）
        alembic_cfg.set_main_option("script_location", str(alembic_dir))

        # 覆盖数据库 URL
        alembic_cfg.set_main_option("sqlalchemy.url", self.database_url)

        return alembic_cfg

    def close(self) -> None:
        """关闭数据库连接。"""
        self.engine.dispose()

    def __enter__(self) -> "DatabaseManager":
        """上下文管理器入口。

        Returns:
            DatabaseManager 实例
        """
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """上下文管理器退出。

        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常回溯
        """
        self.close()


def init_database(database_url: str | None = None) -> DatabaseManager:
    """便捷函数：初始化数据库。

    Args:
        database_url: 数据库连接 URL

    Returns:
        DatabaseManager 实例

    Example:
        >>> db = init_database()
        >>> session = db.get_session()
    """
    db = DatabaseManager(database_url)
    db.init_database()
    return db


def get_database_manager(database_url: str | None = None) -> DatabaseManager:
    """便捷函数：获取数据库管理器（不初始化）。

    Args:
        database_url: 数据库连接 URL

    Returns:
        DatabaseManager 实例

    Example:
        >>> db = get_database_manager()
        >>> if not db.health_check():
        ...     db.init_database()
    """
    return DatabaseManager(database_url)
