"""
Constants Module Unit Tests

测试常量定义模块
"""

import unittest
import sys
from pathlib import Path

# 添加项目根目录到sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from lib.constants import SUPPORTED_LANGUAGES


class TestLanguageConstants(unittest.TestCase):
    """语言常量测试类"""

    def test_supported_languages_exists(self):
        """测试支持的语言字典存在"""
        self.assertIsNotNone(SUPPORTED_LANGUAGES)
        self.assertIsInstance(SUPPORTED_LANGUAGES, dict)

    def test_supported_languages_not_empty(self):
        """测试支持的语言字典非空"""
        self.assertGreater(len(SUPPORTED_LANGUAGES), 0)

    def test_all_extensions_are_lists(self):
        """测试所有扩展名都是列表"""
        for language, extensions in SUPPORTED_LANGUAGES.items():
            self.assertIsInstance(extensions, list,
                f"Language {language} extensions should be a list")
            self.assertGreater(len(extensions), 0,
                f"Language {language} should have at least one extension")

    def test_all_extensions_start_with_dot(self):
        """测试所有扩展名都以点开头（或特殊文件名）"""
        for language, extensions in SUPPORTED_LANGUAGES.items():
            for ext in extensions:
                if ext not in ['Dockerfile', 'dockerfile']:  # 特殊情况
                    self.assertTrue(ext.startswith('.'),
                        f"Extension {ext} for language {language} should start with '.'")

    def test_key_languages_exist(self):
        """测试关键编程语言存在"""
        key_languages = ['python', 'javascript', 'java', 'golang', 'rust']
        for lang in key_languages:
            self.assertIn(lang, SUPPORTED_LANGUAGES,
                f"Language {lang} should be supported")

    def test_python_extensions(self):
        """测试Python文件扩展名"""
        self.assertIn('.py', SUPPORTED_LANGUAGES['python'])
        self.assertEqual(len(SUPPORTED_LANGUAGES['python']), 1)

    def test_javascript_extensions(self):
        """测试JavaScript文件扩展名"""
        js_exts = SUPPORTED_LANGUAGES['javascript']
        self.assertIn('.js', js_exts)
        self.assertIn('.jsx', js_exts)

    def test_no_duplicate_extensions_across_languages(self):
        """测试不同语言间没有重复的扩展名（除了Android）"""
        ext_to_langs = {}
        for language, extensions in SUPPORTED_LANGUAGES.items():
            for ext in extensions:
                if ext not in ext_to_langs:
                    ext_to_langs[ext] = []
                ext_to_langs[ext].append(language)

        # 检查重复（除了特殊情况）
        for ext, langs in ext_to_langs.items():
            if ext not in ['.java', '.kt', '.h']:  # 这些可能有重复
                if len(langs) > 1:
                    # 只允许特定的重复组合
                    allowed_combinations = [
                        {'java', 'android'},
                        {'kotlin', 'android'},
                        {'c', 'cpp'}  # C头文件可能在C和C++中
                    ]
                    self.assertIn(set(langs), allowed_combinations,
                        f"Extension {ext} found in unexpected languages: {langs}")


class TestLanguageOrdering(unittest.TestCase):
    """语言排序测试（重要！）"""

    def test_specific_languages_before_generic(self):
        """测试更具体的语言在更通用的语言之前"""
        languages = list(SUPPORTED_LANGUAGES.keys())

        # Java 应该在 Android 之前
        java_idx = languages.index('java')
        android_idx = languages.index('android')
        self.assertLess(java_idx, android_idx,
            "Java should come before Android")

        # Kotlin 应该在 Android 之前
        kotlin_idx = languages.index('kotlin')
        self.assertLess(kotlin_idx, android_idx,
            "Kotlin should come before Android")


if __name__ == '__main__':
    unittest.main()
