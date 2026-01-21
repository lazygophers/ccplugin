"""Notify Plugin Scripts"""

try:
    from .notifier import Notifier, notify
    __all__ = ["Notifier", "notify"]
except ImportError:
    # notifier 模块可能还未实现
    __all__ = []

try:
    from .notify import play_text_tts, show_system_notification
    __all__.extend(["play_text_tts", "show_system_notification"])
except ImportError:
    # notify 模块可能还未实现
    pass
