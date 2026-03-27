"""
Transcript 事件模型

定义事件类型和处理机制，支持事件序列化和监听。
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class EventType(Enum):
    """事件类型"""
    USER_MESSAGE = "user_message"
    ASSISTANT_MESSAGE = "assistant_message"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    STATUS_CHANGE = "status_change"
    ERROR = "error"


@dataclass
class TranscriptEvent:
    """
    事件基类

    所有事件的基础类，包含通用的事件属性。
    """
    event_type: EventType
    timestamp: float
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "data": self.data,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TranscriptEvent':
        """从字典创建"""
        event_type = EventType(data["event_type"])
        return cls(
            event_type=event_type,
            timestamp=data["timestamp"],
            data=data["data"],
            metadata=data.get("metadata", {}),
        )


@dataclass
class UserMessageEvent(TranscriptEvent):
    """用户消息事件"""
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.event_type = EventType.USER_MESSAGE
        if not self.data:
            self.data = {"content": self.content}


@dataclass
class AssistantMessageEvent(TranscriptEvent):
    """助手消息事件"""
    content: str = ""
    thinking: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.event_type = EventType.ASSISTANT_MESSAGE
        if not self.data:
            self.data = {
                "content": self.content,
                "thinking": self.thinking,
            }


@dataclass
class ToolCallEvent(TranscriptEvent):
    """工具调用事件"""
    tool_name: str = ""
    tool_args: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.event_type = EventType.TOOL_CALL
        if not self.data:
            self.data = {
                "tool_name": self.tool_name,
                "tool_args": self.tool_args,
            }


@dataclass
class ToolResultEvent(TranscriptEvent):
    """工具结果事件"""
    tool_name: str = ""
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.event_type = EventType.TOOL_RESULT
        if not self.data:
            self.data = {
                "tool_name": self.tool_name,
                "result": self.result,
                "error": self.error,
            }


@dataclass
class StatusChangeEvent(TranscriptEvent):
    """状态变化事件"""
    old_status: str = ""
    new_status: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.event_type = EventType.STATUS_CHANGE
        if not self.data:
            self.data = {
                "old_status": self.old_status,
                "new_status": self.new_status,
            }


@dataclass
class ErrorEvent(TranscriptEvent):
    """错误事件"""
    error_message: str = ""
    error_type: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.event_type = EventType.ERROR
        if not self.data:
            self.data = {
                "error_message": self.error_message,
                "error_type": self.error_type,
            }


class EventSequence:
    """
    事件序列

    维护事件的时间顺序，支持事件过滤和聚合。
    """

    def __init__(self):
        """初始化事件序列"""
        self._events: List[TranscriptEvent] = []

    def append(self, event: TranscriptEvent) -> None:
        """
        添加事件

        Args:
            event: 事件对象
        """
        self._events.append(event)

    def extend(self, events: List[TranscriptEvent]) -> None:
        """
        批量添加事件

        Args:
            events: 事件列表
        """
        self._events.extend(events)

    def filter_by_type(self, event_type: EventType) -> List[TranscriptEvent]:
        """
        按类型过滤事件

        Args:
            event_type: 事件类型

        Returns:
            过滤后的事件列表
        """
        return [e for e in self._events if e.event_type == event_type]

    def filter_by_time(self, start: float, end: float) -> List[TranscriptEvent]:
        """
        按时间范围过滤事件

        Args:
            start: 开始时间
            end: 结束时间

        Returns:
            过滤后的事件列表
        """
        return [e for e in self._events if start <= e.timestamp <= end]

    def get_latest(self, count: int = 1) -> List[TranscriptEvent]:
        """
        获取最新的 N 个事件

        Args:
            count: 事件数量

        Returns:
            事件列表
        """
        return self._events[-count:] if count > 0 else []

    def get_all(self) -> List[TranscriptEvent]:
        """
        获取所有事件

        Returns:
            所有事件列表
        """
        return self._events.copy()

    def clear(self) -> None:
        """清空事件序列"""
        self._events.clear()

    def __len__(self) -> int:
        """获取事件数量"""
        return len(self._events)

    def __iter__(self):
        """迭代事件"""
        return iter(self._events)


class EventListener:
    """事件监听器函数类型"""
    def __call__(self, event: TranscriptEvent) -> None:
        ...


class EventBus:
    """
    事件总线

    实现发布-订阅模式，支持多个监听器。
    """

    def __init__(self):
        """初始化事件总线"""
        self._listeners: Dict[EventType, List[EventListener]] = {}

    def subscribe(self, event_type: EventType, listener: EventListener) -> None:
        """
        订阅事件

        Args:
            event_type: 事件类型
            listener: 监听器函数
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)

    def unsubscribe(self, event_type: EventType, listener: EventListener) -> None:
        """
        取消订阅

        Args:
            event_type: 事件类型
            listener: 监听器函数
        """
        if event_type in self._listeners:
            try:
                self._listeners[event_type].remove(listener)
            except ValueError:
                pass

    def publish(self, event: TranscriptEvent) -> None:
        """
        发布事件

        Args:
            event: 事件对象
        """
        listeners = self._listeners.get(event.event_type, [])
        for listener in listeners:
            try:
                listener(event)
            except Exception:
                # 监听器异常不影响其他监听器
                pass

    def clear(self) -> None:
        """清空所有监听器"""
        self._listeners.clear()
