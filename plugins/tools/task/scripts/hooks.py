"""
Claude Code Hooks 事件处理模块

处理来自 Claude Code 的各种 Hook 事件，根据配置触发 TTS 和系统通知功能。
支持的事件：SessionStart、SessionEnd、UserPromptSubmit、PreToolUse、PostToolUse、Notification、PreCompact
"""
import os.path
import sys
import traceback

from lib import logging
from lib.utils.env import get_project_dir
from lib.utils.gitignore import add_gitignore_rule
from lib.hooks import load_hooks

def handle_session_start():
	if not os.path.exists(os.path.join(get_project_dir(), ".claude", "tasks")):
		os.mkdir(os.path.join(get_project_dir(), ".claude", "tasks"))

	add_gitignore_rule("/tasks", file_path=os.path.join(get_project_dir(), ".claude", ".gitignore"))

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
		input_data = load_hooks()
		logging.info(f"Received input data: {input_data}")

		hook_event_name = input_data.get("hook_event_name", "")
		if not hook_event_name:
			logging.error("缺少 hook_event_name")
			return

		# 路由到不同的处理器
		if hook_event_name == "SessionStart":
			handle_session_start()
	except Exception as e:
		logging.error(f"未捕获的异常: {e}\n{traceback.format_exc()}")
		sys.exit(0)
