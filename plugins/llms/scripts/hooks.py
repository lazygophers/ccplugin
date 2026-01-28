"""
LLMS.txt Plugin - Hooks Handler

处理 llms.txt 相关的 hook 事件
"""

import json
import sys
from pathlib import Path

from lib import logging
from lib.hooks import load_hooks

logger = logging.get_logger(__name__)


def handle_hook() -> None:
    """处理 hook 模式：从 stdin 读取 JSON 并分发到对应处理器"""
    try:
        hook_data = load_hooks()
        event_name = hook_data.get("hook_event_name")

        logging.info(f"接收到事件: {event_name}")

    except json.JSONDecodeError as e:
        logging.error(f"JSON 解析失败: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Hook 处理失败: {e}")
        sys.exit(1)
