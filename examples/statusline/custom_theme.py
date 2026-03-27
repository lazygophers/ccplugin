"""
自定义主题示例
"""

from scripts.statusline.config.manager import get_default_config
from scripts.statusline.core.loop import StatuslineLoop
from scripts.statusline.renderer.theme import Theme, ThemeColors, ThemeSymbols, ThemeManager
import json


def example_builtin_themes():
    """使用内置主题"""
    print("=== 内置主题示例 ===")

    themes = ["default", "minimal", "colorful", "dark", "light"]
    transcript = json.dumps({
        "role": "user",
        "content": "Theme example"
    })

    for theme_name in themes:
        config = get_default_config()
        config.theme = theme_name

        loop = StatuslineLoop(config)
        result = loop.process(transcript)

        print(f"{theme_name:10s}: {result}")

    print()


def example_custom_theme():
    """创建自定义主题"""
    print("=== 自定义主题示例 ===")

    # 创建自定义主题
    custom_theme = Theme(
        name="custom",
        colors=ThemeColors(
            primary="\x1b[35m",  # 紫色
            secondary="\x1b[94m",  # 亮蓝色
            success="\x1b[92m",  # 亮绿色
            warning="\x1b[93m",  # 亮黄色
            error="\x1b[91m",  # 亮红色
        ),
        symbols=ThemeSymbols(
            progress_filled="▓",
            progress_empty="▒",
            error="✗",
            warning="⚠",
            success="✓",
        ),
    )

    # 注册自定义主题
    manager = ThemeManager()
    manager.register_theme(custom_theme)

    # 使用自定义主题
    config = get_default_config()
    config.theme = "custom"

    loop = StatuslineLoop(config)

    transcript = json.dumps({
        "role": "user",
        "content": "Custom theme example"
    })

    result = loop.process(transcript)
    print(f"自定义主题: {result}")
    print()


def example_save_and_load_theme():
    """保存和加载主题"""
    print("=== 保存和加载主题示例 ===")

    import tempfile
    from pathlib import Path

    # 创建主题
    theme = Theme(
        name="saved_theme",
        colors=ThemeColors(
            primary="\x1b[36m",
        ),
    )

    # 保存到临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = Path(f.name)

    manager = ThemeManager()
    manager.save_to_file(theme, temp_path)
    print(f"主题已保存到: {temp_path}")

    # 从文件加载
    loaded_theme = manager.load_from_file(temp_path)
    print(f"已加载主题: {loaded_theme.name}")

    # 清理
    temp_path.unlink()
    print()


if __name__ == "__main__":
    example_builtin_themes()
    example_custom_theme()
    example_save_and_load_theme()
