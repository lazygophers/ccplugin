"""
Claude Code Hooks 配置系统单元测试
"""

import tempfile
from pathlib import Path
import pytest
import yaml
from .config import (
    HookConfig,
    ToolSpecificHookConfig,
    NotificationTypeHookConfig,
    SessionStartHookConfig,
    SessionEndHookConfig,
    PreCompactHookConfig,
    HooksConfig,
    load_config,
)


class TestHookConfig:
    """单个 Hook 配置测试"""

    def test_default_hook_config(self):
        """测试默认 Hook 配置"""
        config = HookConfig()
        assert config.enabled is False
        assert config.play_sound is False
        assert config.message is None

    def test_hook_config_with_values(self):
        """测试带值的 Hook 配置"""
        config = HookConfig(enabled=True, play_sound=True, message="Test message")
        assert config.enabled is True
        assert config.play_sound is True
        assert config.message == "Test message"

    def test_hook_config_validation(self):
        """测试 Hook 配置验证"""
        config = HookConfig(enabled=True, play_sound=False, message="Test")
        assert config.validate() is True

        # 无效的 enabled 类型
        config = HookConfig(enabled="yes")
        with pytest.raises(ValueError, match="enabled 必须是 bool 类型"):
            config.validate()

        # 无效的 play_sound 类型
        config = HookConfig(play_sound="no")
        with pytest.raises(ValueError, match="play_sound 必须是 bool 类型"):
            config.validate()

        # 无效的 message 类型
        config = HookConfig(message=123)
        with pytest.raises(ValueError, match="message 必须是 str 类型或 None"):
            config.validate()


class TestToolSpecificHookConfig:
    """工具特定 Hook 配置测试"""

    def test_default_tool_specific_config(self):
        """测试默认工具特定配置"""
        config = ToolSpecificHookConfig()
        assert config.write.enabled is False
        assert config.edit.enabled is False
        assert config.bash.enabled is False
        assert config.task.enabled is False
        assert config.webfetch.enabled is False
        assert config.websearch.enabled is False

    def test_tool_specific_config_validation(self):
        """测试工具特定配置验证"""
        config = ToolSpecificHookConfig()
        assert config.validate() is True


class TestNotificationTypeHookConfig:
    """通知类型 Hook 配置测试"""

    def test_default_notification_config(self):
        """测试默认通知配置"""
        config = NotificationTypeHookConfig()
        assert config.permission_prompt.enabled is False
        assert config.idle_prompt.enabled is False
        assert config.auth_success.enabled is False
        assert config.elicitation_dialog.enabled is False

    def test_notification_config_validation(self):
        """测试通知配置验证"""
        config = NotificationTypeHookConfig()
        assert config.validate() is True


class TestSessionStartHookConfig:
    """SessionStart Hook 配置测试"""

    def test_default_session_start_config(self):
        """测试默认 SessionStart 配置"""
        config = SessionStartHookConfig()
        assert config.startup.enabled is False
        assert config.resume.enabled is False
        assert config.clear.enabled is False
        assert config.compact.enabled is False

    def test_session_start_config_validation(self):
        """测试 SessionStart 配置验证"""
        config = SessionStartHookConfig()
        assert config.validate() is True


class TestSessionEndHookConfig:
    """SessionEnd Hook 配置测试"""

    def test_default_session_end_config(self):
        """测试默认 SessionEnd 配置"""
        config = SessionEndHookConfig()
        assert config.clear.enabled is False
        assert config.logout.enabled is False
        assert config.prompt_input_exit.enabled is False
        assert config.other.enabled is False

    def test_session_end_config_validation(self):
        """测试 SessionEnd 配置验证"""
        config = SessionEndHookConfig()
        assert config.validate() is True


class TestPreCompactHookConfig:
    """PreCompact Hook 配置测试"""

    def test_default_pre_compact_config(self):
        """测试默认 PreCompact 配置"""
        config = PreCompactHookConfig()
        assert config.manual.enabled is False
        assert config.auto.enabled is False

    def test_pre_compact_config_validation(self):
        """测试 PreCompact 配置验证"""
        config = PreCompactHookConfig()
        assert config.validate() is True


class TestHooksConfig:
    """完整 Hooks 配置测试"""

    def test_default_hooks_config(self):
        """测试默认 Hooks 配置"""
        config = HooksConfig()
        assert config.stop.enabled is True
        assert config.stop.play_sound is True
        assert config.subagent_stop.enabled is False
        assert config.permission_request.enabled is False
        assert config.user_prompt_submit.enabled is False

    def test_hooks_config_validation(self):
        """测试 Hooks 配置验证"""
        config = HooksConfig()
        assert config.validate() is True

    def test_hooks_config_from_dict(self):
        """测试从字典加载配置"""
        config_dict = {
            "hooks": {
                "stop": {
                    "enabled": True,
                    "play_sound": True,
                    "message": "Session stopped"
                },
                "notification": {
                    "permission_prompt": {
                        "enabled": False,
                        "play_sound": False,
                        "message": "Permission required"
                    }
                },
                "session_start": {
                    "startup": {
                        "enabled": False,
                        "play_sound": False,
                        "message": "Session started"
                    }
                }
            }
        }

        config = HooksConfig.from_dict(config_dict)
        assert config.stop.enabled is True
        assert config.stop.message == "Session stopped"
        assert config.notification.permission_prompt.enabled is False
        assert config.session_start.startup.enabled is False

    def test_hooks_config_to_dict(self):
        """测试转换为字典"""
        config = HooksConfig()
        config_dict = config.to_dict()

        assert "hooks" in config_dict
        assert "stop" in config_dict["hooks"]
        assert config_dict["hooks"]["stop"]["enabled"] is True

    def test_hooks_config_save_load(self):
        """测试保存和加载配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"

            # 创建和保存配置
            original_config = HooksConfig()
            original_config.save_to_file(config_path)

            # 加载配置
            loaded_config = HooksConfig.load_from_file(config_path)

            # 验证加载的配置
            assert loaded_config.stop.enabled == original_config.stop.enabled
            assert loaded_config.stop.play_sound == original_config.stop.play_sound

    def test_hooks_config_file_not_found(self):
        """测试加载不存在的文件"""
        config_path = Path("/nonexistent/config.yaml")
        with pytest.raises(FileNotFoundError):
            HooksConfig.load_from_file(config_path)


class TestLoadConfig:
    """加载配置函数测试"""

    def test_load_default_config(self):
        """测试加载默认配置"""
        from .config import get_default_config
        config = get_default_config()
        assert config.stop.enabled is True

    def test_load_custom_config(self):
        """测试加载自定义配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"

            # 创建自定义配置
            custom_config = HooksConfig()
            custom_config.subagent_stop.enabled = True
            custom_config.save_to_file(config_path)

            # 加载自定义配置
            loaded_config = load_config(config_path)
            assert loaded_config.subagent_stop.enabled is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
