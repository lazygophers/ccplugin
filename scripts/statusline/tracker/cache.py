"""
缓存策略

提供多级缓存和失效策略，提高状态查询性能。
"""

import time
import hashlib
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import OrderedDict
from enum import Enum

from .aggregator import AggregatedState, StateDimension


class CacheLevel(Enum):
    """缓存级别"""
    L1_MEMORY = "l1_memory"
    L2_DISK = "l2_disk"
    L3_COMPUTE = "l3_compute"


@dataclass
class CacheKey:
    """
    缓存键

    用于标识和索引缓存项。
    """
    dimension: StateDimension
    time_window: Tuple[float, float]
    filters: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        """生成哈希值"""
        key_str = f"{self.dimension.value}:{self.time_window}:{sorted(self.filters.items())}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def __eq__(self, other) -> bool:
        """比较相等"""
        if not isinstance(other, CacheKey):
            return False
        return (
            self.dimension == other.dimension
            and self.time_window == other.time_window
            and self.filters == other.filters
        )


@dataclass
class CacheEntry:
    """
    缓存条目

    包含缓存值和元数据。
    """
    key: CacheKey
    value: AggregatedState
    created_at: float
    ttl: Optional[float] = None
    access_count: int = 0

    @property
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl


@dataclass
class CacheStats:
    """缓存统计"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0

    @property
    def hit_rate(self) -> float:
        """计算命中率"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class LRUCache:
    """
    LRU 缓存实现

    基于 OrderedDict 的最近最少使用缓存。
    """

    def __init__(self, max_size: int = 1000):
        """
        初始化 LRU 缓存

        Args:
            max_size: 最大缓存大小
        """
        self._cache: OrderedDict[int, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._stats = CacheStats()

    def get(self, key: CacheKey) -> Optional[AggregatedState]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值或 None
        """
        key_hash = hash(key)

        if key_hash not in self._cache:
            self._stats.misses += 1
            return None

        entry = self._cache[key_hash]

        # 检查过期
        if entry.is_expired:
            del self._cache[key_hash]
            self._stats.misses += 1
            self._stats.evictions += 1
            self._stats.size = len(self._cache)
            return None

        # 更新访问顺序和计数
        self._cache.move_to_end(key_hash)
        entry.access_count += 1
        self._stats.hits += 1

        return entry.value

    def set(self, key: CacheKey, value: AggregatedState, ttl: Optional[float] = None) -> None:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒）
        """
        key_hash = hash(key)
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            ttl=ttl,
        )

        # 如果缓存已满，删除最旧的项
        if len(self._cache) >= self._max_size and key_hash not in self._cache:
            self._cache.popitem(last=False)
            self._stats.evictions += 1

        self._cache[key_hash] = entry
        self._cache.move_to_end(key_hash)
        self._stats.size = len(self._cache)

    def invalidate(self, pattern: Optional[str] = None) -> None:
        """
        失效缓存

        Args:
            pattern: 过滤模式，None 表示清空所有
        """
        if pattern is None:
            self._cache.clear()
        else:
            keys_to_delete = [
                key_hash for key_hash, entry in self._cache.items()
                if pattern in str(entry.key.dimension.value)
            ]
            for key_hash in keys_to_delete:
                del self._cache[key_hash]

        self._stats.size = len(self._cache)

    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._stats.size = 0

    def get_stats(self) -> CacheStats:
        """
        获取缓存统计

        Returns:
            缓存统计对象
        """
        return self._stats


class StateCache:
    """
    状态缓存

    提供多级缓存和统一的缓存接口。
    """

    def __init__(self, l1_size: int = 1000, default_ttl: int = 60):
        """
        初始化状态缓存

        Args:
            l1_size: L1 缓存大小
            default_ttl: 默认 TTL（秒）
        """
        self._l1_cache = LRUCache(max_size=l1_size)
        self._default_ttl = default_ttl

    def get(self, key: CacheKey) -> Optional[AggregatedState]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值或 None
        """
        # 先查 L1
        value = self._l1_cache.get(key)
        if value is not None:
            return value

        return None

    def set(self, key: CacheKey, value: AggregatedState, ttl: Optional[int] = None) -> None:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None 使用默认值
        """
        if ttl is None:
            ttl = self._default_ttl

        # 存入 L1
        self._l1_cache.set(key, value, ttl=ttl)

    def invalidate(self, pattern: Optional[str] = None) -> None:
        """
        失效缓存

        Args:
            pattern: 过滤模式，None 表示清空所有
        """
        self._l1_cache.invalidate(pattern)

    def clear(self) -> None:
        """清空所有缓存"""
        self._l1_cache.clear()

    def get_stats(self) -> Dict[str, CacheStats]:
        """
        获取缓存统计

        Returns:
            各级缓存的统计信息
        """
        return {
            "l1": self._l1_cache.get_stats(),
        }
