"""
验证工具函数

提供配置、布局、主题等验证功能。
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from ..config.manager import Config, LayoutMode


def validate_config(config: Config) -> List[str]:
    """
    验证配置

    Args:
        config: 配置对象

    Returns:
        错误列表，空列表表示无错误
    """
    return config.validate()


def validate_config_dict(data: Dict[str, Any]) -> List[str]:
    """
    验证配置字典

    Args:
        data: 配置字典

    Returns:
        错误列表
    """
    errors = []

    # 处理 None 输入
    if data is None:
        return ["Config cannot be None"]

    # 验证布局模式
    if "layout_mode" in data:
        if not validate_layout(data["layout_mode"]):
            errors.append(f"Invalid layout_mode: {data['layout_mode']}")

    # 验证宽度
    if "layout_width" in data:
        if not validate_width(data["layout_width"]):
            errors.append(f"Invalid layout_width: {data['layout_width']}")

    # 验证刷新间隔
    if "refresh" in data and isinstance(data["refresh"], dict):
        interval = data["refresh"].get("interval")
        if interval is not None and interval <= 0:
            errors.append("refresh.interval must be positive")

    # 验证缓存 TTL
    if "cache" in data and isinstance(data["cache"], dict):
        ttl = data["cache"].get("ttl")
        if ttl is not None and ttl <= 0:
            errors.append("cache.ttl must be positive")

    return errors


def validate_layout(layout: str) -> bool:
    """
    验证布局模式

    Args:
        layout: 布局模式字符串

    Returns:
        是否有效
    """
    try:
        LayoutMode(layout)
        return True
    except ValueError:
        return False


def validate_theme(theme: str, available_themes: Optional[List[str]] = None) -> bool:
    """
    验证主题名称

    Args:
        theme: 主题名称
        available_themes: 可用主题列表

    Returns:
        是否有效
    """
    if not theme:
        return False

    if available_themes is None:
        # 默认主题列表
        available_themes = ["default", "minimal", "colorful", "dark", "light"]

    return theme in available_themes


def validate_width(width: int, min_width: int = 10, max_width: int = 200) -> bool:
    """
    验证宽度值

    Args:
        width: 宽度值
        min_width: 最小宽度
        max_width: 最大宽度

    Returns:
        是否有效
    """
    return min_width <= width <= max_width


def validate_percentage(value: float) -> bool:
    """
    验证百分比值

    Args:
        value: 百分比值

    Returns:
        是否有效 (0-100)
    """
    return 0 <= value <= 100


def validate_color_rgb(rgb: tuple) -> bool:
    """
    验证 RGB 颜色值

    Args:
        rgb: RGB 元组 (r, g, b)

    Returns:
        是否有效
    """
    if not isinstance(rgb, (tuple, list)) or len(rgb) != 3:
        return False

    return all(0 <= c <= 255 for c in rgb)


def validate_path(path: Any) -> bool:
    """
    验证路径是否存在

    Args:
        path: 路径（Path 对象、字符串或 None）

    Returns:
        是否有效且存在
    """
    if path is None:
        return False

    if isinstance(path, str):
        if not path:
            return False
        path = Path(path)

    if not isinstance(path, Path):
        return False

    return path.exists()
