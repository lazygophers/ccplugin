import json
import subprocess
import sys
import traceback
from pathlib import Path

from lib import logging
from lib.hooks import load_hooks

prompt = {}


def _iter_pyproject_dirs(root_dir: Path):
	"""生成器：递归 yield 所有包含 pyproject.toml 文件的目录"""
	for pyproject_path in root_dir.rglob("pyproject.toml"):
		yield pyproject_path.parent


def handle_stop() -> tuple[bool, Path | None, str | None]:
	"""
		1. 遍历所有存在 pyproject.toml 文件的目录
		2. 检查 lib、scripts 和 .claude/scripts 目录
		3. 在每一个目录执行 `uvx ruff check`
		4. 返回 (success, failed_dir, error_output)
	"""
	cwd = Path.cwd()
	root_dir = cwd.joinpath("plugins")
	found_any = False

	# 检查 plugins 目录下所有有 pyproject.toml 的目录
	for dir_path in _iter_pyproject_dirs(root_dir):
		found_any = True
		# 1. ruff 检查
		try:
			result = subprocess.run(["uvx", "ruff", "check"], cwd=dir_path, capture_output=True, text=True, )
			if result.returncode != 0:
				error_output = result.stderr or result.stdout
				return False, dir_path, error_output.strip()
		except Exception as e:
			logging.error(f"执行 ruff check 失败: {e}")
			return False, dir_path, str(e)

		# 2. 检查 main.py --help（如果存在）
		main_py = dir_path / "scripts" / "main.py"
		if main_py.exists():
			try:
				result = subprocess.run(
					["uv", "run", "./scripts/main.py", "--help"],
					cwd=dir_path,
					capture_output=True,
					text=True,
					timeout=30,
				)
				if result.returncode != 0:
					error_output = result.stderr or result.stdout
					return False, dir_path, f"main.py --help 失败:\n{error_output.strip()}"
			except subprocess.TimeoutExpired:
				return False, dir_path, "main.py --help 超时"
			except Exception as e:
				logging.error(f"执行 main.py --help 失败: {e}")
				return False, dir_path, str(e)

	# 检查 lib 目录
	lib_dir = cwd.joinpath("lib")
	if lib_dir.exists():
		found_any = True
		try:
			result = subprocess.run(["uvx", "ruff", "check"], cwd=lib_dir, capture_output=True, text=True, )
			if result.returncode != 0:
				error_output = result.stderr or result.stdout
				return False, lib_dir, error_output.strip()
		except Exception as e:
			logging.error(f"执行 ruff check 失败: {e}")
			return False, lib_dir, str(e)

	# 检查 scripts 目录
	scripts_dir = cwd.joinpath("scripts")
	if scripts_dir.exists():
		found_any = True
		try:
			result = subprocess.run(["uvx", "ruff", "check"], cwd=scripts_dir, capture_output=True, text=True, )
			if result.returncode != 0:
				error_output = result.stderr or result.stdout
				return False, scripts_dir, error_output.strip()
		except Exception as e:
			logging.error(f"执行 ruff check 失败: {e}")
			return False, scripts_dir, str(e)

	# 检查 .claude/scripts 目录
	claude_scripts = cwd.joinpath(".claude", "scripts")
	if claude_scripts.exists():
		found_any = True
		try:
			result = subprocess.run(["uvx", "ruff", "check"], cwd=claude_scripts, capture_output=True, text=True, )
			if result.returncode != 0:
				error_output = result.stderr or result.stdout
				return False, claude_scripts, error_output.strip()
		except Exception as e:
			logging.error(f"执行 ruff check 失败: {e}")
			return False, claude_scripts, str(e)

	if not found_any:
		logging.info("未找到任何需要检查的目录")

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
				reason = f"代码检查失败：目录 `{failed_dir}`\n\n{error_output}"
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