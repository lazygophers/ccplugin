import json

from lib import logging
from lib.hooks import load_hooks
from version import init_version, auto_update


def handle_hook() -> None:
	"""处理 hook 模式：从 stdin 读取 JSON 并记录。"""
	hook_data = load_hooks()
	event_name = hook_data.get("hook_event_name")

	logging.info(f"接收到事件:{event_name}")

	if event_name == "SessionStart":
		init_version()
	elif event_name == "UserPromptSubmit":
		auto_update()
	elif event_name == "PreToolUse":
		auto_update()