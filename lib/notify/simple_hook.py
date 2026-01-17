#!/usr/bin/env python3
"""
简单事件 Hook 处理脚本
处理 SessionEnd、UserPromptSubmit、SubagentStop 等简单事件的通知
"""

import json
import sys
from datetime import datetime
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


# 事件类型配置映射
EVENT_TYPE_MAPPING = {
    "SessionEnd": {
        "title": "会话结束",
        "message_template": "Claude Code 会话已结束",
    },
    "UserPromptSubmit": {
        "title": "用户提示",
        "message_template": "用户提示已提交",
    },
    "SubagentStop": {
        "title": "子代理停止",
        "message_template": "子代理已停止",
    },
}


def get_hook_input() -> Optional[Dict[str, Any]]:
    """从stdin读取hook输入"""
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return None


def should_notify_event(event_type: str, config: Optional[Dict]) -> tuple[bool, bool]:
    """
    判断是否需要为该事件发送通知

    Args:
        event_type: 事件类型
        config: 配置字典

    Returns:
        (should_notify, should_voice): 是否通知、是否语音
    """
    if config is None:
        return False, False

    try:
        events = config.get('events', {})
        event_config = events.get(event_type, {})

        notify_flag = event_config.get('notify', False)
        voice = event_config.get('voice', False) if notify_flag else False

        return notify_flag, voice
    except Exception:
        return False, False


def get_message_for_event(event_type: str, hook_input: Dict) -> str:
    """
    根据事件类型获取通知消息

    Args:
        event_type: 事件类型
        hook_input: hook输入的JSON数据

    Returns:
        str: 通知消息
    """
    event_info = EVENT_TYPE_MAPPING.get(event_type, {})
    message = event_info.get("message_template", f"{event_type} 事件已触发")

    # 针对不同事件类型添加额外信息
    if event_type == "SessionEnd":
        reason = hook_input.get("reason", "unknown")
        timestamp = datetime.now().strftime("%H:%M:%S")
        message = f"[{timestamp}] Claude Code 会话已结束（原因: {reason}）"
    elif event_type == "UserPromptSubmit":
        prompt = hook_input.get("prompt", "")
        if prompt:
            # 限制显示长度
            display_prompt = prompt[:30] + "..." if len(prompt) > 30 else prompt
            message = f"用户提示已提交：{display_prompt}"

    return message


def send_notification(event_type: str, hook_input: Dict) -> bool:
    """
    发送通知

    Args:
        event_type: 事件类型
        hook_input: hook输入的JSON数据

    Returns:
        bool: 是否成功
    """
    try:
        event_info = EVENT_TYPE_MAPPING.get(event_type, {})
        title = event_info.get("title", "Claude Code")
        message = get_message_for_event(event_type, hook_input)
        timeout = 3000

        return notify(title, message, timeout)
    except Exception:
        return False


def main(event_type: str) -> int:
    """
    主函数

    Args:
        event_type: 事件类型

    Returns:
        int: 返回码（0 为成功）
    """
    try:
        # 读取hook输入
        hook_input = get_hook_input()
        if hook_input is None:
            return 0

        # 验证事件类型
        if hook_input.get("hook_event_name") != event_type:
            return 0

        # 读取配置
        config = get_effective_config()

        # 判断是否需要通知
        should_notify, should_voice = should_notify_event(event_type, config)

        if should_notify:
            send_notification(event_type, hook_input)

            # 如果需要语音播报，则播报
            if should_voice:
                message = get_message_for_event(event_type, hook_input)
                speak(message)

        # 返回成功
        return 0
    except Exception:
        # 错误时也返回 0，不中断主程序
        return 0


if __name__ == "__main__":
    sys.exit(0)
