import json
import sys

from lib import logging
from lib.hooks import load_hooks
from lib.hooks.pre_tool_use import handle_pre_tool_use, PreToolUseConfig

pre_tool_use_config = PreToolUseConfig()
pre_tool_use_config.safe_remove_files = [
	"pyproject.toml"
	"uv.lock"
]
pre_tool_use_config.safe_edit_files = [
	"pyproject.toml"
	"uv.lock"
]
pre_tool_use_config.safe_read_files = [
	"uv.lock"
]


def handle_hook() -> None:
	"""处理 hook 模式：从 stdin 读取 JSON 并记录。"""
	hook_data = load_hooks()
	event_name = hook_data.get("hook_event_name")

	if event_name == "PreToolUse":
		handle_pre_tool_use(hook_data, pre_tool_use_config)