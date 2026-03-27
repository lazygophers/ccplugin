"""
Compact 布局测试
"""

import pytest

from scripts.statusline.layout.factory import LayoutFactory
from scripts.statusline.layout.compact import CompactLayout
from scripts.statusline.tracker.aggregator import AggregatedState, StateDimension


class TestCompactLayout:
    """Compact 布局测试"""

    def test_compact_layout_creation(self):
        """测试 Compact 布局创建"""
        layout = LayoutFactory.create("compact")
        assert isinstance(layout, CompactLayout)

    def test_compact_layout_render_basic(self):
        """测试 Compact 布局基础渲染"""
        layout = CompactLayout()
        # 创建正确的 AggregatedState
        state = AggregatedState(
            dimension=StateDimension.USER_STATUS,
            value="idle",
            timestamp=0.0,
        )
        result = layout.render(state)
        assert isinstance(result, str)  # Compact 返回字符串

    def test_compact_layout_progress(self):
        """测试 Compact 布局进度渲染"""
        layout = CompactLayout()
        state = AggregatedState(
            dimension=StateDimension.PROGRESS,
            value={"percentage": 50, "completed": 1, "total": 2},
            timestamp=0.0,
        )
        result = layout.render(state)
        assert isinstance(result, str)
        assert "50%" in result

    def test_compact_layout_resources(self):
        """测试 Compact 布局资源渲染"""
        layout = CompactLayout()
        state = AggregatedState(
            dimension=StateDimension.RESOURCES,
            value={"tokens": 1500, "duration_ms": 5000},
            timestamp=0.0,
        )
        result = layout.render(state)
        assert isinstance(result, str)
        assert "1.5K" in result

    def test_compact_layout_estimate_height(self):
        """测试 Compact 布局高度估算"""
        layout = CompactLayout()
        width = layout.get_width()
        assert isinstance(width, int)
        assert width > 0
