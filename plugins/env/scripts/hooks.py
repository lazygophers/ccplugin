import json
import os
import subprocess
import sys

from lib import logging
from lib.hooks import load_hooks
from lib.utils import get_project_dir


def execute_command(command: str) -> str | None:
	"""执行命令"""
	try:
		logging.info(f"执行命令:{command}")
		return subprocess.run(command, cwd=get_project_dir(), env=os.environ, capture_output=True, text=True,
		                      encoding='utf-8').stdout.strip()
	except Exception as e:
		logging.error(f"命令执行失败: {e}")
		return None


def session_start():
	execute_command("uvx --from git+https://github.com/lazygophers/ccplugin.git@master update")


def handle_hook() -> None:
	"""处理 hook 模式：从 stdin 读取 JSON 并记录。"""
	try:
		hook_data = load_hooks()
		event_name = hook_data.get("hook_event_name")

		logging.info(f"接收到事件:{event_name}")

		if event_name == "SessionStart":
			session_start()

	except json.JSONDecodeError as e:
		logging.error(f"JSON 解析失败: {e}")
		sys.exit(1)
	except Exception as e:
		logging.error(f"Hook 处理失败: {e}")
		sys.exit(1)