"""
紧凑布局

优化空间利用的布局模式。
"""

from typing import Dict, Any, Optional
from ..tracker.aggregator import AggregatedState
from ..utils.formatting import (
    format_token_count,
    format_percentage,
    join_parts,
)

from .base import Layout


class CompactLayout(Layout):
    """
    紧凑布局

    优化空间利用，使用符号和缩写。
    """

    # 状态符号映射
    STATUS_SYMBOLS = {
        "idle": "○",
        "inputting": "●",
        "thinking": "◐",
        "responding": "◑",
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化紧凑布局

        Args:
            config: 布局配置
        """
        super().__init__(config)
        self._max_width = self._get_config("max_width", 30)
        self._use_symbols = self._get_config("show_symbols", True)
        self._abbreviate = self._get_config("abbreviate", True)
        self._priority = self._get_config(
            "priority", ["progress", "tokens", "status"]
        )

    def render(self, state: AggregatedState) -> str:
        """
        渲染状态为字符串

        Args:
            state: 聚合状态

        Returns:
            渲染后的字符串（单行）
        """
        parts_map = {}

        # 收集所有组件
        if self._components.get("user"):
            user_part = self._render_user_status(state)
            if user_part:
                parts_map["status"] = user_part

        if self._components.get("progress"):
            progress_part = self._render_progress(state)
            if progress_part:
                parts_map["progress"] = progress_part

        if self._components.get("resources"):
            resource_part = self._render_resources(state)
            if resource_part:
                parts_map["tokens"] = resource_part

        # 按优先级排序并选择
        parts = []
        remaining_width = self._max_width

        for priority in self._priority:
            if priority not in parts_map:
                continue

            part = parts_map[priority]
            part_width = len(part)

            if remaining_width >= part_width + 2:  # +2 for separator
                parts.append(part)
                remaining_width -= part_width + 2
            else:
                break

        return join_parts(parts, sep=" | ") if parts else ""

    def get_width(self) -> int:
        """
        获取布局宽度

        Returns:
            布局宽度
        """
        return self._max_width

    def _render_user_status(self, state: AggregatedState) -> Optional[str]:
        """
        渲染用户状态

        Args:
            state: 聚合状态

        Returns:
            用户状态字符串
        """
        status = "idle"
        if isinstance(state.value, dict):
            status = state.value.get("status", "idle")
        elif isinstance(state.value, str):
            status = state.value

        if self._use_symbols:
            return self.STATUS_SYMBOLS.get(status, "○")

        # 使用缩写
        abbreviations = {
            "idle": "IDLE",
            "inputting": "INP",
            "thinking": "THK",
            "responding": "RSP",
        }

        if self._abbreviate:
            return abbreviations.get(status, status.upper()[:3])

        return status.capitalize()

    def _render_progress(self, state: AggregatedState) -> Optional[str]:
        """
        渲染进度信息

        Args:
            state: 聚合状态

        Returns:
            进度字符串
        """
        if not isinstance(state.value, dict):
            return None

        percentage = state.value.get("percentage", 0)
        return format_percentage(percentage, decimals=0)

    def _render_resources(self, state: AggregatedState) -> Optional[str]:
        """
        渲染资源信息

        Args:
            state: 聚合状态

        Returns:
            资源字符串
        """
        if not isinstance(state.value, dict):
            return None

        tokens = state.value.get("tokens", 0)
        return format_token_count(tokens)
