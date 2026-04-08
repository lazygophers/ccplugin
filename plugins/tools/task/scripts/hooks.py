"""
Claude Code Hooks 事件处理模块

处理来自 Claude Code 的各种 Hook 事件，根据配置触发 TTS 和系统通知功能。
支持的事件：SessionStart、SessionEnd、UserPromptSubmit、PreToolUse、PostToolUse、Notification、PreCompact
"""
import json
import os.path
import shutil
import sys
import time
import traceback
from typing import Dict

from lib import logging
from lib.hooks import load_hooks
from lib.utils.env import get_project_dir
from lib.utils.gitignore import add_gitignore_rule

def handle_session_start():
	pass


def handle_stop():
	pass

def handle_hook() -> None:
	"""处理 Hook 事件：从 stdin 读取 JSON 数据并执行相应的 Hook 动作"""
	try:
		input_data = load_hooks()

		hook_event_name = input_data.get("hook_event_name", "")
		if not hook_event_name:
			logging.error("缺少 hook_event_name")
			return

		if hook_event_name == "SessionStart":
			handle_session_start()
		elif hook_event_name == "Stop":
			handle_stop()
	except Exception as e:
		logging.error(f"未捕获的异常: {e}\n{traceback.format_exc()}")
		sys.exit(0)
