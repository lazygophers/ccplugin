"""
pytest 配置和 fixtures
"""

import pytest
from pathlib import Path

from scripts.statusline.config.manager import Config, get_default_config
from scripts.statusline.parser.events import TranscriptEvent, EventType
from scripts.statusline.tracker.aggregator import AggregatedState, StateDimension


@pytest.fixture
def sample_config():
    """示例配置"""
    return get_default_config()


@pytest.fixture
def sample_event():
    """示例事件"""
    return TranscriptEvent(
        event_type=EventType.USER_MESSAGE,
        timestamp=0.0,
        data={"content": "test message"},
    )


@pytest.fixture
def sample_state():
    """示例状态"""
    return AggregatedState(
        dimension=StateDimension.USER_STATUS,
        value="idle",
        timestamp=0.0,
    )


@pytest.fixture
def temp_config_file(tmp_path):
    """临时配置文件"""
    config_file = tmp_path / "config.json"
    config = get_default_config()
    import json
    config_file.write_text(json.dumps(config.to_dict()))
    return config_file
