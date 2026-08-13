import json
import os
import sys
from typing import Any, Dict

from version import init_version, auto_update


def load_hooks() -> Dict[str, Any]:
	"""处理 Hook 事件：从 stdin 读取 JSON 数据并执行相应的 Hook 动作"""
	try:
		hook_data = json.load(sys.stdin)
		if not isinstance(hook_data, dict):
			raise ValueError("Hook 数据必须是 JSON 对象")

		event_name = hook_data.get("hook_event_name", "").strip()
		if not event_name:
			raise ValueError("缺少必需的 hook_event_name 字段")

		if event_name == "SessionStart":
			plugins_path = os.getenv("CLAUDE_PLUGIN_ROOT")
			if plugins_path is not None:
				agent_md_path = os.path.join(plugins_path, "AGENT.md")
				if os.path.exists(agent_md_path):
					with open(agent_md_path, "r", encoding="utf-8") as f:
						for line in f:
							print(line.replace("${CLAUDE_PLUGIN_ROOT}", plugins_path))

		return hook_data

	except (json.JSONDecodeError, ValueError):
		sys.exit(1)
	except Exception:
		sys.exit(1)


def handle_hook() -> None:
	"""处理 hook 模式：从 stdin 读取 JSON 并记录。"""
	hook_data = load_hooks()
	event_name = hook_data.get("hook_event_name")

	if event_name == "SessionStart":
		init_version()
	elif event_name == "UserPromptSubmit":
		auto_update()
