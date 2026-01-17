#!/usr/bin/env python3
"""
PreCompact Hook 处理脚本
在会话压缩前根据配置文件决定是否发送通知
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


def should_notify_precompact(config: Optional[Dict]) -> tuple[bool, bool]:
    """
    判断是否需要发送 PreCompact 通知

    Args:
        config: 配置字典

    Returns:
        (should_notify, should_voice): 是否通知、是否语音
    """
    if config is None:
        return False, False

    try:
        events = config.get('events', {})
        precompact = events.get('PreCompact', {})

        notify_enabled = precompact.get('notify', False)
        voice = precompact.get('voice', False) if notify_enabled else False

        return notify_enabled, voice
    except Exception:
        return False, False


def send_notification(hook_input: Dict) -> bool:
    """
    发送 PreCompact 事件通知

    Args:
        hook_input: hook输入的JSON数据

    Returns:
        bool: 是否成功
    """
    try:
        # 提取触发方式和自定义指令
        trigger = hook_input.get('trigger', 'auto')  # manual 或 auto
        custom_instructions = hook_input.get('custom_instructions', '')

        trigger_text = "手动压缩" if trigger == 'manual' else "自动压缩"
        message = f"会话将要 {trigger_text}"

        if custom_instructions:
            display_instructions = custom_instructions[:50] + "..." if len(custom_instructions) > 50 else custom_instructions
            message += f"（自定义指令: {display_instructions}）"

        title = "Claude Code"
        timeout = 3000

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

        # 验证hook事件名称
        if hook_input.get('hook_event_name') != 'PreCompact':
            return 0

        # 提取常见字段（所有hook都应该有）
        session_id = hook_input.get('session_id', '')
        transcript_path = hook_input.get('transcript_path', '')
        cwd = hook_input.get('cwd', '')
        permission_mode = hook_input.get('permission_mode', 'default')

        # 提取事件特定字段
        # - trigger: 触发方式（manual/auto）
        # - custom_instructions: 用户自定义指令
        trigger = hook_input.get('trigger', 'auto')
        custom_instructions = hook_input.get('custom_instructions', '')

        # 读取配置
        config = get_effective_config()

        # 判断是否需要通知
        should_notify, should_voice = should_notify_precompact(config)

        if should_notify:
            send_notification(hook_input)

            # 如果需要语音播报，则播报
            if should_voice:
                trigger_text = "手动压缩" if trigger == 'manual' else "自动压缩"
                voice_message = f"会话将要{trigger_text}"
                speak(voice_message)

        # 返回成功
        return 0
    except Exception:
        # 错误时也返回 0，不中断主程序
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code if exit_code in (0, 1) else 0)
