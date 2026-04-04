"""
Claude Code Hooks 事件处理模块

处理来自 Claude Code 的各种 Hook 事件，根据配置触发 TTS 和系统通知功能。
支持的事件：SessionStart、SessionEnd、UserPromptSubmit、PreToolUse、PostToolUse、Notification、PreCompact
"""
import json
import os.path
import sys
import traceback

from lib import logging
from lib.utils.env import get_project_dir
from lib.utils.gitignore import add_gitignore_rule
from lib.hooks import load_hooks

def handle_session_start(session_id: str):
	"""SessionStart 事件处理：创建 .claude/tasks 目录并初始化索引"""
	tasks_dir = os.path.join(get_project_dir(), ".claude", "tasks")

	# 创建目录
	if not os.path.exists(tasks_dir):
		os.makedirs(tasks_dir, exist_ok=True)
		logging.info(f"Created tasks directory: {tasks_dir}")

	# 添加到 .gitignore
	add_gitignore_rule("/tasks", file_path=os.path.join(get_project_dir(), ".claude", ".gitignore"))

	# 初始化索引文件（如果不存在）
	index_path = os.path.join(tasks_dir, "index.json")
	if not os.path.exists(index_path):
		with open(index_path, "w") as f:
			json.dump({}, f, indent=2, ensure_ascii=False)
		logging.info(f"Initialized index file: {index_path}")

	# 检查索引中是否有当前 session
	with open(index_path) as f:
		index = json.load(f)

	if session_id not in index:
		logging.info(f"Session {session_id} not found in index, will be created when first task starts")

def handle_hook_skills() -> None:
	"""处理 Hook 事件：从 stdin 读取 JSON 数据并执行相应的 Hook 动作

	Hook 数据格式示例：
	{
		"hook_event_name": "SessionStart",
		"source": "startup",
		"message": "Session started"
	}
	"""
	try:
		input_data = load_hooks()
		logging.info(f"Received input data: {input_data}")

		hook_event_name = input_data.get("hook_event_name", "")
		if not hook_event_name:
			logging.error("缺少 hook_event_name")
			return

		session_id = input_data.get("session_id", "")
		if not session_id:
			logging.error("缺少 session_id")
			return

		# 路由到不同的处理器
		if hook_event_name == "SessionStart":
			handle_session_start(session_id)
	except Exception as e:
		logging.error(f"未捕获的异常: {e}\n{traceback.format_exc()}")
		sys.exit(0)
