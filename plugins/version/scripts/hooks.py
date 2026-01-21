import json
import sys
from pathlib import Path

# Find project root and ccplugin package
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent.parent

# Add ccplugin/ccplugin to sys.path to make lib available
ccplugin_path = project_root / "ccplugin" / "ccplugin"
if ccplugin_path.exists():
	sys.path.insert(0, str(ccplugin_path))
else:
	# Fallback: search upward for lib directory
	current = script_dir
	for _ in range(5):
		if (current / "ccplugin" / "ccplugin" / "lib").exists():
			sys.path.insert(0, str(current / "ccplugin" / "ccplugin"))
			break
		current = current.parent

from lib import logging
from version import init_version, auto_update


def handle_hook() -> None:
	"""处理 hook 模式：从 stdin 读取 JSON 并记录。"""
	try:
		hook_data = json.load(sys.stdin)
		event_name = hook_data.get("hook_event_name")

		logging.info(f"接收到事件:{event_name}")

		if event_name == "SessionStart":
			init_version()
		if event_name == "UserPromptSubmit":
			auto_update()

	except json.JSONDecodeError as e:
		logging.error(f"JSON 解析失败: {e}")
		sys.exit(1)
	except Exception as e:
		logging.error(f"Hook 处理失败: {e}")
		sys.exit(1)