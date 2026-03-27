"""
主题系统

提供主题定义、管理和应用功能。
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum


class ThemeColor(Enum):
    """主题颜色枚举"""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"
    MUTED = "muted"


@dataclass
class ThemeColors:
    """主题颜色定义"""
    primary: str = "\x1b[34m"  # 蓝色
    secondary: str = "\x1b[36m"  # 青色
    success: str = "\x1b[32m"  # 绿色
    warning: str = "\x1b[33m"  # 黄色
    error: str = "\x1b[31m"  # 红色
    info: str = "\x1b[36m"  # 青色
    muted: str = "\x1b[90m"  # 灰色
    reset: str = "\x1b[0m"  # 重置

    def get_color(self, color_type: ThemeColor) -> str:
        """
        获取颜色代码

        Args:
            color_type: 颜色类型

        Returns:
            ANSI 颜色代码
        """
        color_map = {
            ThemeColor.PRIMARY: self.primary,
            ThemeColor.SECONDARY: self.secondary,
            ThemeColor.SUCCESS: self.success,
            ThemeColor.WARNING: self.warning,
            ThemeColor.ERROR: self.error,
            ThemeColor.INFO: self.info,
            ThemeColor.MUTED: self.muted,
        }
        return color_map.get(color_type, self.reset)

    def apply(self, text: str, color_type: ThemeColor) -> str:
        """
        应用颜色到文本

        Args:
            text: 文本
            color_type: 颜色类型

        Returns:
            着色后的文本
        """
        color = self.get_color(color_type)
        return f"{color}{text}{self.reset}"


@dataclass
class ThemeStyles:
    """主题样式定义"""
    bold: bool = False
    dim: bool = False
    italic: bool = False
    underline: bool = False

    def to_ansi(self) -> str:
        """
        转换为 ANSI 代码

        Returns:
            ANSI 样式代码
        """
        codes = []
        if self.bold:
            codes.append("1")
        if self.dim:
            codes.append("2")
        if self.italic:
            codes.append("3")
        if self.underline:
            codes.append("4")

        if codes:
            return f"\x1b[{';'.join(codes)}m"
        return ""


@dataclass
class ThemeSymbols:
    """主题符号定义"""
    progress_filled: str = "█"
    progress_empty: str = "░"
    error: str = "✖"
    warning: str = "⚠"
    success: str = "✔"
    info: str = "ℹ"
    thinking: str = "◐"
    idle: str = "○"


@dataclass
class Theme:
    """
    主题定义

    包含颜色、样式和符号的完整主题。
    """
    name: str
    colors: ThemeColors = field(default_factory=ThemeColors)
    styles: ThemeStyles = field(default_factory=ThemeStyles)
    symbols: ThemeSymbols = field(default_factory=ThemeSymbols)

    def apply_color(self, text: str, color_type: ThemeColor) -> str:
        """
        应用颜色到文本

        Args:
            text: 文本
            color_type: 颜色类型

        Returns:
            着色后的文本
        """
        return self.colors.apply(text, color_type)

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典

        Returns:
            主题字典
        """
        return {
            "name": self.name,
            "colors": {
                "primary": self.colors.primary,
                "secondary": self.colors.secondary,
                "success": self.colors.success,
                "warning": self.colors.warning,
                "error": self.colors.error,
                "info": self.colors.info,
                "muted": self.colors.muted,
            },
            "styles": {
                "bold": self.styles.bold,
                "dim": self.styles.dim,
                "italic": self.styles.italic,
                "underline": self.styles.underline,
            },
            "symbols": {
                "progress_filled": self.symbols.progress_filled,
                "progress_empty": self.symbols.progress_empty,
                "error": self.symbols.error,
                "warning": self.symbols.warning,
                "success": self.symbols.success,
                "info": self.symbols.info,
                "thinking": self.symbols.thinking,
                "idle": self.symbols.idle,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Theme':
        """
        从字典创建主题

        Args:
            data: 主题字典

        Returns:
            主题对象
        """
        colors_data = data.get("colors", {})
        styles_data = data.get("styles", {})
        symbols_data = data.get("symbols", {})

        return cls(
            name=data["name"],
            colors=ThemeColors(**colors_data),
            styles=ThemeStyles(**styles_data),
            symbols=ThemeSymbols(**symbols_data),
        )


class ThemeManager:
    """
    主题管理器

    管理主题的加载、注册和应用。
    """

    # 内置主题
    BUILTIN_THEMES = {
        "default": Theme(
            name="default",
            colors=ThemeColors(),
            styles=ThemeStyles(),
            symbols=ThemeSymbols(),
        ),
        "minimal": Theme(
            name="minimal",
            colors=ThemeColors(
                primary="",
                secondary="",
                success="",
                warning="",
                error="",
                info="",
                muted="",
                reset="",
            ),
            styles=ThemeStyles(),
            symbols=ThemeSymbols(
                progress_filled="=",
                progress_empty="-",
                error="x",
                warning="!",
                success="ok",
                info="i",
                thinking="...",
                idle="-",
            ),
        ),
        "colorful": Theme(
            name="colorful",
            colors=ThemeColors(
                primary="\x1b[35m",  # 紫色
                secondary="\x1b[94m",  # 亮蓝色
                success="\x1b[92m",  # 亮绿色
                warning="\x1b[93m",  # 亮黄色
                error="\x1b[91m",  # 亮红色
                info="\x1b[96m",  # 亮青色
                muted="\x1b[37m",  # 白色
            ),
            styles=ThemeStyles(bold=True),
            symbols=ThemeSymbols(),
        ),
        "dark": Theme(
            name="dark",
            colors=ThemeColors(
                primary="\x1b[36m",  # 青色
                secondary="\x1b[34m",  # 蓝色
                success="\x1b[32m",  # 绿色
                warning="\x1b[33m",  # 黄色
                error="\x1b[31m",  # 红色
                info="\x1b[35m",  # 紫色
                muted="\x1b[90m",  # 灰色
            ),
            styles=ThemeStyles(),
            symbols=ThemeSymbols(),
        ),
        "light": Theme(
            name="light",
            colors=ThemeColors(
                primary="\x1b[94m",  # 亮蓝色
                secondary="\x1b[96m",  # 亮青色
                success="\x1b[92m",  # 亮绿色
                warning="\x1b[93m",  # 亮黄色
                error="\x1b[91m",  # 亮红色
                info="\x1b[95m",  # 亮紫色
                muted="\x1b[37m",  # 白色
            ),
            styles=ThemeStyles(),
            symbols=ThemeSymbols(),
        ),
    }

    def __init__(self):
        """初始化主题管理器"""
        self._themes: Dict[str, Theme] = {}
        self._current_theme: Optional[Theme] = None

        # 注册内置主题
        for theme in self.BUILTIN_THEMES.values():
            self.register_theme(theme)

    def load_theme(self, name: str) -> Theme:
        """
        加载主题

        Args:
            name: 主题名称

        Returns:
            主题对象

        Raises:
            ValueError: 主题不存在
        """
        if name not in self._themes:
            raise ValueError(f"Theme '{name}' not found. Available: {self.list_themes()}")

        self._current_theme = self._themes[name]
        return self._current_theme

    def register_theme(self, theme: Theme) -> None:
        """
        注册主题

        Args:
            theme: 主题对象
        """
        self._themes[theme.name] = theme

    def unregister_theme(self, name: str) -> None:
        """
        注销主题

        Args:
            name: 主题名称
        """
        if name in self._themes:
            del self._themes[name]

    def list_themes(self) -> List[str]:
        """
        列出可用主题

        Returns:
            主题名称列表
        """
        return list(self._themes.keys())

    def get_current_theme(self) -> Optional[Theme]:
        """
        获取当前主题

        Returns:
            当前主题对象
        """
        return self._current_theme

    def apply_theme(self, theme: Theme) -> None:
        """
        应用主题

        Args:
            theme: 主题对象
        """
        self._current_theme = theme

    def load_from_file(self, path: Path) -> Theme:
        """
        从文件加载主题

        Args:
            path: 主题文件路径（JSON 格式）

        Returns:
            主题对象
        """
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        theme = Theme.from_dict(data)
        self.register_theme(theme)
        return theme

    def save_to_file(self, theme: Theme, path: Path) -> None:
        """
        保存主题到文件

        Args:
            theme: 主题对象
            path: 保存路径
        """
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(theme.to_dict(), f, indent=2, ensure_ascii=False)
