"""
配置管理器

提供配置管理、验证和默认值功能。
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from enum import Enum


class LayoutMode(Enum):
    """布局模式"""
    EXPANDED = "expanded"
    COMPACT = "compact"


@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    ttl: int = 60  # 秒
    max_size: int = 1000


@dataclass
class RefreshConfig:
    """刷新配置"""
    interval: float = 0.1  # 秒
    incremental: bool = True


@dataclass
class Config:
    """配置类"""

    # 布局配置
    layout_mode: LayoutMode = LayoutMode.EXPANDED
    layout_width: int = 80

    # 主题配置
    theme: str = "default"

    # 刷新配置
    refresh: RefreshConfig = field(default_factory=RefreshConfig)

    # 缓存配置
    cache: CacheConfig = field(default_factory=CacheConfig)

    # 显示配置
    show_user: bool = True
    show_progress: bool = True
    show_resources: bool = True
    show_errors: bool = True

    # 其他配置
    verbose: bool = False
    debug: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 转换枚举
        data['layout_mode'] = self.layout_mode.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """从字典创建"""
        # 转换枚举
        if 'layout_mode' in data and isinstance(data['layout_mode'], str):
            data['layout_mode'] = LayoutMode(data['layout_mode'])

        # 处理嵌套配置
        if 'refresh' in data and isinstance(data['refresh'], dict):
            data['refresh'] = RefreshConfig(**data['refresh'])
        if 'cache' in data and isinstance(data['cache'], dict):
            data['cache'] = CacheConfig(**data['cache'])

        return cls(**data)

    def validate(self) -> List[str]:
        """验证配置，返回错误列表"""
        errors = []

        if self.layout_width <= 0:
            errors.append("layout_width must be positive")

        if self.refresh.interval <= 0:
            errors.append("refresh.interval must be positive")

        if self.cache.ttl <= 0:
            errors.append("cache.ttl must be positive")

        if self.cache.max_size <= 0:
            errors.append("cache.max_size must be positive")

        return errors


def get_default_config() -> Config:
    """获取默认配置"""
    return Config()


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self._config: Optional[Config] = None
        self._watchers: List[callable] = []

    def load(self, config_path: Optional[Path] = None) -> Config:
        """
        加载配置

        Args:
            config_path: 配置文件路径，可选

        Returns:
            配置对象
        """
        if config_path:
            self.config_path = config_path

        # 从文件加载
        if self.config_path and self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._config = Config.from_dict(data)
        else:
            # 从环境变量加载
            self._config = self._load_from_env()

        # 验证配置
        errors = self._config.validate()
        if errors:
            raise ValueError(f"Invalid configuration: {', '.join(errors)}")

        return self._config

    def save(self, config_path: Optional[Path] = None) -> None:
        """
        保存配置

        Args:
            config_path: 配置文件路径，可选
        """
        if config_path:
            self.config_path = config_path

        if not self.config_path:
            raise ValueError("config_path not set")

        # 确保目录存在
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存配置
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self._config.to_dict(), f, indent=2, ensure_ascii=False)

    def get(self) -> Config:
        """
        获取当前配置

        Returns:
            配置对象
        """
        if self._config is None:
            self._config = get_default_config()
        return self._config

    def update(self, **kwargs) -> None:
        """
        更新配置

        Args:
            **kwargs: 配置项
        """
        config = self.get()
        config_dict = config.to_dict()

        # 更新配置项
        for key, value in kwargs.items():
            if key in config_dict:
                config_dict[key] = value
            else:
                raise ValueError(f"Unknown config key: {key}")

        # 重新创建配置对象
        self._config = Config.from_dict(config_dict)

        # 验证配置
        errors = self._config.validate()
        if errors:
            raise ValueError(f"Invalid configuration: {', '.join(errors)}")

        # 通知监听器
        self._notify_watchers()

    def reload(self) -> Config:
        """
        重新加载配置

        Returns:
            配置对象
        """
        self._config = None
        return self.load()

    def watch(self, callback: callable) -> None:
        """
        监听配置变化

        Args:
            callback: 回调函数
        """
        self._watchers.append(callback)

    def _load_from_env(self) -> Config:
        """
        从环境变量加载配置

        Returns:
            配置对象
        """
        config = get_default_config()

        # 从环境变量读取
        if 'STATUSLINE_LAYOUT' in os.environ:
            config.layout_mode = LayoutMode(os.environ['STATUSLINE_LAYOUT'])
        if 'STATUSLINE_THEME' in os.environ:
            config.theme = os.environ['STATUSLINE_THEME']
        if 'STATUSLINE_WIDTH' in os.environ:
            config.layout_width = int(os.environ['STATUSLINE_WIDTH'])
        if 'STATUSLINE_VERBOSE' in os.environ:
            config.verbose = os.environ['STATUSLINE_VERBOSE'].lower() == 'true'
        if 'STATUSLINE_DEBUG' in os.environ:
            config.debug = os.environ['STATUSLINE_DEBUG'].lower() == 'true'

        return config

    def _notify_watchers(self) -> None:
        """通知配置变化监听器"""
        for callback in self._watchers:
            callback(self._config)
