"""
日志模块单元测试 - 基于 Rich 的日志系统。
"""

import unittest
import sys
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.logging import info, debug, error, warn, enable_debug
from lib.logging.manager import RichLoggerManager


class TestLoggerAPI(unittest.TestCase):
    """测试简洁日志 API。"""

    def setUp(self):
        """测试前设置。"""
        # 重置单实例
        RichLoggerManager._instance = None

    def tearDown(self):
        """测试后清理。"""
        # 重置单实例
        RichLoggerManager._instance = None

    def test_info_logging(self):
        """测试 info 日志记录。"""
        try:
            info("测试信息")
        except Exception as e:
            self.fail(f"info() 调用失败: {e}")

    def test_debug_logging(self):
        """测试 debug 日志记录。"""
        try:
            debug("测试调试")
        except Exception as e:
            self.fail(f"debug() 调用失败: {e}")

    def test_error_logging(self):
        """测试 error 日志记录。"""
        try:
            error("测试错误")
        except Exception as e:
            self.fail(f"error() 调用失败: {e}")

    def test_warn_logging(self):
        """测试 warn 日志记录。"""
        try:
            warn("测试警告")
        except Exception as e:
            self.fail(f"warn() 调用失败: {e}")

    def test_enable_debug(self):
        """测试启用 DEBUG 模式。"""
        logger = RichLoggerManager()
        logger.enable_debug()
        self.assertTrue(logger.debug_enabled)

    def test_log_file_creation(self):
        """测试日志文件创建。"""
        info("测试文件创建")

        log_dir = Path.cwd() / ".lazygophers" / "ccplugin" / "log"
        self.assertTrue(log_dir.exists())

        log_files = list(log_dir.glob("*.log"))
        self.assertGreater(len(log_files), 0)

    def test_log_file_format(self):
        """测试日志文件格式。"""
        info("格式测试")
        error("错误测试")

        log_dir = Path.cwd() / ".lazygophers" / "ccplugin" / "log"
        log_files = sorted(log_dir.glob("*.log"))

        if log_files:
            # 使用最新的日志文件
            content = log_files[-1].read_text()
            # 检查是否包含必要的格式标记
            self.assertIn("INFO", content)
            self.assertIn("ERROR", content)
            self.assertIn("[", content)  # 时间戳括号
            self.assertIn("]", content)

    def test_log_cleanup(self):
        """测试旧日志清理。"""
        logger = RichLoggerManager()

        # 创建一些旧的日志文件来测试清理
        log_dir = logger.log_dir
        for i in range(5):
            old_file = log_dir / f"202601200{i}.log"
            old_file.write_text(f"old log {i}\n")

        # 手动触发清理
        logger._cleanup_old_logs()

        # 应该保留最多 3 个文件
        log_files = list(log_dir.glob("*.log"))
        self.assertLessEqual(len(log_files), 3)

    def test_singleton_pattern(self):
        """测试单例模式。"""
        logger1 = RichLoggerManager()
        logger2 = RichLoggerManager()
        self.assertIs(logger1, logger2)

    def test_multiple_levels(self):
        """测试多个日志级别。"""
        try:
            info("info")
            debug("debug")
            warn("warn")
            error("error")
        except Exception as e:
            self.fail(f"日志级别测试失败: {e}")

    def test_debug_console_output(self):
        """测试 DEBUG 模式控制台输出。"""
        logger = RichLoggerManager()
        logger.enable_debug()

        # 应该有控制台输出器
        self.assertIsNotNone(logger.console_console)
        self.assertTrue(logger.debug_enabled)


class TestLogFileContent(unittest.TestCase):
    """测试日志文件内容。"""

    def setUp(self):
        """测试前设置。"""
        RichLoggerManager._instance = None

    def tearDown(self):
        """测试后清理。"""
        RichLoggerManager._instance = None

    def test_log_content_saved_to_file(self):
        """测试日志内容保存到文件。"""
        info("保存测试消息")

        log_dir = Path.cwd() / ".lazygophers" / "ccplugin" / "log"
        log_files = sorted(log_dir.glob("*.log"))

        self.assertGreater(len(log_files), 0)

        content = log_files[-1].read_text()
        self.assertIn("保存测试消息", content)

    def test_different_log_levels_in_file(self):
        """测试不同级别的日志都保存到文件。"""
        info("信息消息")
        error("错误消息")
        warn("警告消息")

        log_dir = Path.cwd() / ".lazygophers" / "ccplugin" / "log"
        log_files = sorted(log_dir.glob("*.log"))

        if log_files:
            content = log_files[-1].read_text()
            self.assertIn("信息消息", content)
            self.assertIn("错误消息", content)
            self.assertIn("警告消息", content)


class TestLoggerIntegration(unittest.TestCase):
    """集成测试。"""

    def setUp(self):
        """测试前设置。"""
        RichLoggerManager._instance = None

    def tearDown(self):
        """测试后清理。"""
        RichLoggerManager._instance = None

    def test_full_workflow(self):
        """测试完整的日志工作流程。"""
        # 1. 记录日志
        info("工作流启动")
        warn("检测到警告")
        error("处理错误")

        # 2. 启用 DEBUG 模式
        enable_debug()
        debug("调试信息")

        # 3. 检查日志文件
        log_dir = Path.cwd() / ".lazygophers" / "ccplugin" / "log"
        self.assertTrue(log_dir.exists())

        log_files = list(log_dir.glob("*.log"))
        self.assertGreater(len(log_files), 0)

        # 4. 验证内容
        content = log_files[-1].read_text()
        self.assertIn("工作流启动", content)

    def test_api_functions_accessible(self):
        """测试所有 API 函数都可访问。"""
        from lib.logging import info, debug, error, warn, enable_debug

        # 应该能访问所有函数
        self.assertTrue(callable(info))
        self.assertTrue(callable(debug))
        self.assertTrue(callable(error))
        self.assertTrue(callable(warn))
        self.assertTrue(callable(enable_debug))


if __name__ == "__main__":
    unittest.main()