"""
紧凑布局

优化空间利用的布局模式。
"""

from typing import Dict, Any, Optional
from ..tracker.aggregator import AggregatedState
from ..utils.formatting import (
    format_token_count,
    format_percentage,
    format_duration_ms,
    progress_bar,
    shorten_path,
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
        self._max_lines = self._get_config("max_lines", 2)
        self._separator_primary = self._get_config("separator_primary", " · ")
        self._separator_secondary = self._get_config("separator_secondary", " | ")
        self._progress_bar_width = self._get_config("progress_bar_width", 12)
        self._show_model = self._get_config("show_model", True)
        self._show_cost = self._get_config("show_cost", True)
        self._show_git = self._get_config("show_git", True)
        self._use_symbols = self._get_config("show_symbols", True)
        self._abbreviate = self._get_config("abbreviate", True)
        self._priority = self._get_config(
            "priority", ["progress", "tokens", "status"]
        )

    def render(self, state: AggregatedState) -> str:
        """
        渲染状态为多行字符串

        Args:
            state: 聚合状态

        Returns:
            渲染后的字符串（多行或单行）
        """
        lines = []

        # Line 1: 主要信息（模型、成本、时长）
        line1 = self._render_line1_primary(state)
        if line1:
            lines.append(line1)

        # Line 2: 次要信息（Git、路径）
        line2 = self._render_line2_secondary(state)
        if line2:
            lines.append(line2)

        # Line 3: 详细信息（进度、活动）
        if self._max_lines >= 3:
            line3 = self._render_line3_tertiary(state)
            if line3:
                lines.append(line3)

        # 如果没有生成任何行，使用传统的单行渲染（向后兼容）
        if not lines:
            return self._render_legacy(state)

        return "\n".join(lines)

    def _render_legacy(self, state: AggregatedState) -> str:
        """
        传统单行渲染（向后兼容）

        Args:
            state: 聚合状态

        Returns:
            传统格式的单行字符串
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

        if self._components.get("tools"):
            tools_part = self._render_tools(state)
            if tools_part:
                parts_map["tools"] = tools_part

        if self._components.get("agents"):
            agents_part = self._render_agents(state)
            if agents_part:
                parts_map["agents"] = agents_part

        if self._components.get("todos"):
            todos_part = self._render_todos(state)
            if todos_part:
                parts_map["todos"] = todos_part

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

    def _render_tools(self, state: AggregatedState) -> Optional[str]:
        """
        渲染工具信息（累计计数）

        Args:
            state: 聚合状态

        Returns:
            工具字符串
        """
        if not isinstance(state.value, dict):
            return None

        count = state.value.get("history_count", 0)
        return f"🔧{count}"

    def _render_agents(self, state: AggregatedState) -> Optional[str]:
        """
        渲染 Agent 信息（累计计数）

        Args:
            state: 聚合状态

        Returns:
            Agent 字符串
        """
        if not isinstance(state.value, dict):
            return None

        count = state.value.get("history_count", 0)
        return f"🤖{count}"

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

        return f"✓{completed}/{total}"

    def _render_line1_primary(self, state: AggregatedState) -> str:
        """
        渲染主要信息行

        格式: Model · Tokens (Cost)
        示例: GLM-4.7 · 204K（$26.97）

        Args:
            state: 聚合状态

        Returns:
            主要信息行字符串
        """
        parts = []

        if self._show_model:
            model_part = self._render_model(state)
            if model_part:
                parts.append(model_part)

        if self._components.get("resources"):
            resource_part = self._render_tokens_cost(state)
            if resource_part:
                parts.append(resource_part)

        return join_parts(parts, sep=self._separator_primary) if parts else ""

    def _render_line2_secondary(self, state: AggregatedState) -> str:
        """
        渲染次要信息行

        格式: ⎇ branch · +ins -del | path
        示例: ⎇ cdp 19 · +6653 -409 | ~/zhibao/tmtc_bg

        Args:
            state: 聚合状态

        Returns:
            次要信息行字符串
        """
        parts = []

        if self._show_git:
            git_part = self._render_git_compact(state)
            if git_part:
                parts.append(git_part)

        path_part = self._render_path_compact(state)
        if path_part:
            parts.append(path_part)

        return join_parts(parts, sep=self._separator_secondary) if parts else ""

    def _render_line3_tertiary(self, state: AggregatedState) -> str:
        """
        渲染详细信息行

        格式: ████░░░░ 75% · 🔧2 · 🤖1
        示例: ████████████░░░░ 75% · 🔧2

        Args:
            state: 聚合状态

        Returns:
            详细信息行字符串
        """
        parts = []

        progress_part = self._render_progress_bar(state)
        if progress_part:
            parts.append(progress_part)

        activity_part = self._render_activity_compact(state)
        if activity_part:
            parts.append(activity_part)

        return join_parts(parts, sep=self._separator_primary) if parts else ""

    def _render_model(self, state: AggregatedState) -> Optional[str]:
        """
        渲染模型名称（短格式）

        示例: "GLM-4.7" from "glm-4.7-turbo"

        Args:
            state: 聚合状态

        Returns:
            模型名称字符串
        """
        if not isinstance(state.value, dict):
            return None

        model_name = state.value.get("model_name", "")
        if not model_name:
            return None

        return self._shorten_model_name(model_name)

    def _render_tokens_cost(self, state: AggregatedState) -> Optional[str]:
        """
        渲染 Token 和成本

        示例: "204K（$26.97）" 或 "87015 tokens（$11.94）"

        Args:
            state: 聚合状态

        Returns:
            Token 和成本字符串
        """
        if not isinstance(state.value, dict):
            return None

        tokens = state.value.get("tokens", 0)
        cost = state.value.get("cost_usd", 0.0)

        # 如果没有 tokens，不显示
        if tokens == 0:
            return None

        # 根据大小决定显示格式
        if tokens >= 100000:
            token_str = format_token_count(tokens)
        elif tokens >= 1000:
            token_str = f"{tokens // 1000}.{(tokens % 1000) // 100}K"
        else:
            token_str = f"{tokens}"

        if cost > 0 and self._show_cost:
            cost_str = f"${cost:.2f}"
            return f"{token_str}（{cost_str}）"

        return token_str

    def _render_duration(self, state: AggregatedState) -> Optional[str]:
        """
        渲染时长（紧凑格式）

        示例: "42m53s" or "1h23m"

        Args:
            state: 聚合状态

        Returns:
            时长字符串
        """
        if not isinstance(state.value, dict):
            return None

        duration_ms = state.value.get("duration_ms", 0)
        if duration_ms == 0:
            return None

        return format_duration_ms(duration_ms)

    def _render_git_compact(self, state: AggregatedState) -> Optional[str]:
        """
        渲染 Git 信息（紧凑格式）

        示例: "⎇ master · +9.5K/-758" 或 "⎇ cdp 19 · +6653 -409"

        Args:
            state: 聚合状态

        Returns:
            Git 信息字符串
        """
        if not isinstance(state.value, dict):
            return None

        git_info = state.value.get("git", {})
        if not git_info:
            return None

        parts = []

        branch = git_info.get("branch", "")
        if branch:
            parts.append(f"⎇ {branch}")

        insertions = git_info.get("insertions", 0)
        deletions = git_info.get("deletions", 0)

        if insertions > 0 or deletions > 0:
            # 格式化数字（大数字用 K）
            ins_str = f"+{insertions}" if insertions < 1000 else f"+{insertions / 1000:.1f}K"
            del_str = f"-{deletions}" if deletions < 1000 else f"-{deletions / 1000:.1f}K"
            changes = f"{ins_str} {del_str}"
            parts.append(changes)

        return join_parts(parts, sep=" ") if parts else None

    def _render_progress_bar(self, state: AggregatedState) -> Optional[str]:
        """
        渲染进度条

        示例: "████████████░░░░ 75%"

        Args:
            state: 聚合状态

        Returns:
            进度条字符串
        """
        if not isinstance(state.value, dict):
            return None

        percentage = state.value.get("percentage", 0)
        if percentage == 0:
            return None

        bar = progress_bar(percentage, width=self._progress_bar_width)
        pct_str = format_percentage(percentage, decimals=0)

        return f"{bar} {pct_str}"

    def _render_activity_compact(self, state: AggregatedState) -> str:
        """
        渲染活动信息（超紧凑格式）

        示例: "🔧2 · 🤖1 · ✓3/5"

        Args:
            state: 聚合状态

        Returns:
            活动信息字符串
        """
        parts = []

        if self._components.get("tools"):
            tools_part = self._render_tools(state)
            if tools_part:
                parts.append(tools_part)

        if self._components.get("agents"):
            agents_part = self._render_agents(state)
            if agents_part:
                parts.append(agents_part)

        if self._components.get("todos"):
            todos_part = self._render_todos(state)
            if todos_part:
                parts.append(todos_part)

        return join_parts(parts, sep=self._separator_primary) if parts else ""

    def _render_path_compact(self, state: AggregatedState) -> Optional[str]:
        """
        渲染路径（紧凑格式）

        Args:
            state: 聚合状态

        Returns:
            路径字符串
        """
        if not isinstance(state.value, dict):
            return None

        path = state.value.get("current_dir", "")
        if not path:
            return None

        return shorten_path(path, max_len=30)

    def _shorten_model_name(self, model_name: str) -> str:
        """
        提取短模型名

        示例: "glm-4.7-turbo" -> "GLM-4.7"

        Args:
            model_name: 完整模型名

        Returns:
            短模型名
        """
        parts = model_name.split("-")
        if len(parts) >= 2:
            short = "-".join(parts[:2]).upper()
            return short
        return model_name.upper()
