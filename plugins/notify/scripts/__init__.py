"""Notify Plugin Scripts"""

try:
    from .notifier import Notifier, notify
    __all__ = ["Notifier", "notify"]
except ImportError:
    # notifier 模块可能还未实现
    __all__ = []
