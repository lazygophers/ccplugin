"""
Layout 基类测试
"""

import pytest

from scripts.statusline.layout.base import Layout
from scripts.statusline.layout.compact import CompactLayout
from scripts.statusline.tracker.aggregator import AggregatedState, StateDimension


class TestLayout:
    """Layout 基类测试（通过 CompactLayout 测试基类功能）"""

    def test_layout_creation(self):
        """测试布局创建"""
        layout = CompactLayout()
        assert layout is not None

    def test_layout_with_config(self):
        """测试带配置的布局创建"""
        config = {
            "components": ["user", "progress"],
            "max_width": 100,
        }
        layout = CompactLayout(config)
        assert layout is not None

    def test_layout_get_config(self):
        """测试获取配置"""
        config = {"max_width": 50}
        layout = CompactLayout(config)

        assert layout._get_config("max_width", 100) == 50
        assert layout._get_config("unknown_key", "default") == "default"

    def test_layout_enable_component(self):
        """测试启用组件"""
        layout = CompactLayout()
        layout.enable_component("user")
        assert layout.supports_component("user")

    def test_layout_disable_component(self):
        """测试禁用组件"""
        layout = CompactLayout()
        layout.disable_component("user")
        assert not layout.supports_component("user")

    def test_layout_supports_component(self):
        """测试检查组件是否启用"""
        layout = CompactLayout()
        # 默认情况下 user 是启用的
        assert layout.supports_component("user")

        layout.disable_component("user")
        assert not layout.supports_component("user")

    def test_layout_render(self):
        """测试渲染方法"""
        layout = CompactLayout()
        state = AggregatedState(
            dimension=StateDimension.USER_STATUS,
            value="idle",
            timestamp=0.0,
        )

        result = layout.render(state)
        assert isinstance(result, str)

    def test_layout_estimate_height(self):
        """测试高度估算"""
        layout = CompactLayout()
        state = AggregatedState(
            dimension=StateDimension.USER_STATUS,
            value="idle",
            timestamp=0.0,
        )

        # CompactLayout 没有实现 estimate_height，使用默认的 get_width
        width = layout.get_width()
        assert width >= 0

    def test_layout_get_width(self):
        """测试获取宽度"""
        layout = CompactLayout()
        width = layout.get_width()
        assert width > 0

    def test_layout_components_config(self):
        """测试通过配置设置组件"""
        config = {"show_user": True, "show_progress": True, "show_resources": True}
        layout = CompactLayout(config)

        assert layout.supports_component("user")
        assert layout.supports_component("progress")
        assert layout.supports_component("resources")
        # tools/agents/todos 始终启用，无需配置
        assert layout.supports_component("tools")
        assert layout.supports_component("agents")
        assert layout.supports_component("todos")

    def test_layout_enable_multiple_components(self):
        """测试启用多个组件"""
        layout = CompactLayout()
        layout.enable_component("user")
        layout.enable_component("progress")
        layout.enable_component("resources")

        assert layout.supports_component("user")
        assert layout.supports_component("progress")
        assert layout.supports_component("resources")

    def test_layout_disable_nonexistent_component(self):
        """测试禁用不存在的组件（不应报错）"""
        layout = CompactLayout()
        layout.disable_component("nonexistent")
        assert True  # 不应该抛出异常

    def test_layout_empty_config(self):
        """测试空配置"""
        layout = CompactLayout({})
        assert layout is not None

    def test_layout_none_config(self):
        """测试 None 配置"""
        layout = CompactLayout(None)
        assert layout is not None

    def test_render_with_dict_value(self):
        """测试渲染字典值"""
        layout = CompactLayout()
        state = AggregatedState(
            dimension=StateDimension.PROGRESS,
            value={"percentage": 50, "completed": 1, "total": 2},
            timestamp=0.0,
        )

        result = layout.render(state)
        assert isinstance(result, str)

    def test_render_with_string_value(self):
        """测试渲染字符串值"""
        layout = CompactLayout()
        state = AggregatedState(
            dimension=StateDimension.USER_STATUS,
            value="thinking",
            timestamp=0.0,
        )

        result = layout.render(state)
        assert isinstance(result, str)

    def test_render_with_none_value(self):
        """测试渲染 None 值"""
        layout = CompactLayout()
        state = AggregatedState(
            dimension=StateDimension.USER_STATUS,
            value=None,
            timestamp=0.0,
        )

        result = layout.render(state)
        assert isinstance(result, str)

    def test_layout_validate(self):
        """测试布局验证"""
        layout = CompactLayout()
        assert layout.validate()

    def test_layout_update_config(self):
        """测试更新配置"""
        layout = CompactLayout()
        layout.update_config({"show_user": False})
        assert not layout.supports_component("user")

    def test_layout_validate_invalid_config(self):
        """测试无效配置验证"""
        layout = CompactLayout({"width": -1})
        assert not layout.validate()

    def test_abstract_cannot_instantiate(self):
        """测试抽象基类不能直接实例化"""
        with pytest.raises(TypeError):
            Layout()  # type: ignore

    def test_layout_tools_agents_todos_always_enabled(self):
        """测试 tools/agents/todos 组件始终启用"""
        layout = CompactLayout()

        # 验证默认启用
        assert layout.supports_component("tools")
        assert layout.supports_component("agents")
        assert layout.supports_component("todos")

        # 验证尝试禁用无效
        layout.disable_component("tools")
        assert layout.supports_component("tools")

        layout.disable_component("agents")
        assert layout.supports_component("agents")

        layout.disable_component("todos")
        assert layout.supports_component("todos")

        # 验证即使通过配置传入 False，仍然启用
        config = {"show_tools": False, "show_agents": False, "show_todos": False}
        layout2 = CompactLayout(config)
        assert layout2.supports_component("tools")
        assert layout2.supports_component("agents")
        assert layout2.supports_component("todos")

    def test_layout_update_config_ignores_tools_agents_todos(self):
        """测试 update_config 忽略 tools/agents/todos 配置"""
        layout = CompactLayout()

        # 尝试通过 update_config 禁用
        layout.update_config({
            "show_tools": False,
            "show_agents": False,
            "show_todos": False
        })

        # 验证仍然启用
        assert layout.supports_component("tools")
        assert layout.supports_component("agents")
        assert layout.supports_component("todos")
