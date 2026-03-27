"""
验证工具测试
"""

import pytest

from scripts.statusline.utils.validation import (
    validate_config_dict,
    validate_layout,
    validate_theme,
    validate_path,
)


class TestValidation:
    """验证工具测试"""

    def test_validate_config_dict_valid(self):
        """测试有效配置验证"""
        config = {
            "layout_mode": "expanded",
        }
        errors = validate_config_dict(config)
        assert errors == []

    def test_validate_config_dict_invalid_layout(self):
        """测试无效布局模式验证"""
        config = {
            "layout_mode": "invalid_mode",
        }
        errors = validate_config_dict(config)
        assert len(errors) > 0
        assert "Invalid layout_mode" in errors[0]

    def test_validate_config_dict_empty(self):
        """测试空配置验证"""
        config = {}
        errors = validate_config_dict(config)
        # 空配置应该是有效的（使用默认值）
        assert errors == []

    def test_validate_layout_valid(self):
        """测试有效布局验证"""
        assert validate_layout("expanded") is True
        assert validate_layout("compact") is True

    def test_validate_layout_invalid(self):
        """测试无效布局验证"""
        assert validate_layout("invalid_mode") is False

    def test_validate_theme_valid(self):
        """测试有效主题验证"""
        assert validate_theme("default") is True
        assert validate_theme("minimal") is True

    def test_validate_theme_invalid(self):
        """测试无效主题验证"""
        assert validate_theme("nonexistent_theme") is False

    def test_validate_path_valid(self):
        """测试有效路径验证"""
        import tempfile
        import os

        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_path = f.name
            f.write(b"test")

        try:
            from pathlib import Path
            is_valid = validate_path(Path(temp_path))
            assert is_valid is True
        finally:
            os.unlink(temp_path)

    def test_validate_path_invalid(self):
        """测试无效路径验证"""
        from pathlib import Path
        is_valid = validate_path(Path("/nonexistent/path/that/does/not/exist"))
        assert is_valid is False

    def test_validate_path_none(self):
        """测试 None 路径验证"""
        is_valid = validate_path(None)
        assert is_valid is False

    def test_validate_path_empty(self):
        """测试空路径验证"""
        is_valid = validate_path("")
        assert is_valid is False
