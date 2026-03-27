"""
基本使用示例
"""

from scripts.statusline.config.manager import get_default_config, Config, LayoutMode
from scripts.statusline.core.loop import StatuslineLoop
import json


def example_basic():
    """基本使用示例"""
    print("=== 基本使用示例 ===")

    # 使用默认配置
    config = get_default_config()
    loop = StatuslineLoop(config)

    # 处理简单的用户消息
    transcript = json.dumps({
        "role": "user",
        "content": "Hello, world!"
    })

    result = loop.process(transcript)
    print(f"结果: {result}")
    print()


def example_custom_config():
    """自定义配置示例"""
    print("=== 自定义配置示例 ===")

    # 创建自定义配置
    config = Config(
        layout_mode=LayoutMode.COMPACT,
        theme="dark",
        layout_width=60,
        show_user=True,
        show_progress=True,
        show_resources=True,
    )

    loop = StatuslineLoop(config)

    # 处理消息
    transcript = json.dumps({
        "role": "user",
        "content": "Custom config example"
    })

    result = loop.process(transcript)
    print(f"结果: {result}")
    print()


def example_multi_turn():
    """多轮对话示例"""
    print("=== 多轮对话示例 ===")

    config = get_default_config()
    loop = StatuslineLoop(config)

    # 模拟多轮对话
    conversations = [
        {"role": "user", "content": "First question"},
        {"role": "assistant", "content": "First response"},
        {"role": "user", "content": "Second question"},
        {"role": "assistant", "content": "Second response"},
    ]

    for msg in conversations:
        transcript = json.dumps(msg)
        result = loop.process(transcript)
        print(f"{msg['role']}: {result}")
    print()


def example_layout_comparison():
    """布局比较示例"""
    print("=== 布局比较示例 ===")

    transcript = json.dumps({
        "role": "user",
        "content": "Layout comparison"
    })

    # 扩展布局
    config_expanded = Config(layout_mode=LayoutMode.EXPANDED)
    loop_expanded = StatuslineLoop(config_expanded)
    result_expanded = loop_expanded.process(transcript)
    print(f"扩展布局: {result_expanded}")

    # 紧凑布局
    config_compact = Config(layout_mode=LayoutMode.COMPACT)
    loop_compact = StatuslineLoop(config_compact)
    result_compact = loop_compact.process(transcript)
    print(f"紧凑布局: {result_compact}")
    print()


if __name__ == "__main__":
    example_basic()
    example_custom_config()
    example_multi_turn()
    example_layout_comparison()
