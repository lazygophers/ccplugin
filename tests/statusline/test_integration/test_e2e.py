"""
端到端集成测试
"""

import pytest

from scripts.statusline.config.manager import get_default_config
from scripts.statusline.core.loop import StatuslineLoop
from scripts.statusline.parser.events import UserMessageEvent, EventType


class TestE2E:
    """端到端测试"""

    def test_simple_workflow(self, sample_config):
        """测试简单工作流"""
        # 创建主循环
        loop = StatuslineLoop(sample_config)

        # 处理简单 transcript
        transcript = "Test message"
        result = loop.process(transcript)

        # 验证结果
        assert isinstance(result, str)

    def test_user_message_workflow(self, sample_config):
        """测试用户消息工作流"""
        loop = StatuslineLoop(sample_config)

        # 创建用户消息 - 修复参数顺序
        event = UserMessageEvent(
            event_type=EventType.USER_MESSAGE,
            timestamp=0.0,
            data={"content": "Hello, world!"},
            content="Hello, world!",
        )

        # 序列化事件
        import json
        transcript = json.dumps({
            "role": "user",
            "content": "Hello, world!",
        })

        # 处理
        result = loop.process(transcript)

        # 验证
        assert isinstance(result, str)

    def test_multi_event_workflow(self, sample_config):
        """测试多事件工作流"""
        loop = StatuslineLoop(sample_config)

        # 多个事件
        events = [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "Response"},
        ]

        import json
        transcript = json.dumps(events)

        # 处理
        result = loop.process(transcript)

        # 验证
        assert isinstance(result, str)

    def test_cache_workflow(self, sample_config):
        """测试缓存工作流"""
        # 启用缓存
        sample_config.cache.enabled = True

        loop = StatuslineLoop(sample_config)

        transcript = "Test message"

        # 第一次处理
        result1 = loop.process(transcript)

        # 第二次处理（应该使用缓存）
        result2 = loop.process(transcript)

        # 验证结果一致
        assert result1 == result2
