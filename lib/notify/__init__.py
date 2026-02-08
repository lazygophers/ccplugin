"""
Notify Module - CCPlugin 通知和语音模块

提供多语言支持、系统通知、语音播报和声音克隆功能。
"""

from .config import NotifyConfig, VoiceConfig, load_config, save_config
from .tts import TTSEngine, CoquiTTSEngine, SystemTTSEngine, get_engine, speak
from .voice import VoiceCloner, VoiceTrainer
from .notification import show_system_notification, notify
from .i18n import set_language, translate, SUPPORTED_LANGUAGES

__all__ = [
    # 配置
    'NotifyConfig',
    'VoiceConfig',
    'load_config',
    'save_config',
    # TTS 引擎
    'TTSEngine',
    'CoquiTTSEngine',
    'SystemTTSEngine',
    'get_engine',
    'speak',
    # 声音克隆
    'VoiceCloner',
    'VoiceTrainer',
    # 系统通知
    'show_system_notification',
    'notify',
    # 多语言
    'set_language',
    'translate',
    'SUPPORTED_LANGUAGES',
]
