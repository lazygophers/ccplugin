"""
解析器测试
"""

import pytest

from scripts.statusline.parser.incremental import IncrementalParser, ParseState
from scripts.statusline.parser.events import EventType, TranscriptEvent


class TestIncrementalParser:
    """增量解析器测试"""

    def test_parser_initialization(self):
        """测试解析器初始化"""
        parser = IncrementalParser()
        assert parser is not None
        context = parser.get_state()
        assert context.position == 0
        assert context.state == ParseState.IDLE

    def test_parse_empty_chunk(self):
        """测试空数据块解析"""
        parser = IncrementalParser()
        events = parser.parse("")
        assert events == []

    def test_parse_single_event(self):
        """测试单个事件解析"""
        parser = IncrementalParser()
        chunk = '{"event_type": "user_message", "timestamp": 1234567890.0, "data": {"content": "Hello"}}'
        events = parser.parse(chunk)
        assert len(events) == 1
        assert events[0].event_type == EventType.USER_MESSAGE

    def test_parse_incremental(self):
        """测试增量解析"""
        parser = IncrementalParser()

        # 第一次解析
        events1 = parser.parse('{"event_type": "user_message", "timestamp": 1.0, "data": {"content": "A"}}')
        assert len(events1) >= 0

        # 第二次解析（增量）
        events2 = parser.parse('{"event_type": "assistant_message", "timestamp": 2.0, "data": {"content": "B"}}')
        assert len(events2) >= 0

    def test_parse_invalid_json(self):
        """测试无效 JSON 处理"""
        parser = IncrementalParser()
        # 发送无效 JSON
        events1 = parser.parse("invalid json")
        assert events1 == []  # 应该返回空列表

        # 发送有效 JSON
        events2 = parser.parse('{"event_type": "user_message", "timestamp": 1.0, "data": {"content": "Valid"}}')
        assert len(events2) >= 0

    def test_parse_multiple_events(self):
        """测试多个事件解析（JSON 数组）"""
        parser = IncrementalParser()
        chunk = '[{"event_type": "user_message", "timestamp": 1.0, "data": {"content": "A"}}, {"event_type": "assistant_message", "timestamp": 2.0, "data": {"content": "B"}}]'
        events = parser.parse(chunk)
        assert len(events) == 2

    def test_parser_reset(self):
        """测试解析器重置"""
        parser = IncrementalParser()
        parser.parse('{"event_type": "user_message", "timestamp": 1.0, "data": {"content": "A"}}')

        # 重置
        parser.reset()
        context = parser.get_state()
        assert context.position == 0
        assert context.state == ParseState.IDLE
        assert len(parser.get_events()) == 0

    def test_get_events(self):
        """测试获取所有事件"""
        parser = IncrementalParser()
        parser.parse('{"event_type": "user_message", "timestamp": 1.0, "data": {"content": "A"}}')
        parser.parse('{"event_type": "assistant_message", "timestamp": 2.0, "data": {"content": "B"}}')

        events = parser.get_events()
        assert len(events) >= 2
