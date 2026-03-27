"""
配置管理器测试
"""

import pytest
import json
from pathlib import Path

from scripts.statusline.config.manager import (
    Config,
    ConfigManager,
    get_default_config,
    LayoutMode,
    CacheConfig,
    RefreshConfig,
)


class TestConfig:
    """配置类测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = get_default_config()
        assert config.layout_mode == LayoutMode.EXPANDED
        assert config.theme == "default"
        assert config.show_user is True
        assert config.show_progress is True

    def test_config_to_dict(self):
        """测试配置转换为字典"""
        config = get_default_config()
        data = config.to_dict()
        assert "layout_mode" in data
        assert "theme" in data
        assert data["layout_mode"] == "expanded"

    def test_config_from_dict(self):
        """测试从字典创建配置"""
        data = {
            "layout_mode": "compact",
            "theme": "dark",
            "layout_width": 100,
        }
        config = Config.from_dict(data)
        assert config.layout_mode == LayoutMode.COMPACT
        assert config.theme == "dark"
        assert config.layout_width == 100

    def test_config_validation(self):
        """测试配置验证"""
        config = Config()
        errors = config.validate()
        assert len(errors) == 0

        config.layout_width = -1
        errors = config.validate()
        assert len(errors) > 0


class TestConfigManager:
    """配置管理器测试"""

    def test_load_default(self):
        """测试加载默认配置"""
        manager = ConfigManager()
        config = manager.load()
        assert config is not None
        assert config.layout_mode == LayoutMode.EXPANDED

    def test_load_from_file(self, temp_config_file):
        """测试从文件加载配置"""
        manager = ConfigManager(config_path=temp_config_file)
        config = manager.load()
        assert config is not None

    def test_save_to_file(self, tmp_path):
        """测试保存配置到文件"""
        config_file = tmp_path / "config.json"
        manager = ConfigManager(config_path=config_file)

        config = get_default_config()
        manager._config = config
        manager.save()

        assert config_file.exists()

        # 验证保存的内容
        data = json.loads(config_file.read_text())
        assert "layout_mode" in data

    def test_update_config(self):
        """测试更新配置"""
        manager = ConfigManager()
        config = manager.get()

        manager.update(theme="dark", layout_width=120)

        assert manager.get().theme == "dark"
        assert manager.get().layout_width == 120

    def test_invalid_update(self):
        """测试无效更新"""
        manager = ConfigManager()
        with pytest.raises(ValueError):
            manager.update(invalid_key="value")
