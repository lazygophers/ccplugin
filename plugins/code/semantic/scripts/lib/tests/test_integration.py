"""
Integration Tests - 集成测试

验证所有插件能够正常导入和使用公共库
"""

import unittest
import sys
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))


class TestSemanticsIntegration(unittest.TestCase):
    """Semantic 插件集成测试"""

    def test_semantic_script_can_import_lib(self):
        """测试 semantic.py 能否导入 lib 模块"""
        # 添加semantic脚本目录
        semantic_scripts = project_root / 'plugins' / 'semantic' / 'scripts'
        sys.path.insert(0, str(semantic_scripts))

        try:
            # 尝试导入semantic.py中需要的模块
            from lib.constants import SUPPORTED_LANGUAGES
            from lib.config import get_data_path, load_config
            self.assertIsNotNone(SUPPORTED_LANGUAGES)
            self.assertIsNotNone(get_data_path)
            self.assertIsNotNone(load_config)
        finally:
            # 清理sys.path
            if str(semantic_scripts) in sys.path:
                sys.path.remove(str(semantic_scripts))

    def test_lib_modules_importable_from_script(self):
        """测试 lib 模块能否从脚本目录导入"""
        # 模拟从semantic脚本运行
        semantic_scripts = project_root / 'plugins' / 'semantic' / 'scripts'

        # 保存原始sys.path
        original_sys_path = sys.path.copy()

        try:
            # 设置路径如同从semantic脚本运行
            sys.path.insert(0, str(project_root))

            # 尝试导入
            from lib.config import get_data_path
            from lib.constants import SUPPORTED_LANGUAGES
            from lib.utils import check_and_auto_init

            # 验证导入成功
            self.assertTrue(callable(get_data_path))
            self.assertTrue(callable(check_and_auto_init))
            self.assertIsInstance(SUPPORTED_LANGUAGES, dict)

        finally:
            # 恢复原始sys.path
            sys.path = original_sys_path


class TestTaskIntegration(unittest.TestCase):
    """Task 插件集成测试"""

    def test_task_plugin_structure(self):
        """测试 task 插件结构"""
        task_scripts = project_root / 'plugins' / 'task' / 'scripts'
        self.assertTrue(task_scripts.exists(), "Task scripts directory should exist")

        # 检查必需的文件
        required_files = ['task.py', 'mcp_server.py']
        for file in required_files:
            file_path = task_scripts / file
            self.assertTrue(file_path.exists(), f"File {file} should exist in task plugin")

    def test_task_script_executable(self):
        """测试 task 脚本是否可读"""
        task_py = project_root / 'plugins' / 'task' / 'scripts' / 'task.py'
        self.assertTrue(task_py.exists())
        self.assertTrue(task_py.is_file())

        # 读取并验证文件内容
        with open(task_py, 'r') as f:
            content = f.read()
            self.assertIn('#!/usr/bin/env python3', content)


class TestLibStructure(unittest.TestCase):
    """Lib 目录结构测试"""

    def test_lib_directory_exists(self):
        """测试 lib 目录存在"""
        lib_dir = project_root / 'lib'
        self.assertTrue(lib_dir.exists(), "lib directory should exist")
        self.assertTrue(lib_dir.is_dir(), "lib should be a directory")

    def test_lib_core_modules_exist(self):
        """测试 lib 核心模块存在"""
        lib_dir = project_root / 'lib'
        required_modules = ['config', 'constants', 'utils', 'embedding', 'parsers', 'search']

        for module in required_modules:
            module_dir = lib_dir / module
            self.assertTrue(module_dir.exists(), f"Module {module} should exist")
            self.assertTrue(module_dir.is_dir(), f"{module} should be a directory")

            # 检查__init__.py
            init_file = module_dir / '__init__.py'
            self.assertTrue(init_file.exists(), f"__init__.py should exist in {module}")

    def test_lib_tests_exist(self):
        """测试 lib 测试目录存在"""
        tests_dir = project_root / 'lib' / 'tests'
        self.assertTrue(tests_dir.exists(), "tests directory should exist")

        # 检查测试文件
        test_files = ['test_config.py', 'test_constants.py', 'test_utils.py']
        for test_file in test_files:
            file_path = tests_dir / test_file
            self.assertTrue(file_path.exists(), f"Test file {test_file} should exist")

    def test_old_semantic_lib_removed(self):
        """测试旧的 semantic lib 目录已被删除"""
        old_semantic_lib = project_root / 'plugins' / 'semantic' / 'scripts' / 'lib'
        self.assertFalse(old_semantic_lib.exists(),
            "Old semantic lib directory should be removed")

    def test_python_files_count(self):
        """测试 lib 目录中有足够的 Python 文件"""
        lib_dir = project_root / 'lib'
        py_files = list(lib_dir.glob('**/*.py'))
        # 应该有至少30个Python文件
        self.assertGreater(len(py_files), 25, "lib should contain many Python files")


class TestDependencyImports(unittest.TestCase):
    """依赖导入测试"""

    def test_all_core_modules_import(self):
        """测试所有核心模块可以导入"""
        try:
            from lib.config import get_data_path, get_config_path, load_config
            from lib.constants import SUPPORTED_LANGUAGES
            from lib.utils import check_and_auto_init

            # 验证导入的对象
            self.assertTrue(callable(get_data_path))
            self.assertTrue(callable(get_config_path))
            self.assertTrue(callable(load_config))
            self.assertIsInstance(SUPPORTED_LANGUAGES, dict)
            self.assertTrue(callable(check_and_auto_init))

        except ImportError as e:
            self.fail(f"Failed to import core modules: {e}")

    def test_lib_main_init_file(self):
        """测试 lib/__init__.py 存在"""
        main_init = project_root / 'lib' / '__init__.py'
        self.assertTrue(main_init.exists(), "lib/__init__.py should exist")

        # 验证文件可读
        with open(main_init, 'r') as f:
            content = f.read()
            self.assertIn('CCPlugin Common Library', content)


if __name__ == '__main__':
    unittest.main()
