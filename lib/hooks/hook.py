import json
import os.path
import sys
from typing import Any, Dict


_SENSITIVE_KEYS = frozenset({
	'password', 'token', 'secret', 'api_key', 'credential',
	'authorization', 'cookie', 'session', 'private_key',
})


def _truncate_value_for_log(value: Any, max_length: int = 100, _key: str = "") -> Any:
	if _key.lower() in _SENSITIVE_KEYS:
		return "***REDACTED***"
	if isinstance(value, dict):
		return {k: _truncate_value_for_log(v, max_length, _key=k) for k, v in value.items()}
	elif isinstance(value, list):
		return [_truncate_value_for_log(item, max_length) for item in value]
	elif isinstance(value, str):
		if len(value) > max_length:
			return value[:max_length] + "..."
		return value
	else:
		return value


def load_hooks() -> Dict[str, Any]:
	"""处理 Hook 事件：从 stdin 读取 JSON 数据并执行相应的 Hook 动作

	  Hook 数据格式示例：
	  {
	      "hook_event_name": "SessionStart",
	      "source": "startup",
	      "message": "Session started"
	  }
	  """
	try:
		hook_data = json.load(sys.stdin)
		if not isinstance(hook_data, dict):
			raise ValueError("Hook 数据必须是 JSON 对象")

		event_name = hook_data.get("hook_event_name", "").strip()
		if not event_name:
			raise ValueError("缺少必需的 hook_event_name 字段")

		# 处理公共逻辑
		if event_name == "SessionStart":
			plugins_path = os.getenv("CLAUDE_PLUGIN_ROOT")
			if plugins_path is not None:
				agent_md_path = os.path.join(plugins_path, "AGENT.md")
				if os.path.exists(agent_md_path):
					with open(agent_md_path, "r", encoding="utf-8") as f:
						for line in f:
							print(line.replace("${CLAUDE_PLUGIN_ROOT}", plugins_path))

		return hook_data

	except json.JSONDecodeError as e:
		sys.exit(1)
	except ValueError as e:
		sys.exit(1)
	except Exception as e:
		import traceback
		traceback.format_exc()
		sys.exit(1)


if __name__ == '__main__':
	load_hooks()
