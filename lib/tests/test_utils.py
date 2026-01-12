"""
Utils Module Unit Tests

测试通用工具函数模块
"""

import unittest
import sys
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.utils import check_and_auto_init


class TestCheckAndAutoInit(unittest.TestCase):
    """check_and_auto_init 函数测试类"""

    def test_check_and_auto_init_default(self):
        """测试默认参数"""
        result = check_and_auto_init()
        self.assertTrue(result)
        self.assertIsInstance(result, bool)

    def test_check_and_auto_init_silent_true(self):
        """测试silent=True模式"""
        result = check_and_auto_init(silent=True)
        self.assertTrue(result)

    def test_check_and_auto_init_silent_false(self):
        """测试silent=False模式"""
        result = check_and_auto_init(silent=False)
        self.assertTrue(result)

    def test_check_and_auto_init_always_returns_true(self):
        """测试函数始终返回True"""
        for _ in range(5):
            result = check_and_auto_init()
            self.assertTrue(result)


class TestUtilsIntegration(unittest.TestCase):
    """工具函数集成测试"""

    def test_utils_import(self):
        """测试utils模块可以正常导入"""
        from lib import utils
        self.assertTrue(hasattr(utils, 'check_and_auto_init'))

    def test_utils_export_in_module(self):
        """测试__all__导出"""
        from lib.utils import __all__
        self.assertIn('check_and_auto_init', __all__)


if __name__ == '__main__':
    unittest.main()
