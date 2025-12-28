"""国际化（i18n）支持模块。

本模块提供多语言支持，包括：
- 消息翻译
- 语言切换
- 格式化输出
"""

from .manager import I18nManager, get_i18n, set_locale, t

__all__ = ["I18nManager", "get_i18n", "set_locale", "t"]
