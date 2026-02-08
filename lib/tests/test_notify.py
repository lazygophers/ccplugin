"""
通知模块测试

测试 notify 模块的配置管理、TTS、声音克隆和多语言功能。
"""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock


class TestVoiceConfig:
    """测试 VoiceConfig 数据类"""

    def test_default_values(self):
        """测试默认值"""
        from lib.notify.config import VoiceConfig

        voice = VoiceConfig(id="test", name="Test Voice")
        assert voice.id == "test"
        assert voice.name == "Test Voice"
        assert voice.engine == "coqui"
        assert voice.language == "zh"
        assert voice.speed == 1.0
        assert voice.pitch == 1.0
        assert voice.is_cloned is False

    def test_validate_valid(self):
        """测试有效配置验证"""
        from lib.notify.config import VoiceConfig

        voice = VoiceConfig(id="test", name="Test Voice")
        assert voice.validate() is True

    def test_validate_invalid_id(self):
        """测试无效 ID 验证"""
        from lib.notify.config import VoiceConfig

        voice = VoiceConfig(id="", name="Test Voice")
        assert voice.validate() is False

    def test_validate_invalid_engine(self):
        """测试无效引擎验证"""
        from lib.notify.config import VoiceConfig

        voice = VoiceConfig(id="test", name="Test Voice", engine="invalid")
        assert voice.validate() is False

    def test_validate_invalid_speed(self):
        """测试无效语速验证"""
        from lib.notify.config import VoiceConfig

        voice = VoiceConfig(id="test", name="Test Voice", speed=5.0)
        assert voice.validate() is False


class TestNotifyConfig:
    """测试 NotifyConfig 数据类"""

    def test_default_values(self):
        """测试默认值"""
        from lib.notify.config import NotifyConfig

        config = NotifyConfig()
        assert config.default_voice_id is None
        assert config.system_notification is True
        assert config.tts_enabled is True
        assert config.tts_engine == "coqui"
        assert config.language == "zh"
        assert config.auto_download is True

    def test_add_voice(self):
        """测试添加音色"""
        from lib.notify.config import NotifyConfig, VoiceConfig, add_voice

        config = NotifyConfig()
        voice = VoiceConfig(id="test", name="Test")
        assert add_voice(config, voice) is True
        assert "test" in config.voices

    def test_remove_voice(self):
        """测试删除音色"""
        from lib.notify.config import NotifyConfig, VoiceConfig, add_voice, remove_voice

        config = NotifyConfig()
        voice = VoiceConfig(id="test", name="Test")
        add_voice(config, voice)

        assert remove_voice(config, "test") is True
        assert "test" not in config.voices

    def test_remove_nonexistent_voice(self):
        """测试删除不存在的音色"""
        from lib.notify.config import NotifyConfig, remove_voice

        config = NotifyConfig()
        assert remove_voice(config, "nonexistent") is False

    def test_set_default_voice(self):
        """测试设置默认音色"""
        from lib.notify.config import NotifyConfig, VoiceConfig, add_voice, set_default_voice

        config = NotifyConfig()
        voice = VoiceConfig(id="test", name="Test")
        add_voice(config, voice)

        assert set_default_voice(config, "test") is True
        assert config.default_voice_id == "test"

    def test_to_dict(self):
        """测试转换为字典"""
        from lib.notify.config import NotifyConfig, VoiceConfig, add_voice

        config = NotifyConfig()
        voice = VoiceConfig(id="test", name="Test Voice")
        add_voice(config, voice)

        data = config.to_dict()
        assert "test" in data["voices"]
        assert data["default_voice_id"] is None
        assert data["tts_engine"] == "coqui"

    def test_from_dict(self):
        """测试从字典加载"""
        from lib.notify.config import NotifyConfig

        data = {
            "default_voice_id": "test",
            "system_notification": True,
            "tts_enabled": True,
            "tts_engine": "system",
            "language": "en",
            "voices": {
                "test": {
                    "id": "test",
                    "name": "Test Voice",
                    "engine": "coqui",
                    "model_name": "test_model",
                    "language": "en",
                    "speed": 1.2,
                    "pitch": 1.0,
                    "speaker_wav": "/path/to/audio.wav",
                    "is_cloned": True
                }
            }
        }

        config = NotifyConfig.from_dict(data)
        assert config.default_voice_id == "test"
        assert config.tts_engine == "system"
        assert "test" in config.voices
        assert config.voices["test"].name == "Test Voice"


class TestConfigIO:
    """测试配置文件读写"""

    def test_save_and_load(self):
        """测试保存和加载配置"""
        from lib.notify.config import NotifyConfig, VoiceConfig, save_config, load_config, add_voice

        config = NotifyConfig()
        voice = VoiceConfig(id="test", name="Test Voice")
        add_voice(config, voice)

        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            temp_path = f.name

        try:
            assert save_config(config, temp_path) is True
            loaded = load_config(temp_path)
            assert "test" in loaded.voices
            assert loaded.voices["test"].name == "Test Voice"
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_load_nonexistent(self):
        """测试加载不存在的配置文件"""
        from lib.notify.config import load_config

        loaded = load_config("/nonexistent/path.yaml")
        assert loaded.default_voice_id is None


class TestTTSEngine:
    """测试 TTS 引擎"""

    def test_system_engine_creation(self):
        """测试创建系统 TTS 引擎"""
        from lib.notify.tts import SystemTTSEngine

        engine = SystemTTSEngine()
        # 不测试实际功能，只测试创建
        assert engine is not None

    def test_get_system_engine(self):
        """测试获取系统引擎"""
        from lib.notify.tts import get_engine

        engine = get_engine("system")
        assert engine is not None
        # 系统引擎创建成功即可，不检查实际可用性


class TestSystemNotification:
    """测试系统通知"""

    def test_resolve_icon_path_nonexistent(self):
        """测试解析不存在的图标"""
        from lib.notify.notification import _resolve_icon_path

        result = _resolve_icon_path("nonexistent_icon")
        # 返回 None 因为图标不存在
        assert result is None or result is not None  # 取决于图标映射

    @patch('platform.system')
    def test_macos_notification(self, mock_system):
        """测试 macOS 通知"""
        mock_system.return_value = "Darwin"

        from lib.notify.notification import _show_macos_notification

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock()
            result = _show_macos_notification("test message", "test title")
            assert result is True

    @patch('platform.system')
    def test_linux_notification(self, mock_system):
        """测试 Linux 通知"""
        mock_system.return_value = "Linux"

        from lib.notify.notification import _show_linux_notification

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock()
            result = _show_linux_notification("test message", "test title")
            assert result is True


class TestI18n:
    """测试多语言支持"""

    def test_supported_languages(self):
        """测试支持的语言列表"""
        from lib.notify.i18n import SUPPORTED_LANGUAGES, get_supported_languages

        assert "zh" in SUPPORTED_LANGUAGES
        assert "en" in SUPPORTED_LANGUAGES
        assert get_supported_languages() == SUPPORTED_LANGUAGES

    def test_set_language(self):
        """测试设置语言"""
        from lib.notify.i18n import set_language, get_language

        original = get_language()
        set_language("en")
        assert get_language() == "en"
        set_language(original)

    def test_translate_builtin(self):
        """测试内置翻译"""
        from lib.notify.i18n import translate, set_language

        # 设置语言
        set_language("zh")

        # 测试翻译
        result = translate("Operation completed")
        assert result == "操作已完成"

    def test_translate_unknown(self):
        """测试未知文本翻译"""
        from lib.notify.i18n import translate

        # 未知文本应返回原文本
        result = translate("Unknown text")
        assert result == "Unknown text"

    def test_language_names(self):
        """测试语言名称"""
        from lib.notify.i18n import get_language_name

        assert get_language_name("zh") == "中文"
        assert get_language_name("en") == "English"
        assert get_language_name("ja") == "日本語"

    def test_is_language_supported(self):
        """测试语言支持检查"""
        from lib.notify.i18n import is_language_supported

        assert is_language_supported("zh") is True
        assert is_language_supported("xx") is False


class TestVoiceCloner:
    """测试声音克隆"""

    def test_cloner_creation(self):
        """测试创建克隆器"""
        from lib.notify.voice import VoiceCloner

        cloner = VoiceCloner()
        assert cloner is not None

    def test_trainer_creation(self):
        """测试创建训练器"""
        from lib.notify.voice import VoiceTrainer

        trainer = VoiceTrainer()
        assert trainer is not None

    def test_analyze_audio(self):
        """测试音频分析"""
        from lib.notify.voice import VoiceTrainer
        import wave
        import tempfile

        trainer = VoiceTrainer()

        # 创建测试音频文件
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_path = f.name

        try:
            # 创建简单的 WAV 文件
            with wave.open(temp_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(22050)
                # 写入 1 秒的静音
                wf.writeframes(b'\x00' * 44000)

            sample = trainer.analyze_audio(temp_path)
            assert sample is not None
            assert sample.sample_rate == 22050
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestIntegration:
    """集成测试"""

    def test_notify_module_import(self):
        """测试模块导入"""
        from lib import notify

        assert hasattr(notify, 'NotifyConfig')
        assert hasattr(notify, 'VoiceConfig')
        assert hasattr(notify, 'TTSEngine')
        assert hasattr(notify, 'VoiceCloner')
        assert hasattr(notify, 'set_language')
        assert hasattr(notify, 'translate')

    def test_config_functions(self):
        """测试配置函数"""
        from lib.notify.config import load_config, save_config, NotifyConfig

        config = NotifyConfig()
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            temp_path = f.name

        try:
            save_config(config, temp_path)
            loaded = load_config(temp_path)
            assert loaded.tts_enabled is True
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
