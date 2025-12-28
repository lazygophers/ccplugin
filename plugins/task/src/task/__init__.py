"""任务管理插件。

基于 MCP 的任务管理系统，提供完整的 CRUD、依赖管理和统计功能。

主要模块：
- types: Pydantic 数据模型
- models: SQLAlchemy 数据库模型
- database: 数据库管理
- repository: 数据访问层
- mappers: 模型转换
- workspace: 工作空间管理
- server: MCP 服务器

使用示例：
    >>> from task import get_workspace
    >>> workspace = get_workspace()
    >>> db = workspace.get_database_manager()
    >>> session = db.get_session()
"""

from .database import DatabaseManager, init_database
from .repository import (
    DependencyRepository,
    TaskRepository,
    TransactionManager,
)
from .types import (
    BriefTask,
    Dependency,
    DependencyType,
    Priority,
    Task,
    TaskStatus,
    TaskStatistics,
    TaskType,
)
from .workspace import WorkspaceManager, get_workspace

__version__ = "0.2.0"

__all__ = [
    # Types
    "Task",
    "BriefTask",
    "Dependency",
    "TaskStatistics",
    "TaskType",
    "TaskStatus",
    "Priority",
    "DependencyType",
    # Database
    "DatabaseManager",
    "init_database",
    # Repository
    "TaskRepository",
    "DependencyRepository",
    "TransactionManager",
    # Workspace
    "WorkspaceManager",
    "get_workspace",
]
