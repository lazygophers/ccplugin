#!/usr/bin/env python3
"""
Stop Hook - 在会话结束时发送通知
包含会话统计信息：时间戳、交互次数等
"""

import sys
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# 导入通知器
try:
    from notifier import notify
except ImportError:
    # 如果导入失败，定义一个虚拟的 notify 函数
    def notify(title: str, message: str, timeout: int = 5000) -> bool:
        print(f"[{title}] {message}")
        return True


def count_interactions(transcript_path: str) -> int:
    """
    统计会话中的交互次数
    
    Args:
        transcript_path: 转录文件路径
        
    Returns:
        交互次数
    """
    try:
        transcript_path = Path(transcript_path).expanduser()
        if not transcript_path.exists():
            return 0

        count = 0
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    # 计算对话轮次
                    if data.get("type") in ["user_message", "assistant_message"]:
                        count += 1
                except json.JSONDecodeError:
                    pass
        
        return count // 2  # 用户和助手各一条为一轮
    except (IOError, ValueError):
        return 0


def validate_hook_input(data: Dict[str, Any]) -> tuple[bool, str]:
    """
    验证 Hook 输入数据的完整性
    
    Args:
        data: Hook 输入的 JSON 数据
        
    Returns:
        (是否有效, 错误信息) 元组
    """
    # 检查必填字段
    required_fields = ["session_id", "hook_event_name"]
    for field in required_fields:
        if field not in data:
            return False, f"缺少必填字段: {field}"
    
    # 检查事件名称
    if data.get("hook_event_name") != "Stop":
        return False, f"错误的事件类型: {data.get('hook_event_name')}，期望: Stop"
    
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
        "session_id": data.get("session_id", "unknown"),
        "transcript_path": data.get("transcript_path", ""),
        "permission_mode": data.get("permission_mode", "default"),
        "hook_event_name": data.get("hook_event_name", "Stop"),
        "stop_hook_active": data.get("stop_hook_active", False),
        "timestamp": datetime.now().strftime("%H:%M:%S"),
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
        
        # 统计交互次数
        interaction_count = count_interactions(parsed["transcript_path"])
        
        # 生成通知消息
        title = "Claude Code 会话已结束"
        message = f"[{parsed['timestamp']}] 本次会话共有 {interaction_count} 轮交互"
        
        # 发送通知
        notify(title, message, timeout=5000)
        
    except Exception as e:
        # 静默处理错误，不中断主程序
        pass


if __name__ == "__main__":
    main()
