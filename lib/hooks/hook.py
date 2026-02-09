import json
import logging
import os.path
import sys

from lib.utils import get_plugins_path


def load_hooks():
	"""处理 Hook 事件：从 stdin 读取 JSON 数据并执行相应的 Hook 动作

	  Hook 数据格式示例：
	  {
	      "hook_event_name": "SessionStart",
	      "source": "startup",
	      "message": "Session started"
	  }
	  """
	try:
		logging.info("load_hooks: 开始读取 stdin")
		hook_data = json.load(sys.stdin)
		logging.info(f"load_hooks: 读取到数据: {hook_data}")
		if not isinstance(hook_data, dict):
			raise ValueError("Hook 数据必须是 JSON 对象")

		event_name = hook_data.get("hook_event_name", "").strip()
		if not event_name:
			raise ValueError("缺少必需的 hook_event_name 字段")

		# 处理公共逻辑
		if event_name == "SessionStart":
			logging.info("load_hooks: 处理 SessionStart 事件")
			plugins_path = get_plugins_path()
			logging.info(f"load_hooks: plugins_path = {plugins_path}")
			if plugins_path is None:
				logging.debug("CLAUDE_PLUGIN_ROOT 未设置，跳过 AGENT.md 处理")
			else:
				agent_md_path = os.path.join(plugins_path, "AGENT.md")
				if os.path.exists(agent_md_path):
					with open(agent_md_path, "r", encoding="utf-8") as f:
						for line in f:
							print(line.replace("${CLAUDE_PLUGIN_ROOT}", plugins_path))

		return hook_data

	except json.JSONDecodeError as e:
		logging.error(f"JSON 解析失败: {e}")
		sys.exit(1)
	except ValueError as e:
		logging.error(f"Hook 数据验证失败: {e}")
		sys.exit(1)
	except Exception as e:
		logging.error(f"Hook 处理失败: {e}")
		import traceback
		logging.error(traceback.format_exc())
		sys.exit(1)


if __name__ == '__main__':
	load_hooks()