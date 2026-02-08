"""
CCPlugin lib - Shared library for ccplugin with logging and utilities.
"""

from . import logging
from .logging import enable_debug, info, debug, error, warn
from . import notify
from .notify import (
    NotifyConfig,
    VoiceConfig,
    load_config,
    save_config,
    TTSEngine,
    CoquiTTSEngine,
    SystemTTSEngine,
    get_engine,
    speak,
    VoiceCloner,
    VoiceTrainer,
    show_system_notification,
    notify as notify_func,
    set_language,
    translate,
    SUPPORTED_LANGUAGES,
)

__all__ = [
    # Logging
    'logging',
    'enable_debug',
    'info',
    'debug',
    'error',
    'warn',
    # Notify module
    'notify',
    # Config
    'NotifyConfig',
    'VoiceConfig',
    'load_config',
    'save_config',
    # TTS
    'TTSEngine',
    'CoquiTTSEngine',
    'SystemTTSEngine',
    'get_engine',
    'speak',
    # Voice cloning
    'VoiceCloner',
    'VoiceTrainer',
    # Notification
    'show_system_notification',
    'notify_func',
    # i18n
    'set_language',
    'translate',
    'SUPPORTED_LANGUAGES',
]