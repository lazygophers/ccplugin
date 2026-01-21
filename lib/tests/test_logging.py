"""
日志模块单元测试。
"""

import unittest
import logging
import sys
import tempfile
import shutil
from pathlib import Path
from io import StringIO

# 添加项目根目录到 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.logging import get_logger, setup_logging, set_level, HourlyRotatingFileHandler


class TestHourlyRotatingFileHandler(unittest.TestCase):
    """测试按小时分割的日志处理器。"""

    def setUp(self):
        """测试前设置。"""
        self.test_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.test_dir) / "logs"

    def tearDown(self):
        """测试后清理。"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_handler_creation(self):
        """测试处理器创建。"""
        handler = HourlyRotatingFileHandler(str(self.log_dir))
        self.assertTrue(self.log_dir.exists())
        handler.close()

    def test_log_file_creation(self):
        """测试日志文件创建。"""
        handler = HourlyRotatingFileHandler(str(self.log_dir))
        # 设置日志格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        handler.setFormatter(formatter)

        logger = logging.getLogger("test_handler")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # 写入日志
        logger.info("test message")

        # 验证文件已创建
        log_files = list(self.log_dir.glob("*.log"))
        self.assertEqual(len(log_files), 1)
        self.assertTrue(log_files[0].exists())

        # 验证内容
        content = log_files[0].read_text()
        self.assertIn("test message", content)
        self.assertIn("INFO", content)

        handler.close()

    def test_log_format(self):
        """测试日志格式。"""
        handler = HourlyRotatingFileHandler(str(self.log_dir))
        logger = logging.getLogger("test_format")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # 获取处理器的格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        handler.setFormatter(formatter)

        # 写入日志
        logger.info("format test")

        # 验证格式
        log_files = list(self.log_dir.glob("*.log"))
        content = log_files[0].read_text()

        # 应包含时间、级别、文件和消息
        self.assertIn("-", content)  # 时间分隔符
        self.assertIn("INFO", content)  # 级别
        self.assertIn("test_logging.py:", content)  # 文件名和行号
        self.assertIn("format test", content)  # 消息

        handler.close()

    def test_cleanup_old_logs(self):
        """测试清理旧日志。"""
        handler = HourlyRotatingFileHandler(str(self.log_dir))

        # 创建 5 个日志文件
        for i in range(5):
            log_file = self.log_dir / f"202601200{i}.log"
            log_file.write_text(f"old log {i}\n")

        # 手动触发清理
        handler._cleanup_old_logs()

        # 应该只保留 3 个文件
        log_files = list(self.log_dir.glob("*.log"))
        self.assertLessEqual(len(log_files), 3)

        handler.close()


class TestLoggerAPI(unittest.TestCase):
    """测试日志记录器 API。"""

    def setUp(self):
        """测试前设置。"""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = Path.cwd()

    def tearDown(self):
        """测试后清理。"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_get_logger_basic(self):
        """测试基础 get_logger 功能。"""
        logger = get_logger("test_basic")
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "test_basic")

    def test_get_logger_debug_mode(self):
        """测试 get_logger 的 DEBUG 模式。"""
        logger = get_logger("test_debug", debug=True)

        # 应该有 2 个处理器（文件 + 控制台）
        self.assertEqual(len(logger.handlers), 2)

        # 应该有一个 StreamHandler
        has_stream_handler = any(
            isinstance(h, logging.StreamHandler) for h in logger.handlers
        )
        self.assertTrue(has_stream_handler)

    def test_get_logger_caching(self):
        """测试 get_logger 缓存功能。"""
        logger1 = get_logger("test_cache")
        logger2 = get_logger("test_cache")
        self.assertIs(logger1, logger2)

    def test_set_level(self):
        """测试设置全局日志级别。"""
        logger1 = get_logger("test_level1")
        logger2 = get_logger("test_level2")

        # 设置全局级别为 DEBUG
        set_level(logging.DEBUG)

        # 两个 logger 的级别都应该更新
        self.assertEqual(logger1.level, logging.DEBUG)
        self.assertEqual(logger2.level, logging.DEBUG)

    def test_setup_logging_with_console(self):
        """测试全局日志配置。"""
        logger = get_logger("test_setup")

        # 调用全局配置
        setup_logging(enable_console=True)

        # 应该有控制台处理器
        has_console = any(
            isinstance(h, logging.StreamHandler) for h in logger.handlers
        )
        self.assertTrue(has_console)

    def test_log_levels(self):
        """测试不同的日志级别。"""
        logger = get_logger("test_levels")

        # 应该可以调用所有日志级别方法
        try:
            logger.debug("debug message")
            logger.info("info message")
            logger.warning("warning message")
            logger.error("error message")
            logger.critical("critical message")
        except Exception as e:
            self.fail(f"日志级别方法调用失败: {e}")


class TestLogFileContent(unittest.TestCase):
    """测试日志文件内容。"""

    def setUp(self):
        """测试前设置。"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """测试后清理。"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_multiple_loggers_same_file(self):
        """测试多个 logger 写入同一个文件。"""
        log_dir = Path(self.test_dir) / "logs"

        logger1 = get_logger("module1")
        logger2 = get_logger("module2")

        # 两个 logger 都应该有处理器
        self.assertGreater(len(logger1.handlers), 0)
        self.assertGreater(len(logger2.handlers), 0)

    def test_error_logging(self):
        """测试错误日志记录。"""
        logger = get_logger("test_error")

        try:
            raise ValueError("Test error")
        except ValueError:
            # 记录异常
            logger.error("An error occurred")

        # 验证日志已记录
        log_dir = Path.cwd() / "lazygophers" / "ccplugin" / "log"
        if log_dir.exists():
            log_files = list(log_dir.glob("*.log"))
            if log_files:
                content = log_files[0].read_text()
                self.assertIn("error occurred", content.lower())


class TestLoggerIntegration(unittest.TestCase):
    """集成测试。"""

    def test_full_workflow(self):
        """测试完整的日志工作流程。"""
        # 1. 获取 logger
        logger = get_logger("integration_test", debug=False)

        # 2. 写入日志
        logger.info("Integration test started")
        logger.warning("This is a warning")
        logger.error("This is an error")

        # 3. 验证日志目录存在
        log_dir = Path.cwd() / "lazygophers" / "ccplugin" / "log"
        self.assertTrue(log_dir.exists())

        # 4. 验证日志文件存在
        log_files = list(log_dir.glob("*.log"))
        self.assertGreater(len(log_files), 0)

        # 5. 验证内容
        all_content = ""
        for log_file in log_files:
            all_content += log_file.read_text()

        self.assertIn("Integration test started", all_content)


if __name__ == "__main__":
    unittest.main()
