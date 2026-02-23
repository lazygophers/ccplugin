"""
Claude Code Hooks 事件处理模块

处理来自 Claude Code 的各种 Hook 事件，根据配置触发 TTS 和系统通知功能。
支持的事件：SessionStart、SessionEnd、UserPromptSubmit、PreToolUse、PostToolUse、Notification、PreCompact
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any
import copy
from config import load_config, HooksConfig, HookConfig
from lib.hooks import load_hooks
from lib.logging import info, error, debug
from lib.utils.env import get_project_dir, get_plugins_path
from notify import play_text_tts, show_system_notification


def get_hook_config(config: HooksConfig, event_name: str, context: Optional[Dict[str, Any]] = None) -> Optional[
	HookConfig]:
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

	支持的字段：
	  - tool_name: 工具名称
	  - notification_type: 通知类型
	  - source: 会话启动源（startup/editor/cli 等）
	  - reason: 会话结束原因
	  - trigger: 压缩触发类型
	  - message: 消息内容
	  - title: 消息标题
	  - project_name: 项目名（从 hook_data 或自动获取项目路径的名称）
	  - session_id: 会话 ID
	  - file_path: 文件完整路径
	  - file_name: 文件名
	  - status: 状态（success/error/warning/pending 等）
	  - error_message: 错误消息
	  - duration: 耗时（毫秒）
	  - timestamp: 时间戳
	  - time_now: 当前时间的可读格式（自动生成）
	  - user_name: 用户名称
	  - environment: 环境信息（dev/test/prod 等）
	  - tags: 标签（逗号分隔）
	  - priority: 优先级（low/medium/high/critical）
	  - plugin_name: 插件名称
	  - result: 操作结果摘要

	Args:
		hook_data: 来自 Claude Code 的 Hook 事件数据

	Returns:
		提取的上下文字典
	"""
	context = copy.deepcopy(hook_data)

	if "tool_input" in hook_data:
		if "file_path" in hook_data["tool_input"]:
			context["file_path"] = hook_data["tool_input"]["file_path"]
			context["file_name"] = os.path.basename(hook_data["tool_input"]["file_path"])

	context["time_now"] = datetime.now().strftime("%Y年%m月%d日 %H点%M分")
	context["timestamp"] = datetime.now().timestamp()

	context["plugin_name"] = os.path.basename(get_plugins_path())
	context["project_name"] = os.path.basename(get_project_dir())

	if "hook_event_name" in hook_data:
		context["hook_event_name"] = hook_data["hook_event_name"]

	if "tool_name" in hook_data:
		context["tool_name"] = hook_data["tool_name"]

	if "session_id" in hook_data:
		context["session_id"] = hook_data["session_id"]

	if "tool_response" in hook_data:
		if "success" in hook_data["tool_response"]:
			if hook_data["tool_response"]["success"]:
				context["success"] = "成功"
			else:
				context["success"] = "失败"

	if "notification_type" in hook_data:
		context["notification_type"] = hook_data["notification_type"]

	if "message" in hook_data:
		context["message"] = hook_data["message"]

	if "agent_type" in hook_data:
		context["agent_type"] = hook_data["agent_type"]

	return context


def execute_hook_actions(hook_config: Optional[HookConfig], event_name: str,
                         context: Optional[Dict[str, Any]] = None) -> bool:
	"""执行 Hook 配置中指定的动作

	Args:
		hook_config: HookConfig 配置对象或 None
		event_name: Hook 事件名称
		context: 事件上下文，用于参数替换

	Returns:
		是否成功执行
	"""
	if not hook_config or not hook_config.enabled:
		debug(f"Hook {event_name} 未启用")
		return True

	success = True

	message = hook_config.message or f"{event_name} 事件已触发"

	logging.info(f'context:{context}')

	# 如果 context 存在，使用其中的参数替换消息中的占位符
	if context:
		try:
			message = message.format(**context)
		except (KeyError, ValueError) as e:
			debug(f"消息参数替换失败: {e}，使用原始消息")

	# 显示消息
	if hook_config.enabled:
		info(f"弹出提示：{message}")
		if show_system_notification(message):
			# 播放声音（TTS）
			if hook_config.play_sound:
				info(f"播放 TTS: {message}")
				if not play_text_tts(message):
					error(f"TTS 播放失败: {message}")
					success = False
		else:
			error(f"系统通知显示失败: {message}")
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
	hook_data = load_hooks()

	if not isinstance(hook_data, dict):
		raise ValueError("Hook 数据必须是 JSON 对象")

	event_name = hook_data.get("hook_event_name", "").strip()

	if not event_name:
		raise ValueError("缺少必需的 hook_event_name 字段")

	info(f"处理 Hook 事件: {event_name}")
	debug(f"Hook 数据: {json.dumps(hook_data)}")

	config = load_config()

	context = extract_context_from_hook_data(hook_data)

	hook_config = get_hook_config(config, event_name, context)

	if hook_config is None:
		debug(f"未找到 {event_name} 的 Hook 配置")
		return

	if not execute_hook_actions(hook_config, event_name, context):
		error(f"Hook {event_name} 执行失败")
		sys.exit(1)

	info(f"Hook 事件 {event_name} 处理完成")

	print(json.dumps({
		"continue": True,
	}))