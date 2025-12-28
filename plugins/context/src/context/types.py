"""Context Plugin 类型定义."""

from pydantic import BaseModel


class ContextItem(BaseModel):
    """上下文项模型."""
    id: str
    session_id: str
    content: str
    role: str
    timestamp: float


class ContextError(Exception):
    """上下文插件异常."""
    pass
