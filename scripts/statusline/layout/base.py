"""
布局基类

定义布局系统的抽象接口和通用功能。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from ..tracker.aggregator import AggregatedState


class Layout(ABC):
    """
    布局基类

    所有布局的抽象基类，定义统一的接口。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化布局

        Args:
            config: 布局配置
        """
        self._config = config or {}
        self._components: Dict[str, bool] = {
            "user": self._config.get("show_user", True),
            "progress": self._config.get("show_progress", True),
            "resources": self._config.get("show_resources", True),
            "errors": self._config.get("show_errors", True),
            "tools": True,   # 始终启用
            "agents.bak": True,  # 始终启用
            "todos": True,   # 始终启用
        }

    @abstractmethod
    def render(self, state: AggregatedState) -> str:
        """
        渲染状态为字符串

        Args:
            state: 聚合状态

        Returns:
            渲染后的字符串
        """
        pass

    @abstractmethod
    def get_width(self) -> int:
        """
        获取布局宽度

        Returns:
            布局宽度（字符数）
        """
        pass

    def validate(self) -> bool:
        """
        验证布局配置

        Returns:
            是否有效
        """
        try:
            self._validate_config()
            return True
        except Exception:
            return False

    def supports_component(self, component: str) -> bool:
        """
        检查是否支持特定组件

        Args:
            component: 组件名称

        Returns:
            是否支持
        """
        return component in self._components and self._components[component]

    def enable_component(self, component: str) -> None:
        """
        启用组件

        Args:
            component: 组件名称

        Note:
            tools, agents.bak, todos 组件始终启用，不能被禁用
        """
        if component in ("tools", "agents.bak", "todos"):
            # 这些组件始终启用，忽略禁用请求
            return

        if component in self._components:
            self._components[component] = True

    def disable_component(self, component: str) -> None:
        """
        禁用组件

        Args:
            component: 组件名称

        Note:
            tools, agents.bak, todos 组件始终启用，不能被禁用
        """
        if component in ("tools", "agents.bak", "todos"):
            # 这些组件始终启用，忽略禁用请求
            return

        if component in self._components:
            self._components[component] = False

    def update_config(self, config: Dict[str, Any]) -> None:
        """
        更新配置

        Args:
            config: 配置字典

        Note:
            tools, agents.bak, todos 组件始终启用，忽略相关配置
        """
        self._config.update(config)

        # 更新可配置组件的显示状态
        if "show_user" in config:
            self._components["user"] = config["show_user"]
        if "show_progress" in config:
            self._components["progress"] = config["show_progress"]
        if "show_resources" in config:
            self._components["resources"] = config["show_resources"]
        if "show_errors" in config:
            self._components["errors"] = config["show_errors"]

        # tools/agents.bak/todos 组件始终启用，忽略配置中的设置
        # 如果配置中包含这些选项，静默忽略以保持向后兼容

    def _validate_config(self) -> None:
        """
        验证配置的具体实现

        Raises:
            ValueError: 配置无效
        """
        width = self._config.get("width", 80)
        if width <= 0:
            raise ValueError(f"Invalid width: {width}")

    def _get_config(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值
        """
        return self._config.get(key, default)
