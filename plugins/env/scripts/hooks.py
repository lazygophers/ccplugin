import json
import os
import subprocess
import sys

from lib import logging
from lib.hooks import load_hooks
from lib.utils import get_project_dir

def handle_hook() -> None:
	"""处理 hook 模式：从 stdin 读取 JSON 并记录。"""
	try:
		hook_data = load_hooks()
		event_name = hook_data.get("hook_event_name")

	except json.JSONDecodeError as e:
		logging.error(f"JSON 解析失败: {e}")
		sys.exit(1)
	except Exception as e:
		logging.error(f"Hook 处理失败: {e}")
		sys.exit(1)