"""
记忆管理包

提供完整的记忆生命周期管理功能。
"""

from .models import (
    MemoryStatus,
    RelationType,
    Memory,
    MemoryPath,
    MemoryVersion,
    MemoryRelation,
    Session,
    ErrorSolution,
)
from .database import init_db, close_db, get_db_path
from .crud import create_memory, get_memory, update_memory, delete_memory, create_version
from .search import search_memories, list_memories, get_memories_by_priority
from .lifecycle import (
    set_priority,
    deprecate_memory,
    archive_memory,
    restore_memory,
)
from .version import (
    get_versions,
    get_version,
    rollback_to_version,
    diff_versions,
)
from .relation import add_relation, get_relations, remove_relation
from .path import add_memory_path, get_memory_paths, find_memories_by_path
from .import_export import export_memories, import_memories
from .stats import get_stats, clean_memories
from .session import create_session, end_session
from .error import (
    record_error_solution,
    find_error_solution,
    mark_solution_success,
)

__all__ = [
    "MemoryStatus",
    "RelationType",
    "Memory",
    "MemoryPath",
    "MemoryVersion",
    "MemoryRelation",
    "Session",
    "ErrorSolution",
    "init_db",
    "close_db",
    "get_db_path",
    "create_memory",
    "get_memory",
    "update_memory",
    "delete_memory",
    "create_version",
    "search_memories",
    "list_memories",
    "get_memories_by_priority",
    "set_priority",
    "deprecate_memory",
    "archive_memory",
    "restore_memory",
    "get_versions",
    "get_version",
    "rollback_to_version",
    "diff_versions",
    "add_relation",
    "get_relations",
    "remove_relation",
    "add_memory_path",
    "get_memory_paths",
    "find_memories_by_path",
    "export_memories",
    "import_memories",
    "get_stats",
    "clean_memories",
    "create_session",
    "end_session",
    "record_error_solution",
    "find_error_solution",
    "mark_solution_success",
]
