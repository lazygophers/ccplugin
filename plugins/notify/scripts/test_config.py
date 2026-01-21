"""
Hook 配置系统单元测试
"""

import tempfile
from pathlib import Path
import pytest
import yaml
from config import (
    NotificationConfig,
    StopHookConfig,
    NotificationHookConfig,
    PermissionHookConfig,
    HooksConfig,
    HookEventType,
    NotificationType,
    NotificationChannel,
)


class TestNotificationConfig:
    """通知配置测试"""

    def test_default_notification_config(self):
        """测试默认通知配置"""
        config = NotificationConfig()
        assert config.enabled is True
        assert config.channels == ["macos_notification"]
        assert config.play_sound is False
        assert config.template is None

    def test_notification_config_validation(self):
        """测试通知配置验证"""
        # 有效配置
        config = NotificationConfig(
            enabled=True,
            channels=["macos_notification", "file_log"],
            play_sound=True,
            template="Test template"
        )
        assert config.validate() is True

        # 无效的通知渠道
        config = NotificationConfig(channels=["invalid_channel"])
        with pytest.raises(ValueError, match="无效的通知渠道"):
            config.validate()

        # 无效的数据类型
        config = NotificationConfig(enabled="yes")
        with pytest.raises(ValueError, match="enabled 必须是 bool 类型"):
            config.validate()


class TestStopHookConfig:
    """Stop Hook 配置测试"""

    def test_default_stop_hook_config(self):
        """测试默认 Stop Hook 配置"""
        config = StopHookConfig()
        assert config.enabled is True
        assert config.notification.enabled is True
        assert config.script_path is None

    def test_stop_hook_config_with_custom_values(self):
        """测试自定义 Stop Hook 配置"""
        notification = NotificationConfig(
            enabled=True,
            channels=["file_log"],
            play_sound=True
        )
        config = StopHookConfig(
            enabled=True,
            notification=notification,
            script_path="/path/to/script.py"
        )
        assert config.enabled is True
        assert config.script_path == "/path/to/script.py"
        assert config.validate() is True

    def test_stop_hook_config_validation(self):
        """测试 Stop Hook 配置验证"""
        config = StopHookConfig(enabled="invalid")
        with pytest.raises(ValueError, match="enabled 必须是 bool 类型"):
            config.validate()


class TestNotificationHookConfig:
    """Notification Hook 配置测试"""

    def test_default_notification_hook_config(self):
        """测试默认 Notification Hook 配置"""
        config = NotificationHookConfig()
        assert config.enabled is True
        assert config.permission_prompt.enabled is True
        assert config.warning.enabled is True
        assert config.info.enabled is False
        assert config.error.enabled is True

    def test_notification_hook_config_validation(self):
        """测试 Notification Hook 配置验证"""
        config = NotificationHookConfig(enabled=True)
        assert config.validate() is True

    def test_notification_hook_config_with_invalid_sub_config(self):
        """测试带有无效子配置的 Notification Hook"""
        config = NotificationHookConfig(
            permission_prompt=NotificationConfig(channels=["invalid"])
        )
        with pytest.raises(ValueError):
            config.validate()


class TestPermissionHookConfig:
    """Permission Hook 配置测试"""

    def test_default_permission_hook_config(self):
        """测试默认 Permission Hook 配置"""
        config = PermissionHookConfig()
        assert config.enabled is True
        assert config.notification.enabled is True

    def test_permission_hook_config_validation(self):
        """测试 Permission Hook 配置验证"""
        config = PermissionHookConfig()
        assert config.validate() is True


class TestHooksConfig:
    """完整 Hooks 配置测试"""

    def test_default_hooks_config(self):
        """测试默认完整配置"""
        config = HooksConfig()
        assert config.stop_hook.enabled is True
        assert config.notification_hook.enabled is True
        assert config.permission_hook.enabled is True

    def test_hooks_config_from_dict(self):
        """测试从字典加载配置"""
        config_dict = {
            "stop_hook": {
                "enabled": True,
                "notification": {
                    "enabled": True,
                    "channels": ["macos_notification"],
                    "play_sound": False
                }
            },
            "notification_hook": {
                "enabled": True,
                "permission_prompt": {
                    "enabled": True,
                    "channels": ["macos_notification"],
                    "play_sound": True
                },
                "warning": {
                    "enabled": True,
                    "channels": ["file_log"]
                },
                "info": {
                    "enabled": False
                },
                "error": {
                    "enabled": True,
                    "channels": ["macos_notification"]
                }
            },
            "permission_hook": {
                "enabled": False
            }
        }

        config = HooksConfig.from_dict(config_dict)
        assert config.stop_hook.enabled is True
        assert config.permission_hook.enabled is False

    def test_hooks_config_save_and_load(self):
        """测试配置文件保存和加载"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "hooks.yaml"

            # 创建并保存配置
            original_config = HooksConfig(
                stop_hook=StopHookConfig(
                    enabled=True,
                    notification=NotificationConfig(
                        enabled=True,
                        channels=["macos_notification"],
                        play_sound=True
                    )
                )
            )
            original_config.save_to_file(config_path)

            # 加载并验证
            loaded_config = HooksConfig.load_from_file(config_path)
            assert loaded_config.stop_hook.enabled is True
            assert loaded_config.stop_hook.notification.play_sound is True

    def test_hooks_config_to_dict(self):
        """测试配置转字典"""
        config = HooksConfig()
        config_dict = config.to_dict()

        assert "stop_hook" in config_dict
        assert "notification_hook" in config_dict
        assert "permission_hook" in config_dict

    def test_hooks_config_validation(self):
        """测试完整配置验证"""
        config = HooksConfig()
        assert config.validate() is True

    def test_hooks_config_validation_with_invalid_sub_config(self):
        """测试带有无效子配置的完整验证"""
        config = HooksConfig(
            stop_hook=StopHookConfig(
                notification=NotificationConfig(channels=["invalid"])
            )
        )
        with pytest.raises(ValueError):
            config.validate()


class TestConfigFileHandling:
    """配置文件处理测试"""

    def test_load_from_nonexistent_file(self):
        """测试加载不存在的文件"""
        config_path = Path("/nonexistent/path/hooks.yaml")
        with pytest.raises(FileNotFoundError):
            HooksConfig.load_from_file(config_path)

    def test_save_creates_directory(self):
        """测试保存时创建目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "subdir" / "hooks.yaml"
            config = HooksConfig()
            config.save_to_file(config_path)

            assert config_path.exists()
            assert config_path.parent.exists()

    def test_yaml_file_format(self):
        """测试生成的 YAML 格式"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "hooks.yaml"
            config = HooksConfig()
            config.save_to_file(config_path)

            # 验证文件可被 YAML 解析
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded_data = yaml.safe_load(f)

            assert isinstance(loaded_data, dict)
            assert "stop_hook" in loaded_data
            assert "notification_hook" in loaded_data
            assert "permission_hook" in loaded_data


class TestEnumTypes:
    """枚举类型测试"""

    def test_hook_event_type_values(self):
        """测试 Hook 事件类型枚举"""
        assert HookEventType.STOP.value == "stop"
        assert HookEventType.NOTIFICATION.value == "notification"
        assert HookEventType.PERMISSION.value == "permission"

    def test_notification_type_values(self):
        """测试通知类型枚举"""
        assert NotificationType.PERMISSION_PROMPT.value == "permission_prompt"
        assert NotificationType.WARNING.value == "warning"
        assert NotificationType.INFO.value == "info"
        assert NotificationType.ERROR.value == "error"

    def test_notification_channel_values(self):
        """测试通知渠道枚举"""
        assert NotificationChannel.MACOS_NOTIFICATION.value == "macos_notification"
        assert NotificationChannel.SYSTEM_LOG.value == "system_log"
        assert NotificationChannel.FILE_LOG.value == "file_log"
        assert NotificationChannel.ALL.value == "all"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
