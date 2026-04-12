"""
Task 插件 Hooks 事件处理模块

处理 SessionStart 事件：替换模板变量 ${CLAUDE_PLUGIN_ROOT}。
"""
import os
import sys
import traceback

from lib import logging
from lib.hooks import load_hooks
from lib.utils.env import get_plugins_path
from utils import is_plugin_env
from typing import Dict, Any

def handle_session_start():
	"""SessionStart Hook：替换模板变量"""

	# 只在插件环境时替换变量
	if not is_plugin_env():
		return

	plugin_root = get_plugins_path()
	dirs_to_scan = ["skills", "agents", "commands"]

	for dir_name in dirs_to_scan:
		dir_path = os.path.join(plugin_root, dir_name)
		if not os.path.exists(dir_path):
			continue

		_replace_plugin_root_variable(dir_path, plugin_root)


def _replace_plugin_root_variable(directory: str, plugin_root: str) -> None:
	"""递归扫描目录，替换文件中的 ${CLAUDE_PLUGIN_ROOT} 变量
	Args:
		directory: 要扫描的目录路径
		plugin_root: 插件根目录路径
	"""
	for root, dirs, files in os.walk(directory):
		for file_name in files:
			file_path = os.path.join(root, file_name)

			try:
				with open(file_path, 'r', encoding='utf-8') as f:
					content = f.read()

				# 检查是否包含需要替换的变量
				if "${CLAUDE_PLUGIN_ROOT}" not in content:
					continue

				# 执行替换
				new_content = content.replace("${CLAUDE_PLUGIN_ROOT}", plugin_root)

				# 只有内容变化时才写入
				if new_content != content:
					with open(file_path, 'w', encoding='utf-8') as f:
						f.write(new_content)
					logging.info(f"已替换变量: {file_path}")
			except (UnicodeDecodeError, PermissionError):
				# 跳过二进制文件或无权限文件
				continue

def handle_user_prompt_submit(input: Dict[str,Any]):
	"""UserPromptSubmit Hook：不再强制注入 flow，仅在有活跃任务时提示"""
	pass

def handle_stop():
	pass

def handle_hook() -> None:
	"""处理 Hook 事件：从 stdin 读取 JSON 数据并执行相应的 Hook 动作"""
	try:
		input_data = load_hooks()

		hook_event_name = input_data.get("hook_event_name", "")
		if not hook_event_name:
			logging.error("缺少 hook_event_name")
			return

		if hook_event_name == "SessionStart":
			handle_session_start()
		elif hook_event_name == "UserPromptSubmit":
			handle_user_prompt_submit(input_data)
		elif hook_event_name == "Stop":
			handle_stop()
	except Exception as e:
		logging.error(f"未捕获的异常: {e}\n{traceback.format_exc()}")
		sys.exit(0)
