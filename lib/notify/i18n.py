"""
多语言支持模块

提供语言设置、文本翻译和本地化功能。
"""

from typing import Dict, Optional, Callable

# 支持的语言列表
SUPPORTED_LANGUAGES = [
    "zh",   # 中文
    "en",   # 英语
    "ja",   # 日语
    "ko",   # 韩语
    "fr",   # 法语
    "de",   # 德语
    "es",   # 西班牙语
    "it",   # 意大利语
    "pt",   # 葡萄牙语
    "ru",   # 俄语
    "ar",   # 阿拉伯语
    "hi",   # 印地语
]

# 语言名称映射
LANGUAGE_NAMES = {
    "zh": "中文",
    "en": "English",
    "ja": "日本語",
    "ko": "한국어",
    "fr": "Français",
    "de": "Deutsch",
    "es": "Español",
    "it": "Italiano",
    "pt": "Português",
    "ru": "Русский",
    "ar": "العربية",
    "hi": "हिन्दी",
}

# 默认语言
_default_language: str = "zh"

# 翻译字典
_translations: Dict[str, Dict[str, str]] = {}

# 自定义翻译器
_custom_translator: Optional[Callable[[str, str], str]] = None


def set_language(lang: str) -> bool:
    """设置当前语言

    Args:
        lang: 语言代码

    Returns:
        设置成功返回 True
    """
    global _default_language

    if lang in SUPPORTED_LANGUAGES:
        _default_language = lang
        return True
    else:
        from lib.logging import warn
        warn(f"不支持的语言: {lang}，将使用默认语言")
        return False


def get_language() -> str:
    """获取当前语言"""
    return _default_language


def get_language_name(lang: str) -> str:
    """获取语言名称

    Args:
        lang: 语言代码

    Returns:
        语言本地化名称
    """
    return LANGUAGE_NAMES.get(lang, lang)


def set_custom_translator(
    translator: Callable[[str, str], str]
) -> None:
    """设置自定义翻译器

    Args:
        translator: 翻译函数，接受 (text, lang) 参数
    """
    global _custom_translator
    _custom_translator = translator


def translate(
    text: str,
    lang: Optional[str] = None
) -> str:
    """翻译文本到指定语言

    如果没有找到翻译，返回原文本。

    Args:
        text: 要翻译的文本
        lang: 目标语言代码，如果为 None 则使用当前语言

    Returns:
        翻译后的文本
    """
    if lang is None:
        lang = get_language()

    # 使用自定义翻译器
    if _custom_translator:
        return _custom_translator(text, lang)

    # 从内置翻译字典查找
    if lang in _translations:
        lang_dict = _translations[lang]
        if text in lang_dict:
            return lang_dict[text]

    # 如果是中文且目标语言不是中文，使用翻译字典
    if lang != "zh" and "zh" in _translations:
        zh_dict = _translations.get("zh", {})
        if text in zh_dict:
            # 尝试查找目标语言
            pass

    return text


def register_translations(
    lang: str,
    translations: Dict[str, str]
) -> None:
    """注册翻译字典

    Args:
        lang: 语言代码
        translations: 翻译字典 {原文: 译文}
    """
    global _translations

    if lang not in _translations:
        _translations[lang] = {}

    _translations[lang].update(translations)


def get_supported_languages() -> list:
    """获取支持的语言列表"""
    return SUPPORTED_LANGUAGES.copy()


def is_language_supported(lang: str) -> bool:
    """检查语言是否支持"""
    return lang in SUPPORTED_LANGUAGES


# 内置翻译字典 - 常用操作提示
BUILTIN_TRANSLATIONS = {
    "zh": {
        # 系统通知
        "Operation completed": "操作已完成",
        "Operation failed": "操作失败",
        "Permission required": "需要权限",
        "Task finished": "任务已完成",
        "Session started": "会话已启动",
        "Session ended": "会话已结束",

        # 工具使用
        "Reading file": "正在读取文件",
        "Writing file": "正在写入文件",
        "Editing file": "正在编辑文件",
        "Running command": "正在运行命令",
        "Searching...": "正在搜索...",

        # 错误提示
        "Error occurred": "发生错误",
        "File not found": "文件未找到",
        "Invalid input": "输入无效",
        "Network error": "网络错误",

        # 确认提示
        "Continue?": "是否继续？",
        "Yes": "是",
        "No": "否",
        "Cancel": "取消",
        "OK": "确定",
    },
    "ja": {
        "Operation completed": "操作が完了しました",
        "Operation failed": "操作に失敗しました",
        "Permission required": "権限が必要です",
        "Task finished": "タスクが完了しました",
        "Session started": "セッションが開始されました",
        "Session ended": "セッションが終了しました",
    },
    "ko": {
        "Operation completed": "작업이 완료되었습니다",
        "Operation failed": "작업이 실패했습니다",
        "Permission required": "권한이 필요합니다",
        "Task finished": "작업이 완료되었습니다",
        "Session started": "세션이 시작되었습니다",
        "Session ended": "세션이 종료되었습니다",
    },
}

# 注册内置翻译
for lang, translations in BUILTIN_TRANSLATIONS.items():
    register_translations(lang, translations)


class I18n:
    """国际化管理器"""

    def __init__(self, lang: Optional[str] = None):
        """初始化

        Args:
            lang: 初始语言代码
        """
        if lang:
            set_language(lang)

    def t(self, text: str, lang: Optional[str] = None) -> str:
        """翻译文本

        Args:
            text: 要翻译的文本
            lang: 目标语言

        Returns:
            翻译后的文本
        """
        return translate(text, lang)

    @property
    def current_lang(self) -> str:
        """获取当前语言"""
        return get_language()

    @current_lang.setter
    def current_lang(self, lang: str) -> None:
        """设置当前语言"""
        set_language(lang)

    def list_languages(self) -> list:
        """列出支持的语言"""
        return get_supported_languages()

    def get_language_name(self, lang: str) -> str:
        """获取语言名称"""
        return get_language_name(lang)
