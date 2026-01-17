#!/usr/bin/env python3
"""
PreToolUse Hook 处理脚本
在工具使用前根据配置文件决定是否发送通知
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


def should_notify_tool(tool_name: str, config: Optional[Dict]) -> tuple[bool, bool]:
    """
    判断是否需要为该工具发送通知

    Args:
        tool_name: 工具名称
        config: 配置字典

    Returns:
        (should_notify, should_voice): 是否通知、是否语音
    """
    if config is None:
        return False, False

    try:
        events = config.get('events', {})
        pretooluse = events.get('PreToolUse', {})
        tools = pretooluse.get('tools', {})
        tool_config = tools.get(tool_name, {})

        notify = tool_config.get('notify', False)
        voice = tool_config.get('voice', False) if notify else False

        return notify, voice
    except Exception:
        return False, False


def send_notification(tool_name: str, hook_input: Dict) -> bool:
    """
    发送工具使用前的通知

    Args:
        tool_name: 工具名称
        hook_input: hook输入的JSON数据

    Returns:
        bool: 是否成功
    """
    try:
        message = f"准备使用工具: {tool_name}"
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

        # 获取工具名称
        tool_name = hook_input.get('tool_name', '')
        if not tool_name:
            return 0

        # 读取配置
        config = get_effective_config()

        # 判断是否需要通知
        should_notify, should_voice = should_notify_tool(tool_name, config)

        if should_notify:
            send_notification(tool_name, hook_input)

            # 如果需要语音播报，则播报
            if should_voice:
                voice_message = f"工具 {tool_name} 准备执行"
                speak(voice_message)

        # 返回成功
        return 0
    except Exception:
        # 错误时也返回 0，不中断主程序
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code if exit_code in (0, 1) else 0)
