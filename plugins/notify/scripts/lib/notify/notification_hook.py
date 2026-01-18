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
    from lib.logging import get_logger
except ImportError as e:
    sys.exit(1)

# 初始化日志（hook 脚本仅输出到文件）
logger = get_logger("notification-hook", enable_console=False)


def get_hook_input() -> Optional[Dict[str, Any]]:
    """从stdin读取hook输入"""
    try:
        data = json.load(sys.stdin)
        logger.debug(f"读取 hook 输入: session_id={data.get('session_id')}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"无法解析 JSON 输入: {e}")
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
        logger.debug(f"配置为空，通知类型 {notification_type} 将被忽略")
        return False, False

    try:
        # 先检查全局notify设置是否禁用了所有通知
        global_notify = config.get('notify', True)
        if not global_notify:
            # 全局禁用了通知
            logger.info(f"全局禁用了通知，跳过通知类型: {notification_type}")
            return False, False

        events = config.get('events', {})
        notification = events.get('Notification', {})
        types = notification.get('types', {})
        type_config = types.get(notification_type, {})

        # 如果该通知类型有具体配置，使用它；否则保持为False（类型级默认不通知）
        notify = type_config.get('notify', False)
        voice = type_config.get('voice', False) if notify else False

        logger.debug(f"通知类型 {notification_type}: 通知={notify}, 语音={voice}")
        return notify, voice
    except Exception as e:
        logger.error(f"判断通知类型 {notification_type} 时出错: {e}")
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
        logger.info("Notification hook 启动")

        # 读取hook输入
        hook_input = get_hook_input()
        if hook_input is None:
            logger.error("无法读取 hook 输入")
            return 0

        # 验证hook事件名称
        if hook_input.get('hook_event_name') != 'Notification':
            logger.debug(f"Hook 事件类型不是 Notification: {hook_input.get('hook_event_name')}")
            return 0

        # 提取常见字段（所有hook都应该有）
        session_id = hook_input.get('session_id', '')
        notification_type = hook_input.get('notification_type', '')
        message = hook_input.get('message', '')

        logger.info(f"处理通知: type={notification_type}, session={session_id[:8]}")

        if not notification_type or not message:
            logger.warning("通知类型或消息为空，忽略")
            return 0

        # 读取配置
        config = get_effective_config()

        # 判断是否需要通知
        should_notify, should_voice = should_notify_type(notification_type, config)

        if should_notify:
            logger.info(f"发送通知: {notification_type}")
            send_notification(message)

            # 如果需要语音播报，则播报
            if should_voice:
                logger.info(f"播报通知: {notification_type}")
                speak(message)
        else:
            logger.debug(f"通知被配置禁用: {notification_type}")

        logger.info("Notification hook 处理完成")
        # 返回成功
        return 0
    except Exception as e:
        logger.error(f"Notification hook 处理失败: {e}")
        # 错误时也返回 0，不中断主程序
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code if exit_code in (0, 1) else 0)
