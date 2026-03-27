"""
主循环

协调各模块工作，实现状态栏的核心逻辑。
"""

import sys
import time
from typing import Optional, Dict, Any

from ..config.manager import Config
from ..parser.incremental import IncrementalParser
from ..tracker.aggregator import StateAggregator
from ..tracker.cache import StateCache, CacheKey
from ..layout.factory import LayoutFactory
from ..layout.base import Layout
from ..renderer.theme import ThemeManager
from ..renderer.incremental import IncrementalRenderer


class StatuslineLoop:
    """
    状态栏主循环

    协调解析、聚合、缓存、布局和渲染等模块。
    """

    def __init__(self, config: Config):
        """
        初始化主循环

        Args:
            config: 配置对象
        """
        self._config = config

        # 初始化各模块
        self._parser = IncrementalParser()
        self._aggregator = StateAggregator()
        self._cache = StateCache(
            l1_size=config.cache.max_size,
            default_ttl=config.cache.ttl,
        )
        self._theme_manager = ThemeManager()
        self._layout: Optional[Layout] = None
        self._renderer: Optional[IncrementalRenderer] = None

        # 运行状态
        self._running = False
        self._last_update = 0.0

        # 性能统计
        self._frame_count = 0
        self._start_time = 0.0

        # 初始化布局和渲染器
        self._init_layout_and_renderer()

    def _init_layout_and_renderer(self) -> None:
        """初始化布局和渲染器"""
        # 注册布局（仅当未注册时）
        from ..layout.expanded import ExpandedLayout
        from ..layout.compact import CompactLayout

        if not LayoutFactory.is_registered("expanded"):
            LayoutFactory.register("expanded", ExpandedLayout)
        if not LayoutFactory.is_registered("compact"):
            LayoutFactory.register("compact", CompactLayout)

        # 创建布局
        self._layout = LayoutFactory.create_from_config(self._config)

        # 加载主题
        theme = self._theme_manager.load_theme(self._config.theme)

        # 创建渲染器
        self._renderer = IncrementalRenderer(self._layout, theme)

    def start(self) -> None:
        """启动主循环"""
        self._running = True
        self._start_time = time.time()

        try:
            self._loop()
        except KeyboardInterrupt:
            self._stop()
        except Exception as e:
            self._handle_error(e)
        finally:
            self._cleanup()

    def _loop(self) -> None:
        """主循环逻辑"""
        while self._running:
            # 1. 读取输入
            chunk = self._read_input()
            if not chunk:
                time.sleep(self._config.refresh.interval)
                continue

            # 2. 解析事件
            events = self._parser.parse(chunk)
            if not events:
                time.sleep(self._config.refresh.interval)
                continue

            # 3. 更新状态
            for event in events:
                self._aggregator.update(event)

            # 4. 检查是否需要更新
            current_time = time.time()
            if self._should_update(current_time):
                # 5. 渲染输出
                self._render_and_output()
                self._last_update = current_time

            # 6. 控制刷新频率
            time.sleep(self._config.refresh.interval)

    def _read_input(self) -> str:
        """
        读取输入

        Returns:
            输入字符串
        """
        if sys.stdin is None or sys.stdin.isatty():
            return ""

        try:
            # 尝试读取可用数据
            import select
            if select.select([sys.stdin], [], [], 0)[0]:
                return sys.stdin.read()
        except Exception:
            pass

        return ""

    def _should_update(self, current_time: float) -> bool:
        """
        检查是否需要更新

        Args:
            current_time: 当前时间

        Returns:
            是否需要更新
        """
        if not self._config.refresh.incremental:
            return True

        time_since_last = current_time - self._last_update
        return time_since_last >= self._config.refresh.interval

    def _render_and_output(self) -> None:
        """渲染并输出结果"""
        # 获取所有状态
        states = self._aggregator.get_all_states()

        # 选择主要状态（用户状态）
        from ..tracker.aggregator import StateDimension
        main_state = states.get(StateDimension.USER_STATUS)

        if main_state is None:
            return

        # 检查缓存
        cache_key = CacheKey(
            dimension=main_state.dimension,
            time_window=(self._last_update, time.time()),
        )

        if self._config.cache.enabled:
            cached = self._cache.get(cache_key)
            if cached is not None:
                self._write_output(str(cached.value))
                return

        # 渲染状态
        output = self._renderer.render(main_state)

        # 输出
        self._write_output(output)

        # 更新缓存
        if self._config.cache.enabled:
            from ..tracker.aggregator import AggregatedState
            cache_state = AggregatedState(
                dimension=main_state.dimension,
                value=output,
                timestamp=time.time(),
            )
            self._cache.set(cache_key, cache_state)

    def _write_output(self, output: str) -> None:
        """
        写入输出

        Args:
            output: 输出字符串
        """
        if output:
            print(output, flush=True)

    def _handle_error(self, error: Exception) -> None:
        """
        处理错误

        Args:
            error: 异常对象
        """
        if self._config.debug:
            import traceback
            traceback.print_exc()
        else:
            print(f"Error: {error}", file=sys.stderr)

    def _stop(self) -> None:
        """停止主循环"""
        self._running = False

    def _cleanup(self) -> None:
        """清理资源"""
        self._cache.clear()
        self._parser.reset()
        self._aggregator.clear()
        if self._renderer:
            self._renderer.reset()

    def pause(self) -> None:
        """暂停主循环"""
        self._running = False

    def resume(self) -> None:
        """恢复主循环"""
        if not self._running:
            self._running = True
            self._loop()

    def get_stats(self) -> Dict[str, Any]:
        """
        获取性能统计

        Returns:
            统计信息字典
        """
        elapsed_time = time.time() - self._start_time if self._start_time > 0 else 0
        fps = self._frame_count / elapsed_time if elapsed_time > 0 else 0

        cache_stats = self._cache.get_stats()

        return {
            "frame_count": self._frame_count,
            "elapsed_time": elapsed_time,
            "fps": fps,
            "cache_stats": cache_stats,
        }

    def process(self, transcript: str) -> str:
        """
        处理单个 transcript 并返回结果

        Args:
            transcript: transcript 字符串

        Returns:
            渲染结果
        """
        # 解析
        events = self._parser.parse(transcript)

        # 更新状态
        for event in events:
            self._aggregator.update(event)

        # 渲染
        from ..tracker.aggregator import StateDimension
        states = self._aggregator.get_all_states()
        main_state = states.get(StateDimension.USER_STATUS)

        if main_state is None:
            return ""

        return self._renderer.render(main_state)
