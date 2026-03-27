"""
事件模型测试
"""

import pytest

from scripts.statusline.parser.events import (
    EventType,
    TranscriptEvent,
    UserMessageEvent,
    AssistantMessageEvent,
    ToolCallEvent,
    ToolResultEvent,
    AgentCallEvent,
    AgentResultEvent,
    TodoWriteEvent,
    TodoUpdateEvent,
    StatusChangeEvent,
    ErrorEvent,
    EventSequence,
    EventBus,
    EventListener,
)


class TestEventTypes:
    """事件类型测试"""

    def test_event_type_values(self):
        """测试事件类型值"""
        assert EventType.USER_MESSAGE.value == "user_message"
        assert EventType.ASSISTANT_MESSAGE.value == "assistant_message"
        assert EventType.TOOL_CALL.value == "tool_call"
        assert EventType.TOOL_RESULT.value == "tool_result"
        assert EventType.AGENT_CALL.value == "agent_call"
        assert EventType.AGENT_RESULT.value == "agent_result"
        assert EventType.TODO_WRITE.value == "todo_write"
        assert EventType.TODO_UPDATE.value == "todo_update"
        assert EventType.STATUS_CHANGE.value == "status_change"
        assert EventType.ERROR.value == "error"


class TestTranscriptEvent:
    """基础事件测试"""

    def test_event_creation(self):
        """测试事件创建"""
        event = TranscriptEvent(
            event_type=EventType.USER_MESSAGE,
            timestamp=1.0,
            data={"content": "Hello"},
        )
        assert event.event_type == EventType.USER_MESSAGE
        assert event.timestamp == 1.0
        assert event.data == {"content": "Hello"}

    def test_event_to_dict(self):
        """测试事件转换为字典"""
        event = TranscriptEvent(
            event_type=EventType.USER_MESSAGE,
            timestamp=1.0,
            data={"content": "Hello"},
            metadata={"key": "value"},
        )
        result = event.to_dict()
        assert result["event_type"] == "user_message"
        assert result["timestamp"] == 1.0
        assert result["data"] == {"content": "Hello"}
        assert result["metadata"] == {"key": "value"}

    def test_event_from_dict(self):
        """测试从字典创建事件"""
        data = {
            "event_type": "user_message",
            "timestamp": 1.0,
            "data": {"content": "Hello"},
            "metadata": {"key": "value"},
        }
        event = TranscriptEvent.from_dict(data)
        assert event.event_type == EventType.USER_MESSAGE
        assert event.timestamp == 1.0


class TestUserMessageEvent:
    """用户消息事件测试"""

    def test_user_message_creation(self):
        """测试用户消息事件创建"""
        event = UserMessageEvent(
            event_type=EventType.USER_MESSAGE,
            timestamp=1.0,
            data={},
            content="Hello",
        )
        assert event.content == "Hello"
        assert event.event_type == EventType.USER_MESSAGE

    def test_user_message_auto_data(self):
        """测试自动生成 data"""
        event = UserMessageEvent(
            event_type=EventType.USER_MESSAGE,
            timestamp=1.0,
            data={},
            content="Hello",
        )
        # __post_init__ 会自动设置 data
        assert event.data["content"] == "Hello"


class TestAssistantMessageEvent:
    """助手消息事件测试"""

    def test_assistant_message_creation(self):
        """测试助手消息事件创建"""
        event = AssistantMessageEvent(
            event_type=EventType.ASSISTANT_MESSAGE,
            timestamp=1.0,
            data={},
            content="Response",
            thinking=False,
        )
        assert event.content == "Response"
        assert not event.thinking


class TestToolCallEvent:
    """工具调用事件测试"""

    def test_tool_call_creation(self):
        """测试工具调用事件创建"""
        event = ToolCallEvent(
            event_type=EventType.TOOL_CALL,
            timestamp=1.0,
            data={},
            tool_name="read_file",
            tool_args={"path": "/path/to/file"},
        )
        assert event.tool_name == "read_file"
        assert event.tool_args == {"path": "/path/to/file"}


class TestToolResultEvent:
    """工具结果事件测试"""

    def test_tool_result_creation(self):
        """测试工具结果事件创建"""
        event = ToolResultEvent(
            event_type=EventType.TOOL_RESULT,
            timestamp=1.0,
            data={},
            tool_name="read_file",
            result="file content",
            error=None,
        )
        assert event.tool_name == "read_file"
        assert event.result == "file content"
        assert event.error is None

    def test_tool_result_with_error(self):
        """测试带错误的工具结果"""
        event = ToolResultEvent(
            event_type=EventType.TOOL_RESULT,
            timestamp=1.0,
            data={},
            tool_name="read_file",
            result=None,
            error="File not found",
        )
        assert event.error == "File not found"


class TestStatusChangeEvent:
    """状态变化事件测试"""

    def test_status_change_creation(self):
        """测试状态变化事件创建"""
        event = StatusChangeEvent(
            event_type=EventType.STATUS_CHANGE,
            timestamp=1.0,
            data={},
            old_status="idle",
            new_status="thinking",
        )
        assert event.old_status == "idle"
        assert event.new_status == "thinking"


class TestErrorEvent:
    """错误事件测试"""

    def test_error_event_creation(self):
        """测试错误事件创建"""
        event = ErrorEvent(
            event_type=EventType.ERROR,
            timestamp=1.0,
            data={},
            error_message="Something went wrong",
            error_type="ValueError",
        )
        assert event.error_message == "Something went wrong"
        assert event.error_type == "ValueError"


class TestAgentCallEvent:
    """Agent 调用事件测试"""

    def test_agent_call_creation(self):
        """测试 Agent 调用事件创建"""
        event = AgentCallEvent(
            event_type=EventType.AGENT_CALL,
            timestamp=1.0,
            data={},
            agent_name="research",
            agent_type="skill",
            status="running",
        )
        assert event.agent_name == "research"
        assert event.agent_type == "skill"
        assert event.status == "running"
        assert event.event_type == EventType.AGENT_CALL


class TestAgentResultEvent:
    """Agent 结果事件测试"""

    def test_agent_result_creation(self):
        """测试 Agent 结果事件创建"""
        event = AgentResultEvent(
            event_type=EventType.AGENT_RESULT,
            timestamp=1.0,
            data={},
            agent_name="research",
            result={"data": "result"},
            error=None,
        )
        assert event.agent_name == "research"
        assert event.result == {"data": "result"}
        assert event.error is None

    def test_agent_result_with_error(self):
        """测试带错误的 Agent 结果"""
        event = AgentResultEvent(
            event_type=EventType.AGENT_RESULT,
            timestamp=1.0,
            data={},
            agent_name="research",
            result=None,
            error="Agent failed",
        )
        assert event.error == "Agent failed"


class TestTodoWriteEvent:
    """Todo 写入事件测试"""

    def test_todo_write_creation(self):
        """测试 Todo 写入事件创建"""
        event = TodoWriteEvent(
            event_type=EventType.TODO_WRITE,
            timestamp=1.0,
            data={},
            todo_id="task-1",
            content="Implement feature",
            total=5,
        )
        assert event.todo_id == "task-1"
        assert event.content == "Implement feature"
        assert event.total == 5


class TestTodoUpdateEvent:
    """Todo 更新事件测试"""

    def test_todo_update_creation(self):
        """测试 Todo 更新事件创建"""
        event = TodoUpdateEvent(
            event_type=EventType.TODO_UPDATE,
            timestamp=1.0,
            data={},
            todo_id="task-1",
            completed=3,
            total=5,
        )
        assert event.todo_id == "task-1"
        assert event.completed == 3
        assert event.total == 5


class TestEventSequence:
    """事件序列测试"""

    def test_event_sequence_creation(self):
        """测试事件序列创建"""
        seq = EventSequence()
        assert len(seq) == 0

    def test_event_sequence_append(self):
        """测试添加事件"""
        seq = EventSequence()
        event = UserMessageEvent(
            event_type=EventType.USER_MESSAGE,
            timestamp=1.0,
            data={},
            content="Hello",
        )
        seq.append(event)
        assert len(seq) == 1

    def test_event_sequence_extend(self):
        """测试批量添加事件"""
        seq = EventSequence()
        events = [
            UserMessageEvent(
                event_type=EventType.USER_MESSAGE,
                timestamp=1.0,
                data={},
                content="Hello1",
            ),
            UserMessageEvent(
                event_type=EventType.USER_MESSAGE,
                timestamp=2.0,
                data={},
                content="Hello2",
            ),
        ]
        seq.extend(events)
        assert len(seq) == 2

    def test_event_sequence_filter_by_type(self):
        """测试按类型过滤"""
        seq = EventSequence()
        seq.append(UserMessageEvent(
            event_type=EventType.USER_MESSAGE,
            timestamp=1.0,
            data={},
            content="Hello",
        ))
        seq.append(AssistantMessageEvent(
            event_type=EventType.ASSISTANT_MESSAGE,
            timestamp=2.0,
            data={},
            content="Response",
        ))

        user_events = seq.filter_by_type(EventType.USER_MESSAGE)
        assert len(user_events) == 1
        assert user_events[0].event_type == EventType.USER_MESSAGE

    def test_event_sequence_filter_by_time(self):
        """测试按时间过滤"""
        seq = EventSequence()
        seq.append(UserMessageEvent(
            event_type=EventType.USER_MESSAGE,
            timestamp=1.0,
            data={},
            content="Hello1",
        ))
        seq.append(UserMessageEvent(
            event_type=EventType.USER_MESSAGE,
            timestamp=2.0,
            data={},
            content="Hello2",
        ))

        filtered = seq.filter_by_time(0.5, 1.5)
        assert len(filtered) == 1

    def test_event_sequence_get_latest(self):
        """测试获取最新事件"""
        seq = EventSequence()
        seq.append(UserMessageEvent(
            event_type=EventType.USER_MESSAGE,
            timestamp=1.0,
            data={},
            content="Hello1",
        ))
        seq.append(UserMessageEvent(
            event_type=EventType.USER_MESSAGE,
            timestamp=2.0,
            data={},
            content="Hello2",
        ))

        latest = seq.get_latest(1)
        assert len(latest) == 1
        assert latest[0].content == "Hello2"

    def test_event_sequence_get_all(self):
        """测试获取所有事件"""
        seq = EventSequence()
        event = UserMessageEvent(
            event_type=EventType.USER_MESSAGE,
            timestamp=1.0,
            data={},
            content="Hello",
        )
        seq.append(event)

        all_events = seq.get_all()
        assert len(all_events) == 1

    def test_event_sequence_clear(self):
        """测试清空事件序列"""
        seq = EventSequence()
        seq.append(UserMessageEvent(
            event_type=EventType.USER_MESSAGE,
            timestamp=1.0,
            data={},
            content="Hello",
        ))
        seq.clear()
        assert len(seq) == 0

    def test_event_sequence_iteration(self):
        """测试迭代事件"""
        seq = EventSequence()
        events = [
            UserMessageEvent(
                event_type=EventType.USER_MESSAGE,
                timestamp=i,
                data={},
                content=f"Hello{i}",
            )
            for i in range(3)
        ]
        for event in events:
            seq.append(event)

        count = 0
        for event in seq:
            count += 1
        assert count == 3


class TestEventBus:
    """事件总线测试"""

    def test_event_bus_creation(self):
        """测试事件总线创建"""
        bus = EventBus()
        assert bus is not None

    def test_event_bus_subscribe_publish(self):
        """测试订阅和发布"""
        bus = EventBus()
        received = []

        def listener(event):
            received.append(event)

        bus.subscribe(EventType.USER_MESSAGE, listener)

        event = UserMessageEvent(
            event_type=EventType.USER_MESSAGE,
            timestamp=1.0,
            data={},
            content="Hello",
        )
        bus.publish(event)

        assert len(received) == 1
        assert received[0].content == "Hello"

    def test_event_bus_unsubscribe(self):
        """测试取消订阅"""
        bus = EventBus()
        received = []

        def listener(event):
            received.append(event)

        bus.subscribe(EventType.USER_MESSAGE, listener)
        bus.unsubscribe(EventType.USER_MESSAGE, listener)

        event = UserMessageEvent(
            event_type=EventType.USER_MESSAGE,
            timestamp=1.0,
            data={},
            content="Hello",
        )
        bus.publish(event)

        assert len(received) == 0

    def test_event_bus_multiple_listeners(self):
        """测试多个监听器"""
        bus = EventBus()
        received1 = []
        received2 = []

        def listener1(event):
            received1.append(event)

        def listener2(event):
            received2.append(event)

        bus.subscribe(EventType.USER_MESSAGE, listener1)
        bus.subscribe(EventType.USER_MESSAGE, listener2)

        event = UserMessageEvent(
            event_type=EventType.USER_MESSAGE,
            timestamp=1.0,
            data={},
            content="Hello",
        )
        bus.publish(event)

        assert len(received1) == 1
        assert len(received2) == 1

    def test_event_bus_listener_exception(self):
        """测试监听器异常不影响其他监听器"""
        bus = EventBus()
        received = []

        def failing_listener(event):
            raise Exception("Test error")

        def working_listener(event):
            received.append(event)

        bus.subscribe(EventType.USER_MESSAGE, failing_listener)
        bus.subscribe(EventType.USER_MESSAGE, working_listener)

        event = UserMessageEvent(
            event_type=EventType.USER_MESSAGE,
            timestamp=1.0,
            data={},
            content="Hello",
        )
        bus.publish(event)

        # 工作的监听器应该仍然被调用
        assert len(received) == 1

    def test_event_bus_clear(self):
        """测试清空事件总线"""
        bus = EventBus()

        def listener(event):
            pass

        bus.subscribe(EventType.USER_MESSAGE, listener)
        bus.clear()

        # 清空后重新发布，不应该有错误
        event = UserMessageEvent(
            event_type=EventType.USER_MESSAGE,
            timestamp=1.0,
            data={},
            content="Hello",
        )
        bus.publish(event)
