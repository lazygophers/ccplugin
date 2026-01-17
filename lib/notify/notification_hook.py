#!/usr/bin/env python3
"""
Notification Hook 处理脚本
根据通知类型和配置文件决定是否发送系统通知
"""

import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# 添加项目根目录到 sys.path
script_path = Path(__file__).resolve().parent
project_root = script_path.parent.parent

if not (project_root / 'lib').exists():
    current = script_path
    for _ in range(5):
        if (current / 'lib').exists():
            project_root = current
            break
        current = current.parent

sys.path.insert(0, str(project_root))

try:
    from lib.notify.init_config import get_effective_config
    from lib.notify import notify, speak
except ImportError as e:
    sys.exit(1)


def get_hook_input() -> Optional[Dict[str, Any]]:
    """从stdin读取hook输入"""
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return None


def should_notify_type(notification_type: str, config: Optional[Dict]) -> tuple[bool, bool]:
    """
    判断是否需要为该通知类型发送通知

    Args:
        notification_type: 通知类型（如 permission_prompt、idle_prompt等）
        config: 配置字典

    Returns:
        (should_notify, should_voice): 是否通知、是否语音
    """
    if config is None:
        return False, False

    try:
        events = config.get('events', {})
        notification = events.get('Notification', {})
        types = notification.get('types', {})
        type_config = types.get(notification_type, {})

        notify = type_config.get('notify', False)
        voice = type_config.get('voice', False) if notify else False

        return notify, voice
    except Exception:
        return False, False


def send_notification(message: str) -> bool:
    """
    发送系统通知

    Args:
        message: 通知消息

    Returns:
        bool: 是否成功
    """
    try:
        title = "Claude Code"
        timeout = 5000

        return notify(title, message, timeout)
    except Exception:
        return False


def main() -> int:
    """
    主函数

    Returns:
        int: 返回码（0 为成功）
    """
    try:
        # 读取hook输入
        hook_input = get_hook_input()
        if hook_input is None:
            return 0

        # 获取通知类型和消息
        notification_type = hook_input.get('notification_type', '')
        message = hook_input.get('message', '')

        if not notification_type or not message:
            return 0

        # 读取配置
        config = get_effective_config()

        # 判断是否需要通知
        should_notify, should_voice = should_notify_type(notification_type, config)

        if should_notify:
            send_notification(message)

            # 如果需要语音播报，则播报
            if should_voice:
                speak(message)

        # 返回成功
        return 0
    except Exception:
        # 错误时也返回 0，不中断主程序
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code if exit_code in (0, 1) else 0)
