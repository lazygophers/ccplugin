#!/usr/bin/env python3
"""
Notification Hook - 处理各类事件通知
在权限请求、用户输入等重要事件时发送系统通知
"""

import sys
import json
from typing import Any, Dict, Optional

# 导入通知器
try:
    from notifier import notify
except ImportError:
    # 如果导入失败，定义一个虚拟的 notify 函数
    def notify(title: str, message: str, timeout: int = 5000) -> bool:
        print(f"[{title}] {message}")
        return True


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


def validate_hook_input(data: Dict[str, Any]) -> tuple[bool, str]:
    """
    验证 Hook 输入数据的完整性
    
    Args:
        data: Hook 输入的 JSON 数据
        
    Returns:
        (是否有效, 错误信息) 元组
    """
    # 检查必填字段
    required_fields = ["session_id", "message", "hook_event_name"]
    for field in required_fields:
        if field not in data:
            return False, f"缺少必填字段: {field}"
    
    # 检查事件名称
    if data.get("hook_event_name") != "Notification":
        return False, f"错误的事件类型: {data.get('hook_event_name')}，期望: Notification"
    
    # 检查消息不为空
    if not data.get("message", "").strip():
        return False, "消息内容不能为空"
    
    # 检查通知类型是否有效
    valid_types = ["permission_prompt", "warning", "info", "error"]
    notification_type = data.get("notification_type", "info")
    if notification_type not in valid_types:
        return False, f"无效的通知类型: {notification_type}，有效值: {valid_types}"
    
    return True, ""


def parse_hook_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    解析 Hook 输入数据
    
    Args:
        data: Hook 输入的 JSON 数据
        
    Returns:
        解析后的数据字典
    """
    return {
        "session_id": data.get("session_id", ""),
        "message": data.get("message", ""),
        "notification_type": data.get("notification_type", "info"),
        "cwd": data.get("cwd", ""),
        "permission_mode": data.get("permission_mode", "default"),
        "hook_event_name": data.get("hook_event_name", "Notification"),
        "stop_hook_active": data.get("stop_hook_active", False),
    }


def main():
    """主函数"""
    try:
        # 从标准输入读取 Hook 数据
        hook_input = sys.stdin.read()
        if not hook_input.strip():
            sys.exit(0)

        try:
            data = json.loads(hook_input)
        except json.JSONDecodeError as e:
            # JSON 格式错误
            sys.exit(1)

        # 验证输入数据
        is_valid, error_msg = validate_hook_input(data)
        if not is_valid:
            sys.exit(1)

        # 解析输入
        parsed = parse_hook_input(data)
        
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
        
    except Exception as e:
        # 静默处理错误，不中断主程序
        pass


if __name__ == "__main__":
    main()
