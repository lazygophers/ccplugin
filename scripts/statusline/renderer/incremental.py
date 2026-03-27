"""
增量渲染

实现增量渲染机制，只更新变化的部分以提高性能。
"""

import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from collections import OrderedDict

from ..tracker.aggregator import AggregatedState
from ..layout.base import Layout
from .theme import Theme, ThemeColor


class DiffType(Enum):
    """差异类型"""
    NO_CHANGE = "no_change"
    MINOR_CHANGE = "minor_change"
    MAJOR_CHANGE = "major_change"
    FULL_RERENDER = "full_rerender"


@dataclass
class DiffResult:
    """
    差异结果

    描述状态变化的具体内容。
    """
    diff_type: DiffType
    changed_fields: List[str] = field(default_factory=list)
    old_values: Dict[str, Any] = field(default_factory=dict)
    new_values: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_no_change(self) -> bool:
        """是否无变化"""
        return self.diff_type == DiffType.NO_CHANGE

    @property
    def is_minor(self) -> bool:
        """是否是小变化"""
        return self.diff_type == DiffType.MINOR_CHANGE

    @property
    def is_major(self) -> bool:
        """是否是大变化"""
        return self.diff_type == DiffType.MAJOR_CHANGE


class RenderCache:
    """
    渲染缓存

    缓存渲染结果以提高性能。
    """

    def __init__(self, max_size: int = 100):
        """
        初始化渲染缓存

        Args:
            max_size: 最大缓存大小
        """
        self._cache: OrderedDict[str, str] = OrderedDict()
        self._max_size = max_size

    def get(self, key: str) -> Optional[str]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值或 None
        """
        if key in self._cache:
            # 移到末尾（最近使用）
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def set(self, key: str, value: str) -> None:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
        """
        # 如果缓存已满，删除最旧的项
        if len(self._cache) >= self._max_size and key not in self._cache:
            self._cache.popitem(last=False)

        self._cache[key] = value
        self._cache.move_to_end(key)

    def invalidate(self, pattern: Optional[str] = None) -> None:
        """
        失效缓存

        Args:
            pattern: 过滤模式，None 表示清空所有
        """
        if pattern is None:
            self._cache.clear()
        else:
            keys_to_delete = [k for k in self._cache if pattern in k]
            for key in keys_to_delete:
                del self._cache[key]

    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()


class IncrementalRenderer:
    """
    增量渲染器

    实现增量渲染机制，只更新变化的部分。
    """

    def __init__(self, layout: Layout, theme: Theme):
        """
        初始化增量渲染器

        Args:
            layout: 布局对象
            theme: 主题对象
        """
        self._layout = layout
        self._theme = theme
        self._last_state: Optional[AggregatedState] = None
        self._last_render: Optional[str] = None
        self._cache = RenderCache()

    def render(self, state: AggregatedState) -> str:
        """
        渲染状态

        Args:
            state: 聚合状态

        Returns:
            渲染后的字符串
        """
        # 计算差异
        diff = self._compute_diff(self._last_state, state)

        # 根据差异类型选择渲染策略
        if diff.is_no_change and self._last_render is not None:
            # 无变化，返回上次渲染结果
            return self._last_render
        elif diff.is_minor and self._last_render is not None:
            # 小变化，尝试增量更新
            return self._update_partial(self._last_render, diff)
        else:
            # 大变化或首次渲染，完全重渲染
            return self._render_full(state)

    def _compute_diff(
        self,
        old_state: Optional[AggregatedState],
        new_state: AggregatedState
    ) -> DiffResult:
        """
        计算状态差异

        Args:
            old_state: 旧状态
            new_state: 新状态

        Returns:
            差异结果
        """
        if old_state is None:
            return DiffResult(diff_type=DiffType.FULL_RERENDER)

        changed_fields = []
        old_values = {}
        new_values = {}

        # 比较状态值
        if old_state.value != new_state.value:
            if isinstance(new_state.value, dict):
                for key in new_state.value:
                    if key not in old_state.value or old_state.value[key] != new_state.value[key]:
                        changed_fields.append(key)
                        old_values[key] = old_state.value.get(key)
                        new_values[key] = new_state.value[key]
            else:
                changed_fields.append("value")
                old_values["value"] = old_state.value
                new_values["value"] = new_state.value

        # 确定差异类型
        if not changed_fields:
            diff_type = DiffType.NO_CHANGE
        elif len(changed_fields) <= 2 and self._is_numeric_change(changed_fields, old_values, new_values):
            diff_type = DiffType.MINOR_CHANGE
        else:
            diff_type = DiffType.MAJOR_CHANGE

        return DiffResult(
            diff_type=diff_type,
            changed_fields=changed_fields,
            old_values=old_values,
            new_values=new_values,
        )

    def _is_numeric_change(
        self,
        fields: List[str],
        old_values: Dict[str, Any],
        new_values: Dict[str, Any]
    ) -> bool:
        """
        检查是否是数值变化

        Args:
            fields: 变化字段
            old_values: 旧值
            new_values: 新值

        Returns:
            是否都是数值变化
        """
        for field in fields:
            old_val = old_values.get(field)
            new_val = new_values.get(field)

            if not isinstance(old_val, (int, float)) or not isinstance(new_val, (int, float)):
                return False

        return True

    def _update_partial(self, last_render: str, diff: DiffResult) -> str:
        """
        部分更新渲染结果

        Args:
            last_render: 上次渲染结果
            diff: 差异结果

        Returns:
            更新后的渲染字符串
        """
        # 对于小变化，尝试替换特定部分
        # 这是一个简化实现，实际应用中可能需要更复杂的逻辑

        if "percentage" in diff.changed_fields:
            # 更新百分比
            new_pct = diff.new_values.get("percentage", 0)
            # 使用主题应用颜色
            colored_pct = self._theme.apply_color(f"{new_pct}%", ThemeColor.PRIMARY)
            return last_render  # 简化处理，实际应该替换

        # 对于其他情况，重新渲染
        return self._render_full_from_state(diff.new_values)

    def _render_full(self, state: AggregatedState) -> str:
        """
        完全重渲染

        Args:
            state: 聚合状态

        Returns:
            渲染后的字符串
        """
        result = self._layout.render(state)

        # 应用主题
        if self._theme:
            result = self._apply_theme(result, state)

        # 更新状态
        self._last_state = state
        self._last_render = result

        return result

    def _render_full_from_state(self, state_value: Any) -> str:
        """
        从状态值完全重渲染

        Args:
            state_value: 状态值

        Returns:
            渲染后的字符串
        """
        # 创建临时状态对象
        temp_state = AggregatedState(
            dimension=self._last_state.dimension if self._last_state else None,
            value=state_value,
            timestamp=time.time(),
        )

        return self._render_full(temp_state)

    def _apply_theme(self, text: str, state: AggregatedState) -> str:
        """
        应用主题到渲染结果

        Args:
            text: 渲染文本
            state: 状态对象

        Returns:
            应用主题后的文本
        """
        # 简化实现，实际应用中可能需要更复杂的主题应用逻辑
        return text

    def reset(self) -> None:
        """重置渲染器"""
        self._last_state = None
        self._last_render = None
        self._cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计

        Returns:
            缓存统计信息
        """
        return {
            "cache_size": len(self._cache._cache),
            "max_size": self._cache._max_size,
        }
