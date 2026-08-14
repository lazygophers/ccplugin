"""
布局工厂

提供布局注册和创建功能。
"""

from typing import Dict, Type, List, Optional, Any
from ..config.manager import Config

from .base import Layout


class LayoutFactory:
    """
    布局工厂

    管理布局类型的注册和创建。
    """

    _layouts: Dict[str, Type[Layout]] = {}

    @classmethod
    def register(cls, name: str, layout_cls: Type[Layout]) -> None:
        """
        注册布局类型

        Args:
            name: 布局名称
            layout_cls: 布局类

        Raises:
            ValueError: 布局类无效或名称已存在
        """
        if not issubclass(layout_cls, Layout):
            raise ValueError(f"{layout_cls} must be a subclass of Layout")

        if name in cls._layouts:
            raise ValueError(f"Layout '{name}' is already registered")

        cls._layouts[name] = layout_cls

    @classmethod
    def unregister(cls, name: str) -> None:
        """
        注销布局类型

        Args:
            name: 布局名称
        """
        if name in cls._layouts:
            del cls._layouts[name]

    @classmethod
    def create(cls, name: str, config: Optional[Dict[str, Any]] = None) -> Layout:
        """
        创建布局实例

        Args:
            name: 布局名称
            config: 配置字典

        Returns:
            布局实例

        Raises:
            ValueError: 布局类型未注册
        """
        if name not in cls._layouts:
            raise ValueError(f"Unknown layout: {name}. Available: {cls.list_available()}")

        layout_cls = cls._layouts[name]
        return layout_cls(config)

    @classmethod
    def create_from_config(cls, config: Config) -> Layout:
        """
        从配置创建布局

        Args:
            config: 配置对象

        Returns:
            布局实例
        """
        layout_mode = config.layout_mode.value
        layout_config = {
            "width": config.layout_width,
            "show_user": config.show_user,
            "show_progress": config.show_progress,
            "show_resources": config.show_resources,
            "show_errors": config.show_errors,
        }

        return cls.create(layout_mode, layout_config)

    @classmethod
    def list_available(cls) -> List[str]:
        """
        列出可用布局

        Returns:
            布局名称列表
        """
        return list(cls._layouts.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """
        检查布局是否已注册

        Args:
            name: 布局名称

        Returns:
            是否已注册
        """
        return name in cls._layouts

    @classmethod
    def clear(cls) -> None:
        """清空所有注册的布局"""
        cls._layouts.clear()
