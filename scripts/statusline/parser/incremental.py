"""
增量解析器

支持逐步解析 transcript 数据，维护解析状态。
"""

import json
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from .events import (
    TranscriptEvent,
    EventType,
    UserMessageEvent,
    AssistantMessageEvent,
    ToolCallEvent,
    ToolResultEvent,
    StatusChangeEvent,
    ErrorEvent,
)


class ParseState(Enum):
    """解析状态"""
    IDLE = "idle"
    PARSING_USER = "parsing_user"
    PARSING_ASSISTANT = "parsing_assistant"
    PARSING_TOOL_CALL = "parsing_tool_call"
    PARSING_TOOL_RESULT = "parsing_tool_result"
    ERROR = "error"


@dataclass
class ParserContext:
    """解析器上下文"""
    position: int = 0
    state: ParseState = ParseState.IDLE
    buffer: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_count: int = 0


class IncrementalParser:
    """
    增量解析器

    支持从上次中断位置继续解析，只解析新增的部分。
    """

    def __init__(self, initial_state: Optional[ParserContext] = None):
        """
        初始化解析器

        Args:
            initial_state: 初始解析状态
        """
        self._context = initial_state or ParserContext()
        self._events: List[TranscriptEvent] = []

    def parse(self, chunk: str) -> List[TranscriptEvent]:
        """
        解析数据块

        Args:
            chunk: 输入数据块

        Returns:
            解析出的事件列表
        """
        if not chunk:
            return []

        # 添加到缓冲区
        self._context.buffer += chunk
        self._context.position += len(chunk)

        # 解析缓冲区
        events = self._parse_buffer()

        # 添加到事件列表
        self._events.extend(events)

        return events

    def get_state(self) -> ParserContext:
        """
        获取当前解析状态

        Returns:
            解析上下文
        """
        return self._context

    def reset(self) -> None:
        """重置解析器"""
        self._context = ParserContext()
        self._events.clear()

    def get_events(self) -> List[TranscriptEvent]:
        """
        获取所有已解析的事件

        Returns:
            事件列表
        """
        return self._events.copy()

    def _parse_buffer(self) -> List[TranscriptEvent]:
        """
        解析缓冲区内容

        Returns:
            解析出的事件列表
        """
        events = []

        try:
            # 尝试解析 JSON
            data = json.loads(self._context.buffer)

            if isinstance(data, dict):
                # 单个消息
                event = self._parse_message(data)
                if event:
                    events.append(event)
            elif isinstance(data, list):
                # 消息列表
                for item in data:
                    event = self._parse_message(item)
                    if event:
                        events.append(event)

            # 清空缓冲区
            self._context.buffer = ""
            self._context.state = ParseState.IDLE

        except json.JSONDecodeError:
            # JSON 不完整，等待更多数据
            pass
        except Exception as e:
            # 解析错误
            self._context.state = ParseState.ERROR
            self._context.error_count += 1

        return events

    def _parse_message(self, data: Dict[str, Any]) -> Optional[TranscriptEvent]:
        """
        解析单个消息

        Args:
            data: 消息数据

        Returns:
            事件对象或 None
        """
        if not isinstance(data, dict):
            return None

        # 获取事件类型（支持 event_type 和 role 两种格式）
        event_type_str = data.get("event_type")
        timestamp = data.get("timestamp", self._context.position)
        msg_data = data.get("data", {})

        # 使用 event_type 字段
        if event_type_str:
            try:
                event_type = EventType(event_type_str)
            except ValueError:
                # 未知事件类型
                return None

            if event_type == EventType.USER_MESSAGE:
                return UserMessageEvent(
                    event_type=event_type,
                    timestamp=timestamp,
                    data=msg_data,
                    content=msg_data.get("content", ""),
                )
            elif event_type == EventType.ASSISTANT_MESSAGE:
                return AssistantMessageEvent(
                    event_type=event_type,
                    timestamp=timestamp,
                    data=msg_data,
                    content=msg_data.get("content", ""),
                )
            elif event_type == EventType.TOOL_CALL:
                return ToolCallEvent(
                    event_type=event_type,
                    timestamp=timestamp,
                    data=msg_data,
                    tool_name=msg_data.get("tool_name", ""),
                    tool_args=msg_data.get("tool_args", {}),
                )
            elif event_type == EventType.TOOL_RESULT:
                return ToolResultEvent(
                    event_type=event_type,
                    timestamp=timestamp,
                    data=msg_data,
                    tool_name=msg_data.get("tool_name", ""),
                    result=msg_data.get("result"),
                    error=msg_data.get("error"),
                )
            elif event_type == EventType.STATUS_CHANGE:
                return StatusChangeEvent(
                    event_type=event_type,
                    timestamp=timestamp,
                    data=msg_data,
                    old_status=msg_data.get("old_status", ""),
                    new_status=msg_data.get("new_status", ""),
                )
            elif event_type == EventType.ERROR:
                return ErrorEvent(
                    event_type=event_type,
                    timestamp=timestamp,
                    data=msg_data,
                    error_message=msg_data.get("error_message", ""),
                    error_type=msg_data.get("error_type", ""),
                )
            return None

        # 兼容 role 字段格式
        role = data.get("role")
        content = data.get("content", "")

        if role == "user":
            return UserMessageEvent(
                event_type=EventType.USER_MESSAGE,
                timestamp=timestamp,
                data={"content": content},
                content=content,
            )
        elif role == "assistant":
            return AssistantMessageEvent(
                event_type=EventType.ASSISTANT_MESSAGE,
                timestamp=timestamp,
                data={"content": content},
                content=content,
            )

        return None

    def _detect_message_boundary(self, text: str) -> int:
        """
        检测消息边界

        Args:
            text: 文本

        Returns:
            边界位置，-1 表示未找到
        """
        # 检测 JSON 对象边界
        depth = 0
        in_string = False
        escape = False

        for i, char in enumerate(text):
            if escape:
                escape = False
                continue

            if char == "\\":
                escape = True
                continue

            if char == '"' and not escape:
                in_string = not in_string
                continue

            if not in_string:
                if char == "{":
                    depth += 1
                elif char == "}":
                    depth -= 1
                    if depth == 0:
                        return i + 1

        return -1

    def _extract_json_objects(self, text: str) -> List[str]:
        """
        提取文本中的所有 JSON 对象

        Args:
            text: 文本

        Returns:
            JSON 对象字符串列表
        """
        objects = []
        start = 0

        while start < len(text):
            # 跳过空白字符
            while start < len(text) and text[start].isspace():
                start += 1

            if start >= len(text):
                break

            # 查找 JSON 对象开始
            if text[start] != "{":
                start += 1
                continue

            # 查找对象结束
            end = self._detect_message_boundary(text[start:])
            if end == -1:
                break

            objects.append(text[start:start + end])
            start += end

        return objects
