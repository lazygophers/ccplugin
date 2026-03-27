"""
StatuslineLoop 测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time

from scripts.statusline.core.loop import StatuslineLoop
from scripts.statusline.config.manager import Config, get_default_config


class TestStatuslineLoop:
    """StatuslineLoop 测试"""

    def test_loop_initialization(self):
        """测试主循环初始化"""
        config = get_default_config()
        loop = StatuslineLoop(config)
        assert loop is not None
        assert not loop._running
        assert loop._last_update == 0.0

    def test_loop_pause_resume(self):
        """测试暂停和恢复"""
        config = get_default_config()
        loop = StatuslineLoop(config)

        # 初始状态
        assert not loop._running

        # 暂停
        loop.pause()
        assert not loop._running

        # 恢复
        with patch.object(loop, '_loop'):
            loop.resume()
            assert loop._running

    def test_get_stats(self):
        """测试获取性能统计"""
        config = get_default_config()
        loop = StatuslineLoop(config)

        stats = loop.get_stats()
        assert isinstance(stats, dict)
        assert "frame_count" in stats
        assert "elapsed_time" in stats
        assert "fps" in stats
        assert "cache_stats" in stats

    def test_cleanup(self):
        """测试清理资源"""
        config = get_default_config()
        loop = StatuslineLoop(config)

        # 模拟一些状态
        loop._frame_count = 10
        loop._start_time = time.time()

        # 清理
        loop._cleanup()
        assert loop._frame_count == 10  # frame_count 不被清理

    def test_process_transcript(self):
        """测试处理 transcript"""
        config = get_default_config()
        loop = StatuslineLoop(config)

        # 简单的 transcript
        transcript = '{"event_type": "user_message", "timestamp": 1.0, "data": {"content": "Hello"}}'

        result = loop.process(transcript)
        assert isinstance(result, str)

    def test_process_empty_transcript(self):
        """测试处理空 transcript"""
        config = get_default_config()
        loop = StatuslineLoop(config)

        result = loop.process("")
        assert isinstance(result, str)

    def test_should_update_always(self):
        """测试总是更新模式"""
        config = get_default_config()
        config.refresh.incremental = False
        loop = StatuslineLoop(config)

        # 应该总是返回 True
        assert loop._should_update(time.time())

    def test_should_update_incremental(self):
        """测试增量更新模式"""
        config = get_default_config()
        config.refresh.incremental = True
        config.refresh.interval = 0.1
        loop = StatuslineLoop(config)

        current_time = time.time()
        loop._last_update = current_time

        # 刚更新过，不应该更新
        assert not loop._should_update(current_time)

        # 过了足够时间，应该更新
        assert loop._should_update(current_time + 0.2)

    def test_handle_error_debug_mode(self):
        """测试调试模式错误处理"""
        config = get_default_config()
        config.debug = True
        loop = StatuslineLoop(config)

        # 测试错误处理（不应抛出异常）
        loop._handle_error(Exception("Test error"))

    def test_handle_error_normal_mode(self):
        """测试普通模式错误处理"""
        config = get_default_config()
        config.debug = False
        loop = StatuslineLoop(config)

        # 测试错误处理（不应抛出异常）
        loop._handle_error(Exception("Test error"))

    def test_read_input_no_stdin(self):
        """测试没有 stdin 的情况"""
        config = get_default_config()
        loop = StatuslineLoop(config)

        with patch('scripts.statusline.core.loop.sys.stdin', None):
            result = loop._read_input()
            assert result == ""

    def test_read_input_tty(self):
        """测试 TTY 模式"""
        config = get_default_config()
        loop = StatuslineLoop(config)

        mock_stdin = Mock()
        mock_stdin.isatty.return_value = True

        with patch('scripts.statusline.core.loop.sys.stdin', mock_stdin):
            result = loop._read_input()
            assert result == ""

    def test_read_input_empty(self):
        """测试空输入"""
        config = get_default_config()
        loop = StatuslineLoop(config)

        mock_stdin = Mock()
        mock_stdin.isatty.return_value = False
        mock_stdin.read.return_value = ""

        with patch('scripts.statusline.core.loop.sys.stdin', mock_stdin):
            result = loop._read_input()
            assert result == ""

    @patch('select.select')
    def test_read_input_no_data(self, mock_select):
        """测试没有可用数据"""
        config = get_default_config()
        loop = StatuslineLoop(config)

        mock_stdin = Mock()
        mock_stdin.isatty.return_value = False
        mock_select.return_value = ([], [], [])

        with patch('scripts.statusline.core.loop.sys.stdin', mock_stdin):
            result = loop._read_input()
            assert result == ""

    @patch('select.select')
    def test_read_input_with_data(self, mock_select):
        """测试有数据可读"""
        config = get_default_config()
        loop = StatuslineLoop(config)

        test_data = "test input data"
        mock_stdin = Mock()
        mock_stdin.isatty.return_value = False
        mock_select.return_value = ([mock_stdin], [], [])
        mock_stdin.read.return_value = test_data

        with patch('scripts.statusline.core.loop.sys.stdin', mock_stdin):
            result = loop._read_input()
            assert result == test_data

    @patch('select.select')
    def test_read_input_exception(self, mock_select):
        """测试读取异常"""
        config = get_default_config()
        loop = StatuslineLoop(config)

        mock_stdin = Mock()
        mock_stdin.isatty.return_value = False
        mock_select.side_effect = Exception("Select error")

        with patch('scripts.statusline.core.loop.sys.stdin', mock_stdin):
            result = loop._read_input()
            assert result == ""

    def test_write_output(self):
        """测试写入输出"""
        config = get_default_config()
        loop = StatuslineLoop(config)

        with patch('builtins.print') as mock_print:
            loop._write_output("test output")
            mock_print.assert_called_once_with("test output", flush=True)

    def test_write_output_empty(self):
        """测试写入空输出"""
        config = get_default_config()
        loop = StatuslineLoop(config)

        with patch('builtins.print') as mock_print:
            loop._write_output("")
            mock_print.assert_not_called()

    def test_process_invalid_json(self):
        """测试处理无效 JSON"""
        config = get_default_config()
        loop = StatuslineLoop(config)

        result = loop.process("invalid json")
        assert isinstance(result, str)

    def test_reset(self):
        """测试重置解析器"""
        config = get_default_config()
        loop = StatuslineLoop(config)

        # 处理一些数据
        loop.process('{"event_type": "user_message", "timestamp": 1.0, "data": {"content": "Hello"}}')

        # 重置
        loop._parser.reset()
        assert loop._parser.get_state().position == 0
