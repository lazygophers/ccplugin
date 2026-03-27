"""
扩展布局

展示完整信息的布局模式。
"""

from typing import Dict, Any, Optional
from ..tracker.aggregator import AggregatedState
from ..utils.formatting import (
    format_token_count,
    format_duration,
    format_percentage,
    progress_bar,
    join_parts,
)

from .base import Layout


class ExpandedLayout(Layout):
    """
    扩展布局

    展示完整的状态信息，包括用户状态、进度、资源等。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化扩展布局

        Args:
            config: 布局配置
        """
        super().__init__(config)
        self._progress_width = self._get_config("progress_width", 12)

    def render(self, state: AggregatedState) -> str:
        """
        渲染状态为字符串

        Args:
            state: 聚合状态

        Returns:
            渲染后的字符串
        """
        parts = []

        # 用户状态
        if self._components.get("user"):
            user_part = self._render_user_status(state)
            if user_part:
                parts.append(user_part)

        # 进度信息
        if self._components.get("progress"):
            progress_part = self._render_progress(state)
            if progress_part:
                parts.append(progress_part)

        # 资源信息
        if self._components.get("resources"):
            resource_part = self._render_resources(state)
            if resource_part:
                parts.append(resource_part)

        # 错误信息
        if self._components.get("errors"):
            error_part = self._render_errors(state)
            if error_part:
                parts.append(error_part)

        # 工具信息
        if self._components.get("tools"):
            tools_part = self._render_tools(state)
            if tools_part:
                parts.append(tools_part)

        # Agent 信息
        if self._components.get("agents"):
            agents_part = self._render_agents(state)
            if agents_part:
                parts.append(agents_part)

        # Todo 信息
        if self._components.get("todos"):
            todos_part = self._render_todos(state)
            if todos_part:
                parts.append(todos_part)

        return join_parts(parts, sep=" | ")

    def get_width(self) -> int:
        """
        获取布局宽度

        Returns:
            布局宽度
        """
        return self._get_config("width", 80)

    def _render_user_status(self, state: AggregatedState) -> Optional[str]:
        """
        渲染用户状态

        Args:
            state: 聚合状态

        Returns:
            用户状态字符串
        """
        status_map = {
            "idle": "空闲",
            "inputting": "输入中",
            "thinking": "思考中",
            "responding": "响应中",
        }

        status = "空闲"
        if isinstance(state.value, dict):
            status = state.value.get("status", "idle")
        elif isinstance(state.value, str):
            status = state.value

        return f"[{status_map.get(status, status)}]"

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
        bar = progress_bar(percentage, width=self._progress_width)
        pct_str = format_percentage(percentage)

        return f"{bar} {pct_str}"

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
        duration = state.value.get("duration_ms", 0)

        token_str = format_token_count(tokens)
        duration_str = format_duration(duration)

        return f"[{token_str} tokens] [{duration_str}]"

    def _render_errors(self, state: AggregatedState) -> Optional[str]:
        """
        渲染错误信息

        Args:
            state: 聚合状态

        Returns:
            错误字符串
        """
        if not isinstance(state.value, dict):
            return None

        count = state.value.get("count", 0)
        if count == 0:
            return None

        return f"[{count} errors]"

    def _render_tools(self, state: AggregatedState) -> Optional[str]:
        """
        渲染工具信息

        Args:
            state: 聚合状态

        Returns:
            工具字符串
        """
        if not isinstance(state.value, dict):
            return None

        active_count = state.value.get("active_count", 0)
        if active_count == 0:
            return None

        active = state.value.get("active", [])
        if active:
            tool_names = ", ".join(t.get("name", "?") for t in active[:3])
            return f"[工具: {tool_names} ({active_count} active)]"

        return f"[工具: ({active_count} active)]"

    def _render_agents(self, state: AggregatedState) -> Optional[str]:
        """
        渲染 Agent 信息

        Args:
            state: 聚合状态

        Returns:
            Agent 字符串
        """
        if not isinstance(state.value, dict):
            return None

        active_count = state.value.get("active_count", 0)
        if active_count == 0:
            return None

        active = state.value.get("active", [])
        if active:
            agent_names = ", ".join(a.get("name", "?") for a in active[:2])
            return f"[Agent: {agent_names} ({active_count} running)]"

        return f"[Agent: ({active_count} running)]"

    def _render_todos(self, state: AggregatedState) -> Optional[str]:
        """
        渲染 Todo 信息

        Args:
            state: 聚合状态

        Returns:
            Todo 字符串
        """
        if not isinstance(state.value, dict):
            return None

        total = state.value.get("total", 0)
        completed = state.value.get("completed", 0)

        if total == 0:
            return None

        percentage = state.value.get("percentage", 0)
        return f"[Todo: {completed}/{total} ({percentage:.0f}%)]"
