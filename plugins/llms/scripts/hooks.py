"""
llms.txt Plugin - Hooks Handler

处理 llms.txt 相关的 hook 事件
"""

import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import lib.logging as logging  # noqa: E402
from lib.hooks import load_hooks  # noqa: E402


def handle_hook() -> None:
    """处理 hook 模式：从 stdin 读取 JSON 并分发到对应处理器"""
    hook_data = load_hooks()
    event_name = hook_data.get("hook_event_name")

    logging.info(f"接收到事件: {event_name}")
