import json
import subprocess
import sys
from pathlib import Path

import traceback

from lib import logging
from lib.hooks import load_hooks

prompt = {
	"S"
}


def _iter_pyproject_dirs(root_dir: Path):
	"""生成器：递归 yield 所有包含 pyproject.toml 文件的目录"""
	for pyproject_path in root_dir.rglob("pyproject.toml"):
		yield pyproject_path.parent


def handle_stop() -> tuple[bool, Path | None, str | None]:
	"""
		1. 遍历所有存在 pyproject.toml 文件的目录
		2. 在每一个有 pyproject.toml 文件的目录执行 `uvx ruff check`
		3. 返回 (success, failed_dir, error_output)
	"""
	root_dir = Path.cwd().joinpath("plugins")
	found_any = False

	for dir_path in _iter_pyproject_dirs(root_dir):
		found_any = True
		try:
			result = subprocess.run(
				["uvx", "ruff", "check"],
				cwd=dir_path,
				capture_output=True,
				text=True,
			)
			if result.returncode != 0:
				error_output = result.stderr or result.stdout
				return False, dir_path, error_output.strip()
		except Exception as e:
			logging.error(f"执行 ruff check 失败: {e}")
			return False, dir_path, str(e)

	if not found_any:
		logging.info("未找到任何 pyproject.toml 文件")

	return True, None, None


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
			success, failed_dir, error_output = handle_stop()
			if success:
				print(json.dumps({"continue": False}))
			else:
				reason = f"代码检查失败：目录 `{failed_dir}` 的 !`uvx ruff check` 未通过\n\n错误输出：\n{error_output}"
				print(json.dumps({"continue": True, "decision": "block", "reason": reason}))
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