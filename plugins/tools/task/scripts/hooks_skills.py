"""
Claude Code Hooks 事件处理模块

处理来自 Claude Code 的各种 Hook 事件，根据配置触发 TTS 和系统通知功能。
支持的事件：SessionStart、SessionEnd、UserPromptSubmit、PreToolUse、PostToolUse、Notification、PreCompact
"""
import json
import os.path
import sys
import traceback

from lib import logging
from lib.utils.env import get_project_dir
from lib.utils.gitignore import add_gitignore_rule
from lib.hooks import load_hooks

def handle_session_start(session_id: str):
	with open(os.path.join(get_project_dir(), ".claude", "tasks", "index.json")) as file:
		tasks = json.load(file)
		if session_id not in tasks:
			print(json.dumps({
				"hookSpecificOutput": {
					"hookEventName": "SessionStart",
					"additionalContext": f".claude/tasks/index.json 缺少 {session_id} 的信息"
				}
			}))

def handle_hook_skills() -> None:
	"""处理 Hook 事件：从 stdin 读取 JSON 数据并执行相应的 Hook 动作

	Hook 数据格式示例：
	{
		"hook_event_name": "SessionStart",
		"source": "startup",
		"message": "Session started"
	}
	"""
	try:
		input_data = load_hooks()
		logging.info(f"Received input data: {input_data}")

		hook_event_name = input_data.get("hook_event_name", "")
		if not hook_event_name:
			logging.error("缺少 hook_event_name")
			return

		session_id = input_data.get("session_id", "")
		if not session_id:
			logging.error("缺少 session_id")
			return

		# 路由到不同的处理器
		if hook_event_name == "SessionStart":
			handle_session_start(session_id)
	except Exception as e:
		logging.error(f"未捕获的异常: {e}\n{traceback.format_exc()}")
		sys.exit(0)
