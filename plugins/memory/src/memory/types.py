"""Memory Plugin 类型定义."""

from typing import Any
from pydantic import BaseModel


class MemoryItem(BaseModel):
    """记忆项模型."""
    id: str
    content: str
    metadata: dict[str, Any]
    timestamp: float
    tags: list[str] = []


class MemoryError(Exception):
    """记忆插件异常."""
    pass
