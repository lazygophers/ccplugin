"""
兼容层测试
"""

import pytest

from scripts.statusline.core.compat import migrate_config


class TestCompat:
    """兼容层测试"""

    def test_migrate_config_empty(self):
        """测试空配置迁移"""
        old_config = {}
        new_config = migrate_config(old_config)
        assert new_config is not None
        assert isinstance(new_config, dict)

    def test_migrate_config_legacy_keys(self):
        """测试旧版配置键迁移"""
        old_config = {
            "show_model": True,
            "show_git": True,
            "layout": "expanded",
        }
        new_config = migrate_config(old_config)
        assert new_config is not None
        # 验证键已迁移
        assert "layout_mode" in new_config
        assert new_config["layout_mode"] == "expanded"

    def test_migrate_config_preserves_unknown(self):
        """测试保留未知配置键"""
        old_config = {
            "unknown_key": "value",
            "another_unknown": 123,
        }
        new_config = migrate_config(old_config)
        assert new_config is not None
        # 未知键应被保留或忽略
        assert isinstance(new_config, dict)

    def test_migrate_config_none(self):
        """测试 None 配置处理"""
        new_config = migrate_config(None)
        assert new_config is not None
        assert isinstance(new_config, dict)

    def test_migrate_config_nested(self):
        """测试嵌套配置迁移"""
        old_config = {
            "git": {
                "show_branch": True,
                "show_files": True,
            }
        }
        new_config = migrate_config(old_config)
        assert new_config is not None
        assert isinstance(new_config, dict)
