"""
Config Module Unit Tests

测试配置管理模块的功能
"""

import unittest
from pathlib import Path
import tempfile
import sys
import os

# 添加项目根目录到sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.config import get_data_path, get_config_path, load_config, DEFAULT_CONFIG


class TestConfigModule(unittest.TestCase):
    """配置模块测试类"""

    def test_get_data_path_default(self):
        """测试获取默认数据路径"""
        data_path = get_data_path()
        self.assertIsInstance(data_path, Path)
        self.assertTrue(data_path.is_absolute())

    def test_get_data_path_custom(self):
        """测试获取自定义项目根目录的数据路径"""
        custom_root = "/tmp/test_project"
        data_path = get_data_path(custom_root)
        self.assertEqual(
            data_path,
            Path(custom_root) / ".lazygophers/ccplugin/semantic"
        )

    def test_get_config_path(self):
        """测试获取配置文件路径"""
        config_path = get_config_path()
        self.assertIsInstance(config_path, Path)
        self.assertTrue(config_path.name.endswith('.yaml'))

    def test_load_config_default(self):
        """测试加载默认配置"""
        config = load_config()
        self.assertIsInstance(config, dict)
        # 检查必要的配置字段
        self.assertIn('backend', config)
        self.assertIn('embedding_model', config)
        self.assertIn('similarity_threshold', config)
        self.assertEqual(config['backend'], 'lancedb')

    def test_load_config_fallback_to_default(self):
        """测试配置文件不存在时使用默认值"""
        # 使用不存在的项目根目录
        config = load_config("/nonexistent/path")
        self.assertEqual(config, DEFAULT_CONFIG)

    def test_default_config_structure(self):
        """测试默认配置的结构"""
        self.assertIsInstance(DEFAULT_CONFIG, dict)
        self.assertIn('supported_languages', DEFAULT_CONFIG)
        self.assertIsInstance(DEFAULT_CONFIG['supported_languages'], list)
        self.assertGreater(len(DEFAULT_CONFIG['supported_languages']), 0)


class TestConfigIntegration(unittest.TestCase):
    """配置模块集成测试"""

    def test_config_consistency(self):
        """测试配置的一致性"""
        config1 = load_config()
        config2 = load_config()
        self.assertEqual(config1, config2)

    def test_data_path_consistency(self):
        """测试数据路径的一致性"""
        path1 = get_data_path()
        path2 = get_data_path()
        self.assertEqual(path1, path2)


if __name__ == '__main__':
    unittest.main()
