import json
import sys
import traceback

from lib import logging
from lib.hooks import load_hooks

prompt = {}


def handle_stop() -> bool:
	"""
		1. 遍历所有存在 pyproject.toml 文件的目录
		2. 在每一个有 pyproject.toml 文件的目录执行 `uvx ruff check`
		3. 如果返回的 code 为 0，则返回 true，否则返回 false
	"""


def main():
	"""主函数，捕获所有异常"""
	try:
		input_data = load_hooks()
		logging.info(f"Received input data: {input_data}")

		hook_event_name = input_data.get("hook_event_name", "")
		if not hook_event_name:
			logging.error("缺少 hook_event_name")
			print(json.dumps({"continue": True, "suppressOutput": False}))
			return

		# 路由到不同的处理器
		if hook_event_name == "Stop":
			if handle_stop():
				print(json.dumps({"continue": False}))
			else:
				print(json.dumps({"continue": True, "decision": "block", "reason": "确保每一个存在 `pyproject.toml` 文件所在目录执行 !`uvx ruff check` 都是成功的" }))
		else:
			logging.warning(f"未知的 hook 事件: {hook_event_name}")
			print(json.dumps({"continue": True}))

	except json.JSONDecodeError as e:
		logging.error(f"JSON 解析错误: {e}\n{traceback.format_exc()}")
		print(json.dumps({"continue": True, "suppressOutput": False}))
	except Exception as e:
		logging.error(f"未捕获的异常: {e}\n{traceback.format_exc()}")
		print(json.dumps({"continue": True, "suppressOutput": False}))
		sys.exit(0)


if __name__ == '__main__':
	main()