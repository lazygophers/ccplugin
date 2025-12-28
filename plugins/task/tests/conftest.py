"""测试配置和共享 fixtures。

本模块提供测试所需的共享 fixtures 和配置。
"""

import tempfile
from pathlib import Path
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from task.database import DatabaseManager
from task.models import Base
from task.repository import DependencyRepository, TaskRepository
from task.workspace import WorkspaceManager


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """临时目录 fixture。

    Yields:
        临时目录路径
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def in_memory_db() -> Generator[Session, None, None]:
    """内存数据库会话 fixture。

    Yields:
        SQLAlchemy 会话对象
    """
    # 创建内存数据库
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)

    # 创建会话工厂
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def db_manager(temp_dir: Path) -> Generator[DatabaseManager, None, None]:
    """数据库管理器 fixture。

    Args:
        temp_dir: 临时目录

    Yields:
        DatabaseManager 实例
    """
    db_path = temp_dir / "test.db"
    db_url = f"sqlite:///{db_path}"

    db = DatabaseManager(db_url)
    db.init_database(run_migrations=False)  # 测试中直接创建表

    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def session(db_manager: DatabaseManager) -> Generator[Session, None, None]:
    """数据库会话 fixture。

    Args:
        db_manager: 数据库管理器

    Yields:
        SQLAlchemy 会话对象
    """
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def task_repo(session: Session) -> TaskRepository:
    """任务仓库 fixture。

    Args:
        session: 数据库会话

    Returns:
        TaskRepository 实例
    """
    return TaskRepository(session)


@pytest.fixture
def dep_repo(session: Session) -> DependencyRepository:
    """依赖仓库 fixture。

    Args:
        session: 数据库会话

    Returns:
        DependencyRepository 实例
    """
    return DependencyRepository(session)


@pytest.fixture
def workspace(temp_dir: Path) -> Generator[WorkspaceManager, None, None]:
    """工作空间 fixture。

    Args:
        temp_dir: 临时目录

    Yields:
        WorkspaceManager 实例
    """
    workspace = WorkspaceManager(temp_dir, auto_init=True)
    try:
        yield workspace
    finally:
        workspace.cleanup()


@pytest.fixture
def sample_task_data() -> dict:
    """示例任务数据 fixture。

    Returns:
        任务数据字典
    """
    return {
        "id": "tk-test001",
        "title": "测试任务",
        "description": "这是一个测试任务",
        "task_type": "task",
        "priority": 2,
        "status": "open",
        "tags": ["test", "sample"],
    }


@pytest.fixture
def sample_dependency_data() -> dict:
    """示例依赖数据 fixture。

    Returns:
        依赖数据字典
    """
    return {
        "id": "dep-test001",
        "task_id": "tk-test001",
        "depends_on_id": "tk-test002",
        "dep_type": "blocks",
        "reason": "测试依赖",
    }
