"""市场插件的类型定义."""

from typing import Protocol, TypeVar, Any
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel


class MarketError(Exception):
    """市场插件基础异常."""
    pass


class FeatureType(str, Enum):
    """功能类型枚举."""
    MEMORY = "memory"
    CONTEXT = "context"
    TASK = "task"
    KNOWLEDGE = "knowledge"


class StorageType(str, Enum):
    """存储类型枚举."""
    VECTOR = "vector"
    GRAPH = "graph"
    RELATIONAL = "relational"
    CACHE = "cache"


@dataclass
class ToolConfig:
    """工具配置."""
    feature_type: FeatureType
    storage_type: StorageType
    enabled: bool = True
    max_timeout: float = 30.0


class MemoryItem(BaseModel):
    """记忆项模型."""
    id: str
    content: str
    metadata: dict[str, Any]
    timestamp: float
    tags: list[str] = []


class ContextItem(BaseModel):
    """上下文项模型."""
    id: str
    session_id: str
    content: str
    role: str
    timestamp: float


class TaskItem(BaseModel):
    """任务项模型."""
    id: str
    title: str
    description: str
    status: str
    priority: int
    tags: list[str] = []


class KnowledgeItem(BaseModel):
    """知识库项模型."""
    id: str
    content: str
    embedding: list[float] | None = None
    metadata: dict[str, Any]
    source: str


class MarketTool(Protocol):
    """市场工具协议."""

    async def execute(self, **kwargs: Any) -> Any:
        """执行工具."""
        ...

    @property
    def name(self) -> str:
        """工具名称."""
        ...

    @property
    def description(self) -> str:
        """工具描述."""
        ...
