"""
Claude Code Hooks 事件处理模块

处理来自 Claude Code 的各种 Hook 事件，根据配置触发 TTS 和系统通知功能。
支持的事件：SessionStart、SessionEnd、UserPromptSubmit、PreToolUse、PostToolUse、Notification、PreCompact
"""

import json
import sys
from typing import Optional, Dict, Any

from lib.logging import info, error, debug, enable_debug
from config import load_config, HooksConfig, HookConfig
from notify import play_text_tts, show_system_notification


def get_hook_config(config: HooksConfig, event_name: str, context: Optional[Dict[str, Any]] = None) -> Optional[HookConfig]:
    """根据事件名称获取相应的 Hook 配置

    Args:
        config: HooksConfig 实例
        event_name: Hook 事件名称
        context: 事件上下文（用于获取特定的配置，如工具名称）

    Returns:
        HookConfig 配置对象或 None
    """
    if event_name == "SessionStart":
        source = context.get("source", "startup") if context else "startup"
        hook_config = config.session_start
        return getattr(hook_config, source, None)

    elif event_name == "SessionEnd":
        reason = context.get("reason", "other") if context else "other"
        hook_config = config.session_end
        return getattr(hook_config, reason, None)

    elif event_name == "UserPromptSubmit":
        return config.user_prompt_submit

    elif event_name == "PreToolUse":
        tool_name = context.get("tool_name", "").lower() if context else ""
        hook_config = config.pre_tool_use
        return getattr(hook_config, tool_name, None)

    elif event_name == "PostToolUse":
        tool_name = context.get("tool_name", "").lower() if context else ""
        hook_config = config.post_tool_use
        return getattr(hook_config, tool_name, None)

    elif event_name == "Notification":
        notification_type = context.get("notification_type", "") if context else ""
        hook_config = config.notification
        return getattr(hook_config, notification_type, None)

    elif event_name == "Stop":
        return config.stop

    elif event_name == "SubagentStop":
        return config.subagent_stop

    elif event_name == "PreCompact":
        trigger = context.get("trigger", "manual") if context else "manual"
        hook_config = config.pre_compact
        return getattr(hook_config, trigger, None)

    return None


def extract_context_from_hook_data(hook_data: Dict[str, Any]) -> Dict[str, Any]:
    """从 Hook 数据中提取上下文信息

    Args:
        hook_data: 来自 Claude Code 的 Hook 事件数据

    Returns:
        提取的上下文字典
    """
    context = {}

    # 提取工具名称
    if "tool_name" in hook_data:
        context["tool_name"] = hook_data["tool_name"]

    # 提取通知类型
    if "notification_type" in hook_data:
        context["notification_type"] = hook_data["notification_type"]

    # 提取会话启动源
    if "source" in hook_data:
        context["source"] = hook_data["source"]

    # 提取会话结束原因
    if "reason" in hook_data:
        context["reason"] = hook_data["reason"]

    # 提取压缩触发类型
    if "trigger" in hook_data:
        context["trigger"] = hook_data["trigger"]

    # 提取消息和标题（用于通知）
    if "message" in hook_data:
        context["message"] = hook_data["message"]

    if "title" in hook_data:
        context["title"] = hook_data["title"]

    return context


def execute_hook_actions(hook_config: Optional[HookConfig], event_name: str, context: Optional[Dict[str, Any]] = None) -> bool:
    """执行 Hook 配置中指定的动作

    Args:
        hook_config: HookConfig 配置对象或 None
        event_name: Hook 事件名称
        context: 事件上下文

    Returns:
        是否成功执行
    """
    if not hook_config or not hook_config.enabled:
        debug(f"Hook {event_name} 未启用")
        return True

    success = True

    # 播放声音（TTS）
    if hook_config.play_sound:
        message = hook_config.message or f"{event_name} 事件已触发"
        info(f"播放 TTS: {message}")
        if not play_text_tts(message):
            error(f"TTS 播放失败: {message}")
            success = False

    return success


def handle_hook() -> None:
    """处理 Hook 事件：从 stdin 读取 JSON 数据并执行相应的 Hook 动作

    Hook 数据格式示例：
    {
        "hook_event_name": "SessionStart",
        "source": "startup",
        "message": "Session started"
    }
    """
    try:
        # 尝试从 stdin 读取 Hook 数据
        hook_data = json.load(sys.stdin)

        if not isinstance(hook_data, dict):
            raise ValueError("Hook 数据必须是 JSON 对象")

        event_name = hook_data.get("hook_event_name", "").strip()

        if not event_name:
            raise ValueError("缺少必需的 hook_event_name 字段")

        info(f"处理 Hook 事件: {event_name}")
        debug(f"Hook 数据: {json.dumps(hook_data)}")

        # 加载配置
        config = load_config()

        # 提取上下文信息
        context = extract_context_from_hook_data(hook_data)

        # 获取相应的 Hook 配置
        hook_config = get_hook_config(config, event_name, context)

        if hook_config is None:
            debug(f"未找到 {event_name} 的 Hook 配置")
            return

        # 执行 Hook 动作
        if not execute_hook_actions(hook_config, event_name, context):
            error(f"Hook {event_name} 执行失败")
            sys.exit(1)

        info(f"Hook 事件 {event_name} 处理完成")

    except json.JSONDecodeError as e:
        error(f"JSON 解析失败: {e}")
        sys.exit(1)
    except ValueError as e:
        error(f"Hook 数据验证失败: {e}")
        sys.exit(1)
    except Exception as e:
        error(f"Hook 处理失败: {e}")
        import traceback
        debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    handle_hook()