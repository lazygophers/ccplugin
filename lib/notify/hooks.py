"""
Hook 事件处理
处理 Stop 和 Notification hooks
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from .notifier import notify


# 通知类型映射
NOTIFICATION_TYPE_MAPPING = {
    "permission_prompt": {
        "title": "权限请求",
        "icon": "⚠️",
        "timeout": 8000,
    },
    "warning": {
        "title": "警告",
        "icon": "⚡",
        "timeout": 6000,
    },
    "info": {
        "title": "提示",
        "icon": "ℹ️",
        "timeout": 4000,
    },
    "error": {
        "title": "错误",
        "icon": "❌",
        "timeout": 6000,
    },
}


def count_interactions(transcript_path: str) -> int:
    """
    统计会话中的交互次数

    Args:
        transcript_path: 转录文件路径（来自hook输入的对话JSON路径）

    Returns:
        交互次数，如果路径无效或文件无法读取返回 -1（表示无法统计）
    """
    try:
        # 检查路径有效性
        if not transcript_path or not transcript_path.strip():
            # 路径为空或仅为空格，表示无法统计
            return -1

        transcript_path = Path(transcript_path).expanduser()

        # 检查路径是否存在且是文件（不是目录）
        if not transcript_path.exists() or not transcript_path.is_file():
            # 路径不存在或不是文件
            return -1

        count = 0
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    # 计算对话轮次：user_message 和 assistant_message
                    if data.get("type") in ["user_message", "assistant_message"]:
                        count += 1
                except json.JSONDecodeError:
                    # 跳过格式错误的行
                    pass

        # 用户和助手各一条消息为一轮
        return count // 2 if count > 0 else 0
    except (IOError, ValueError, OSError):
        # 文件读取错误或其他IO异常，返回 -1 表示无法统计
        return -1


def format_notification_message(
    notification_type: str,
    original_message: str,
) -> tuple[str, str]:
    """
    格式化通知消息

    Args:
        notification_type: 通知类型
        original_message: 原始消息内容

    Returns:
        (标题, 消息内容) 元组
    """
    type_config = NOTIFICATION_TYPE_MAPPING.get(
        notification_type,
        {"title": "通知", "icon": "📢", "timeout": 4000},
    )

    title = f"{type_config['icon']} {type_config['title']}"

    # 对长消息进行截断
    max_length = 100
    if len(original_message) > max_length:
        message = original_message[:max_length] + "..."
    else:
        message = original_message

    return title, message


def validate_hook_input(data: Dict[str, Any], hook_type: str) -> tuple[bool, str]:
    """
    验证 Hook 输入数据的完整性

    Args:
        data: Hook 输入的 JSON 数据
        hook_type: Hook 类型 (stop 或 notification)

    Returns:
        (是否有效, 错误信息) 元组
    """
    required_fields = ["session_id", "hook_event_name"]
    for field in required_fields:
        if field not in data:
            return False, f"缺少必填字段: {field}"

    if hook_type == "stop":
        if data.get("hook_event_name") != "Stop":
            return False, f"错误的事件类型: {data.get('hook_event_name')}，期望: Stop"
    elif hook_type == "notification":
        if data.get("hook_event_name") != "Notification":
            return False, f"错误的事件类型: {data.get('hook_event_name')}，期望: Notification"

        # Notification hook 特有的检查
        if not data.get("message", "").strip():
            return False, "消息内容不能为空"

        valid_types = ["permission_prompt", "warning", "info", "error"]
        notification_type = data.get("notification_type", "info")
        if notification_type not in valid_types:
            return False, f"无效的通知类型: {notification_type}，有效值: {valid_types}"

    return True, ""


def parse_stop_hook_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    解析 Stop Hook 输入数据

    官方规范中 Stop Hook 的字段：
    常见字段（所有hook都有）:
    - session_id: 会话ID
    - transcript_path: 对话JSON路径
    - permission_mode: 权限模式（"default"、"plan"、"acceptEdits"等）
    - hook_event_name: 事件名称（"Stop"）

    Stop Hook特有字段:
    - stop_hook_active: 是否已通过stop hook继续执行（true表示需要检查避免无限循环）
    """
    return {
        "session_id": data.get("session_id", ""),
        "transcript_path": data.get("transcript_path", ""),
        "permission_mode": data.get("permission_mode", "default"),
        "hook_event_name": data.get("hook_event_name", "Stop"),
        "stop_hook_active": data.get("stop_hook_active", False),
        "timestamp": datetime.now().strftime("%H:%M:%S"),
    }


def parse_notification_hook_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    解析 Notification Hook 输入数据

    官方规范中 Notification Hook 的字段：
    常见字段（所有hook都有）:
    - session_id: 会话ID
    - transcript_path: 对话JSON路径
    - cwd: 当前工作目录
    - permission_mode: 权限模式（"default"、"plan"、"acceptEdits"等）
    - hook_event_name: 事件名称（"Notification"）

    Notification Hook特有字段:
    - message: 通知消息内容
    - notification_type: 通知类型（permission_prompt、idle_prompt、auth_success、elicitation_dialog等）
    """
    return {
        "session_id": data.get("session_id", ""),
        "transcript_path": data.get("transcript_path", ""),
        "cwd": data.get("cwd", ""),
        "permission_mode": data.get("permission_mode", "default"),
        "message": data.get("message", ""),
        "notification_type": data.get("notification_type", "info"),
        "hook_event_name": data.get("hook_event_name", "Notification"),
    }


def handle_stop_hook() -> int:
    """
    处理 Stop Hook

    根据官方规范，Stop Hook 输入包含：
    - session_id: 会话ID
    - transcript_path: 对话JSON文件路径（可能为空）
    - permission_mode: 权限模式
    - stop_hook_active: 是否已通过hook继续执行
    """
    try:
        hook_input = sys.stdin.read()
        if not hook_input.strip():
            return 0

        try:
            data = json.loads(hook_input)
        except json.JSONDecodeError:
            return 1

        # 验证输入数据
        is_valid, _ = validate_hook_input(data, "stop")
        if not is_valid:
            return 1

        # 解析输入
        parsed = parse_stop_hook_input(data)

        # 生成通知消息
        title = "Claude Code 会话已结束"

        # 尝试统计交互次数
        # transcript_path 是对话JSON文件的路径，可能为空
        interaction_count = count_interactions(parsed["transcript_path"])

        if interaction_count >= 0:
            # 成功统计交互次数
            message = f"[{parsed['timestamp']}] 本次会话共有 {interaction_count} 轮交互"
        else:
            # 无法统计交互次数（transcript_path无效或文件不存在）
            # 此时只显示结束时间和session_id用于参考
            message = f"[{parsed['timestamp']}] 会话已结束 (ID: {parsed['session_id'][:8]})"

        # 发送通知
        notify(title, message, timeout=5000)

        return 0
    except Exception:
        # 异常时不中断主程序
        return 0


def handle_notification_hook() -> int:
    """处理 Notification Hook"""
    try:
        hook_input = sys.stdin.read()
        if not hook_input.strip():
            return 0

        try:
            data = json.loads(hook_input)
        except json.JSONDecodeError:
            return 1

        # 验证输入数据
        is_valid, _ = validate_hook_input(data, "notification")
        if not is_valid:
            return 1

        # 解析输入
        parsed = parse_notification_hook_input(data)

        # 格式化通知
        title, message = format_notification_message(
            parsed["notification_type"],
            parsed["message"],
        )

        # 获取超时时间
        timeout = NOTIFICATION_TYPE_MAPPING.get(
            parsed["notification_type"],
            {},
        ).get("timeout", 4000)

        # 发送通知
        notify(title, message, timeout=timeout)

        return 0
    except Exception:
        return 0
