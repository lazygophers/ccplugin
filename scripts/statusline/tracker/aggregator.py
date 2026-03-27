"""
信息聚合器

从多个数据源收集和聚合状态信息。
"""

from typing import Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import time

from ..parser.events import TranscriptEvent, EventType


class StateDimension(Enum):
    """状态维度"""
    USER_STATUS = "user_status"
    PROGRESS = "progress"
    RESOURCES = "resources"
    ERRORS = "errors"


@dataclass
class AggregatedState:
    """
    聚合状态

    包含各个维度的聚合结果。
    """
    dimension: StateDimension
    value: Any
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = ""


@dataclass
class DataSource:
    """
    数据源

    定义数据源的接口和属性。
    """
    name: str
    priority: int = 0
    enabled: bool = True


class StateAggregator:
    """
    状态聚合器

    从多个数据源收集和聚合状态信息。
    """

    def __init__(self):
        """初始化聚合器"""
        self._sources: Dict[str, DataSource] = {}
        self._states: Dict[StateDimension, AggregatedState] = {}
        self._event_handlers: Dict[EventType, List[Callable]] = {}

    def register_source(self, source: DataSource) -> None:
        """
        注册数据源

        Args:
            source: 数据源对象
        """
        self._sources[source.name] = source

    def unregister_source(self, name: str) -> None:
        """
        注销数据源

        Args:
            name: 数据源名称
        """
        if name in self._sources:
            del self._sources[name]

    def update(self, event: TranscriptEvent) -> None:
        """
        更新状态

        Args:
            event: 事件对象
        """
        # 根据事件类型更新对应维度
        if event.event_type == EventType.USER_MESSAGE:
            self._update_user_status(event)
        elif event.event_type == EventType.ASSISTANT_MESSAGE:
            self._update_user_status(event)
            self._update_resources(event)
        elif event.event_type == EventType.TOOL_CALL:
            self._update_progress(event)
        elif event.event_type == EventType.TOOL_RESULT:
            self._update_progress(event)
        elif event.event_type == EventType.ERROR:
            self._update_errors(event)

        # 调用事件处理器
        handlers = self._event_handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                pass

    def aggregate(self, dimension: StateDimension) -> AggregatedState:
        """
        聚合指定维度的状态

        Args:
            dimension: 状态维度

        Returns:
            聚合状态
        """
        return self._states.get(dimension, self._create_default_state(dimension))

    def get_all_states(self) -> Dict[StateDimension, AggregatedState]:
        """
        获取所有状态

        Returns:
            所有状态的字典
        """
        return {
            dimension: self.aggregate(dimension)
            for dimension in StateDimension
        }

    def register_event_handler(self, event_type: EventType, handler: Callable) -> None:
        """
        注册事件处理器

        Args:
            event_type: 事件类型
            handler: 处理函数
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

    def clear(self) -> None:
        """清空所有状态"""
        self._states.clear()

    def _update_user_status(self, event: TranscriptEvent) -> None:
        """更新用户状态"""
        status = "idle"
        if event.event_type == EventType.USER_MESSAGE:
            status = "inputting"
        elif event.event_type == EventType.ASSISTANT_MESSAGE:
            data = event.data
            if data.get("thinking"):
                status = "thinking"
            else:
                status = "responding"

        self._states[StateDimension.USER_STATUS] = AggregatedState(
            dimension=StateDimension.USER_STATUS,
            value=status,
            timestamp=event.timestamp,
            metadata={"event_type": event.event_type.value},
        )

    def _update_progress(self, event: TranscriptEvent) -> None:
        """更新进度状态"""
        current = self._states.get(StateDimension.PROGRESS)
        if current:
            progress = current.metadata.get("completed", 0) + 1
            total = current.metadata.get("total", progress)
        else:
            progress = 1
            total = 1

        percentage = (progress / total * 100) if total > 0 else 0

        self._states[StateDimension.PROGRESS] = AggregatedState(
            dimension=StateDimension.PROGRESS,
            value={
                "percentage": percentage,
                "completed": progress,
                "total": total,
            },
            timestamp=event.timestamp,
            metadata={
                "event_type": event.event_type.value,
                "completed": progress,
                "total": total,
            },
        )

    def _update_resources(self, event: TranscriptEvent) -> None:
        """更新资源状态"""
        current = self._states.get(StateDimension.RESOURCES)
        if current:
            tokens = current.metadata.get("tokens", 0)
            duration = current.metadata.get("duration", 0.0)
        else:
            tokens = 0
            duration = 0.0

        # 估算 token 数量
        content_length = len(str(event.data))
        estimated_tokens = content_length // 4

        self._states[StateDimension.RESOURCES] = AggregatedState(
            dimension=StateDimension.RESOURCES,
            value={
                "tokens": tokens + estimated_tokens,
                "duration_ms": duration,
            },
            timestamp=event.timestamp,
            metadata={
                "tokens": tokens + estimated_tokens,
                "duration": duration,
            },
        )

    def _update_errors(self, event: TranscriptEvent) -> None:
        """更新错误状态"""
        current = self._states.get(StateDimension.ERRORS)
        if current:
            error_count = current.metadata.get("count", 0)
            errors = current.metadata.get("errors", [])
        else:
            error_count = 0
            errors = []

        error_count += 1
        errors.append({
            "message": event.data.get("error_message", ""),
            "type": event.data.get("error_type", ""),
            "timestamp": event.timestamp,
        })

        self._states[StateDimension.ERRORS] = AggregatedState(
            dimension=StateDimension.ERRORS,
            value={
                "count": error_count,
                "errors": errors[-10:],  # 只保留最近 10 个
            },
            timestamp=event.timestamp,
            metadata={
                "count": error_count,
                "errors": errors,
            },
        )

    def _create_default_state(self, dimension: StateDimension) -> AggregatedState:
        """创建默认状态"""
        default_values = {
            StateDimension.USER_STATUS: "idle",
            StateDimension.PROGRESS: {
                "percentage": 0,
                "completed": 0,
                "total": 0,
            },
            StateDimension.RESOURCES: {
                "tokens": 0,
                "duration_ms": 0,
            },
            StateDimension.ERRORS: {
                "count": 0,
                "errors": [],
            },
        }

        return AggregatedState(
            dimension=dimension,
            value=default_values.get(dimension),
            timestamp=time.time(),
        )
