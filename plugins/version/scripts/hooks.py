import json
import sys

from ccplugin.lib.logging import error
from plugins.version.scripts.version import init_version, auto_update


def handle_hook() -> None:
	"""处理 hook 模式：从 stdin 读取 JSON 并记录。"""
	try:
		hook_data = json.load(sys.stdin)

		event_name = hook_data.get("hook_event_name")
		if event_name == "SessionStart":
			init_version()
		if event_name == "UserPromptSubmit":
			auto_update()

	except json.JSONDecodeError as e:
		error(f"JSON 解析失败: {e}")
		sys.exit(1)
	except Exception as e:
		error(f"Hook 处理失败: {e}")
		sys.exit(1)