import json
import sys

from lib import logging
from lib.hooks import load_hooks
from lib.hooks.pre_tool_use import handle_pre_tool_use, PreToolUseConfig

pre_tool_use_config = PreToolUseConfig()
pre_tool_use_config.safe_read_files = [
	"go.sum"
]
pre_tool_use_config.safe_edit_files = [
	"go.mod",
	"go.sum",
]
pre_tool_use_config.safe_remove_files = [
	"go.mod",
	"go.sum",
]

def handle_hook() -> None:
	"""处理 hook 模式：从 stdin 读取 JSON 并记录。"""
	try:
		hook_data = load_hooks()
		event_name = hook_data.get("hook_event_name")

		if event_name == "PreToolUse":
			handle_pre_tool_use(hook_data, pre_tool_use_config)

	except json.JSONDecodeError as e:
		logging.error(f"JSON 解析失败: {e}")
		sys.exit(1)
	except Exception as e:
		logging.error(f"Hook 处理失败: {e}")
		sys.exit(1)