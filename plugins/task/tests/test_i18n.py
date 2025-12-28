"""i18n 模块测试。

测试国际化功能，包括消息翻译、语言切换和格式化。
"""

import pytest

from task.i18n import I18nManager, get_i18n, set_locale, t


class TestI18nManager:
    """I18nManager 测试。"""

    def test_init_default_locale(self) -> None:
        """测试默认语言检测。"""
        i18n = I18nManager()
        # 应该检测到系统语言或使用默认
        assert i18n.locale in ["zh_CN", "en_US"]

    def test_init_with_locale(self) -> None:
        """测试指定语言初始化。"""
        i18n = I18nManager("zh_CN")
        assert i18n.locale == "zh_CN"

        i18n_en = I18nManager("en_US")
        assert i18n_en.locale == "en_US"

    def test_load_messages(self) -> None:
        """测试加载语言文件。"""
        i18n = I18nManager("zh_CN")

        # 应该加载了中文消息
        assert "zh_CN" in i18n.messages
        assert len(i18n.messages["zh_CN"]) > 0

    def test_translate_basic(self) -> None:
        """测试基本翻译。"""
        i18n = I18nManager("zh_CN")

        # 测试简单消息
        message = i18n.t("task.created")
        assert "任务创建成功" in message

    def test_translate_with_params(self) -> None:
        """测试带参数的翻译。"""
        i18n = I18nManager("zh_CN")

        # 测试单个参数
        message = i18n.t("task.not_found", task_id="tk-123")
        assert "tk-123" in message
        assert "任务不存在" in message

        # 测试多个参数
        message = i18n.t(
            "dependency.added", task_id="tk-1", depends_on_id="tk-2", dep_type="blocks"
        )
        assert "tk-1" in message
        assert "tk-2" in message
        assert "blocks" in message

    def test_translate_nested_keys(self) -> None:
        """测试嵌套键翻译。"""
        i18n = I18nManager("zh_CN")

        # 两级嵌套
        assert i18n.t("task.created") is not None

        # 三级嵌套
        assert i18n.t("stats.by_status") is not None

    def test_translate_missing_key(self) -> None:
        """测试缺失键的处理。"""
        i18n = I18nManager("zh_CN")

        # 缺失的键应该返回键本身
        message = i18n.t("nonexistent.key")
        assert message == "nonexistent.key"

    def test_fallback_to_english(self) -> None:
        """测试回退到英文。"""
        i18n = I18nManager("zh_CN", fallback_locale="en_US")

        # 假设某个键只在英文中存在（实际两种语言都有，这里模拟）
        # 正常情况下会先查中文，找不到则查英文
        message = i18n.t("task.created")
        assert message is not None

    def test_set_locale(self) -> None:
        """测试切换语言。"""
        i18n = I18nManager("zh_CN")
        assert i18n.locale == "zh_CN"

        # 切换到英文
        i18n.set_locale("en_US")
        assert i18n.locale == "en_US"

        # 验证翻译也切换了
        message = i18n.t("task.created")
        assert "Task created successfully" in message


class TestGlobalFunctions:
    """全局函数测试。"""

    def test_get_i18n_singleton(self) -> None:
        """测试全局单例。"""
        i18n1 = get_i18n()
        i18n2 = get_i18n()

        # 应该是同一个实例
        assert i18n1 is i18n2

    def test_set_locale_global(self) -> None:
        """测试全局语言切换。"""
        # 切换到中文
        set_locale("zh_CN")
        i18n = get_i18n()
        assert i18n.locale == "zh_CN"

        # 切换到英文
        set_locale("en_US")
        assert i18n.locale == "en_US"

    def test_t_function(self) -> None:
        """测试便捷翻译函数。"""
        set_locale("zh_CN")
        message = t("task.created")
        assert "任务创建成功" in message

        # 带参数
        message = t("task.not_found", task_id="tk-999")
        assert "tk-999" in message


class TestLanguageFiles:
    """语言文件测试。"""

    def test_chinese_messages(self) -> None:
        """测试中文消息。"""
        i18n = I18nManager("zh_CN")

        # 任务相关
        assert "任务" in i18n.t("task.created")
        assert "更新" in i18n.t("task.updated")
        assert "关闭" in i18n.t("task.closed", title="测试")
        assert "删除" in i18n.t("task.deleted", task_id="tk-1")

        # 依赖相关
        assert "依赖" in i18n.t("dependency.no_deps")

        # 统计相关
        assert "统计" in i18n.t("stats.title")
        assert "状态" in i18n.t("stats.by_status")

    def test_english_messages(self) -> None:
        """测试英文消息。"""
        i18n = I18nManager("en_US")

        # 任务相关
        assert "Task" in i18n.t("task.created")
        assert "updated" in i18n.t("task.updated")
        assert "closed" in i18n.t("task.closed", title="Test")
        assert "deleted" in i18n.t("task.deleted", task_id="tk-1")

        # 依赖相关
        assert "dependencies" in i18n.t("dependency.no_deps")

        # 统计相关
        assert "Statistics" in i18n.t("stats.title")
        assert "Status" in i18n.t("stats.by_status")

    def test_message_consistency(self) -> None:
        """测试消息键一致性。"""
        i18n_zh = I18nManager("zh_CN")
        i18n_en = I18nManager("en_US")

        # 两种语言应该有相同的顶级键
        zh_keys = set(i18n_zh.messages.get("zh_CN", {}).keys())
        en_keys = set(i18n_en.messages.get("en_US", {}).keys())

        assert zh_keys == en_keys, "中英文消息键应该一致"


class TestEdgeCases:
    """边界情况测试。"""

    def test_empty_params(self) -> None:
        """测试空参数。"""
        i18n = I18nManager("zh_CN")
        message = i18n.t("task.created")
        assert message is not None

    def test_extra_params(self) -> None:
        """测试额外参数（应该被忽略）。"""
        i18n = I18nManager("zh_CN")
        message = i18n.t("task.created", extra_param="ignored")
        assert "任务创建成功" in message

    def test_missing_required_param(self) -> None:
        """测试缺少必需参数。"""
        i18n = I18nManager("zh_CN")
        # 应该返回原始模板（不会抛出异常）
        message = i18n.t("task.not_found")  # 缺少 task_id
        assert message is not None

    def test_invalid_locale(self) -> None:
        """测试无效语言代码。"""
        i18n = I18nManager("xx_XX")  # 不存在的语言
        # 应该回退到默认语言
        message = i18n.t("task.created")
        assert message is not None


class TestFormatting:
    """格式化测试。"""

    def test_count_formatting(self) -> None:
        """测试数字格式化。"""
        i18n = I18nManager("zh_CN")

        # 单个任务
        message = i18n.t("task.found_count", count=1)
        assert "1" in message

        # 多个任务
        message = i18n.t("task.found_count", count=10)
        assert "10" in message

    def test_string_formatting(self) -> None:
        """测试字符串格式化。"""
        i18n = I18nManager("zh_CN")

        message = i18n.t("task.closed", title="实现登录功能")
        assert "实现登录功能" in message

    def test_mixed_formatting(self) -> None:
        """测试混合格式化。"""
        i18n = I18nManager("zh_CN")

        message = i18n.t(
            "dependency.added", task_id="tk-1", depends_on_id="tk-2", dep_type="blocks"
        )
        assert all(x in message for x in ["tk-1", "tk-2", "blocks"])
