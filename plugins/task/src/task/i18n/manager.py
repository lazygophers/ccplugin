"""i18n 管理器。

负责加载语言文件、翻译消息和格式化输出。
"""

import json
import os
from pathlib import Path
from typing import Any


class I18nManager:
    """国际化管理器。

    支持多语言消息翻译和格式化。

    Attributes:
        locale: 当前语言环境（如 'zh_CN', 'en_US'）
        messages: 翻译消息字典
        fallback_locale: 备用语言（默认英文）
    """

    def __init__(self, locale: str | None = None, fallback_locale: str = "en_US") -> None:
        """初始化 i18n 管理器。

        Args:
            locale: 语言环境（默认从环境变量读取）
            fallback_locale: 备用语言（默认 en_US）
        """
        self.locale = locale or self._detect_locale()
        self.fallback_locale = fallback_locale
        self.messages: dict[str, dict[str, str]] = {}
        self._load_messages()

    def _detect_locale(self) -> str:
        """检测系统语言环境。

        Returns:
            语言代码（zh_CN / en_US）
        """
        # 优先使用环境变量
        lang = os.getenv("TASK_LOCALE") or os.getenv("LANG", "en_US.UTF-8")

        # 解析语言代码
        if "zh" in lang.lower() or "chinese" in lang.lower():
            return "zh_CN"
        return "en_US"

    def _load_messages(self) -> None:
        """加载语言文件。"""
        locale_dir = Path(__file__).parent / "locales"

        # 加载当前语言
        self._load_locale_file(self.locale, locale_dir)

        # 加载备用语言（如果不同）
        if self.locale != self.fallback_locale:
            self._load_locale_file(self.fallback_locale, locale_dir)

    def _load_locale_file(self, locale: str, locale_dir: Path) -> None:
        """加载单个语言文件。

        Args:
            locale: 语言代码
            locale_dir: 语言文件目录
        """
        locale_file = locale_dir / f"{locale}.json"

        if locale_file.exists():
            try:
                with open(locale_file, encoding="utf-8") as f:
                    self.messages[locale] = json.load(f)
            except (json.JSONDecodeError, OSError):
                # 加载失败，使用空字典
                self.messages[locale] = {}
        else:
            self.messages[locale] = {}

    def t(self, key: str, **kwargs: Any) -> str:
        """翻译消息。

        Args:
            key: 消息键（支持点号分隔的嵌套键）
            **kwargs: 格式化参数

        Returns:
            翻译后的消息

        Example:
            >>> i18n = I18nManager("zh_CN")
            >>> i18n.t("task.created", task_id="tk-123")
            "✅ 任务创建成功: tk-123"
        """
        # 尝试当前语言
        message = self._get_message(key, self.locale)

        # 回退到备用语言
        if message is None and self.locale != self.fallback_locale:
            message = self._get_message(key, self.fallback_locale)

        # 如果都找不到，返回键本身
        if message is None:
            return key

        # 格式化消息
        try:
            return message.format(**kwargs)
        except (KeyError, ValueError):
            return message

    def _get_message(self, key: str, locale: str) -> str | None:
        """从语言字典中获取消息。

        Args:
            key: 消息键（支持点号分隔）
            locale: 语言代码

        Returns:
            消息字符串，如果未找到返回 None
        """
        messages = self.messages.get(locale, {})

        # 支持嵌套键（如 "task.created"）
        keys = key.split(".")
        value: Any = messages

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return None

        return value if isinstance(value, str) else None

    def set_locale(self, locale: str) -> None:
        """切换语言。

        Args:
            locale: 新的语言代码
        """
        if locale != self.locale:
            self.locale = locale
            # 重新加载消息（如果还未加载）
            if locale not in self.messages:
                locale_dir = Path(__file__).parent / "locales"
                self._load_locale_file(locale, locale_dir)


# 全局单例
_i18n_instance: I18nManager | None = None


def get_i18n() -> I18nManager:
    """获取全局 i18n 管理器实例。

    Returns:
        I18nManager 单例
    """
    global _i18n_instance
    if _i18n_instance is None:
        _i18n_instance = I18nManager()
    return _i18n_instance


def set_locale(locale: str) -> None:
    """设置全局语言。

    Args:
        locale: 语言代码（zh_CN / en_US）
    """
    get_i18n().set_locale(locale)


def t(key: str, **kwargs: Any) -> str:
    """便捷翻译函数。

    Args:
        key: 消息键
        **kwargs: 格式化参数

    Returns:
        翻译后的消息
    """
    return get_i18n().t(key, **kwargs)
