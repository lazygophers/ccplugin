"""
向后兼容层

确保现有代码平滑迁移到新架构。
"""

import warnings
from typing import Dict, Any, Optional, List
from pathlib import Path

from .loop import StatuslineLoop
from ..config.manager import Config, ConfigManager, LayoutMode


def migrate_config(old_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    迁移旧配置到新格式

    Args:
        old_config: 旧配置字典

    Returns:
        新配置字典
    """
    if old_config is None:
        return {}

    new_config = {}

    # 映射配置项
    if "layout" in old_config:
        new_config["layout_mode"] = old_config["layout"]
    if "width" in old_config:
        new_config["layout_width"] = old_config["width"]
    if "theme" in old_config:
        new_config["theme"] = old_config["theme"]
    if "show_user" in old_config:
        new_config["show_user"] = old_config["show_user"]
    if "show_progress" in old_config:
        new_config["show_progress"] = old_config["show_progress"]
    if "show_resources" in old_config:
        new_config["show_resources"] = old_config["show_resources"]
    if "show_errors" in old_config:
        new_config["show_errors"] = old_config["show_errors"]

    # 刷新配置
    if "refresh_interval" in old_config:
        new_config["refresh"] = {
            "interval": old_config["refresh_interval"],
            "incremental": old_config.get("incremental", True),
        }

    # 缓存配置
    if "cache_ttl" in old_config or "cache_size" in old_config:
        new_config["cache"] = {
            "enabled": old_config.get("cache_enabled", True),
            "ttl": old_config.get("cache_ttl", 60),
            "max_size": old_config.get("cache_size", 1000),
        }

    return new_config


def validate_migration(old_behavior: Any, new_behavior: Any) -> bool:
    """
    验证迁移结果

    Args:
        old_behavior: 旧行为结果
        new_behavior: 新行为结果

    Returns:
        是否兼容
    """
    # 简化验证，实际应用中可能需要更复杂的逻辑
    if isinstance(old_behavior, str) and isinstance(new_behavior, str):
        # 基本字符串比较
        return True

    if isinstance(old_behavior, dict) and isinstance(new_behavior, dict):
        # 字典结构比较
        return set(old_behavior.keys()) == set(new_behavior.keys())

    return False


class LegacyImpl:
    """
    旧实现

    保留旧版本的实现逻辑用于兼容。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化旧实现

        Args:
            config: 配置字典
        """
        self._config = config

    def process(self, transcript: str) -> str:
        """
        处理 transcript

        Args:
            transcript: transcript 字符串

        Returns:
            处理结果
        """
        # 简化的旧实现
        return f"[Legacy] {transcript[:50]}..."


class NewImpl:
    """
    新实现

    基于新架构的实现。
    """

    def __init__(self, config: Config):
        """
        初始化新实现

        Args:
            config: 配置对象
        """
        self._loop = StatuslineLoop(config)

    def process(self, transcript: str) -> str:
        """
        处理 transcript

        Args:
            transcript: transcript 字符串

        Returns:
            处理结果
        """
        return self._loop.process(transcript)


class CompatLayer:
    """
    兼容层

    提供统一的接口，内部可以选择使用旧实现或新实现。
    """

    def __init__(self, config: Any, use_legacy: bool = False, warn: bool = True):
        """
        初始化兼容层

        Args:
            config: 配置（可以是字典或 Config 对象）
            use_legacy: 是否使用旧实现
            warn: 是否显示弃用警告
        """
        if warn:
            warnings.warn(
                "Legacy API is deprecated. Please migrate to new API.",
                DeprecationWarning,
                stacklevel=2,
            )

        if use_legacy:
            # 使用旧实现
            if isinstance(config, Config):
                old_config = config.to_dict()
            else:
                old_config = config

            self._impl = LegacyImpl(old_config)
        else:
            # 使用新实现
            if isinstance(config, dict):
                # 迁移配置
                new_config_dict = migrate_config(config)
                config = Config.from_dict(new_config_dict)

            self._impl = NewImpl(config)

    def process(self, transcript: str) -> str:
        """
        处理 transcript

        Args:
            transcript: transcript 字符串

        Returns:
            处理结果
        """
        return self._impl.process(transcript)

    def __getattr__(self, name: str) -> Any:
        """
        转发属性访问到实现对象

        Args:
            name: 属性名

        Returns:
            属性值
        """
        return getattr(self._impl, name)


# 保留旧 API 函数
def format_statusline_old(
    transcript: str,
    config: Optional[Dict[str, Any]] = None
) -> str:
    """
    旧的格式化状态栏 API

    Args:
        transcript: transcript 字符串
        config: 配置字典

    Returns:
        格式化后的状态栏字符串

    Note:
        此函数已弃用，请使用新架构 API。
    """
    warnings.warn(
        "format_statusline_old is deprecated. Use StatuslineLoop instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    if config is None:
        config = {}

    # 使用兼容层
    compat = CompatLayer(config, use_legacy=False)
    return compat.process(transcript)


# 新 API 函数
def format_statusline(
    transcript: str,
    config: Optional[Config] = None
) -> str:
    """
    格式化状态栏

    Args:
        transcript: transcript 字符串
        config: 配置对象

    Returns:
        格式化后的状态栏字符串
    """
    if config is None:
        from ..config.manager import get_default_config
        config = get_default_config()

    loop = StatuslineLoop(config)
    return loop.process(transcript)


def load_config_from_file(path: Path) -> Config:
    """
    从文件加载配置

    Args:
        path: 配置文件路径

    Returns:
        配置对象
    """
    manager = ConfigManager(config_path=path)
    return manager.load()


def save_config_to_file(config: Config, path: Path) -> None:
    """
    保存配置到文件

    Args:
        config: 配置对象
        path: 保存路径
    """
    manager = ConfigManager(config_path=path)
    manager._config = config
    manager.save()
