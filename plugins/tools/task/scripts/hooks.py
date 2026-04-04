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

def handle_session_start():
	if not os.path.exists(os.path.join(get_project_dir(), ".claude", "tasks")):
		os.mkdir(os.path.join(get_project_dir(), ".claude", "tasks"))

	add_gitignore_rule("/tasks", file_path=os.path.join(get_project_dir(), ".claude", ".gitignore"))

def handle_stop(hook_event_name: str, session_id: str):
	index_path = os.path.join(get_project_dir(), ".claude", "tasks", "index.json")

	# 如果文件不存在，当做 session 不存在处理
	if not os.path.exists(index_path):
		print(json.dumps({
			"hookSpecificOutput": {
				"hookEventName":hook_event_name,
				"additionalContext": ".claude/tasks/index.json 不存在"
			}
		}))
		return

	# 读取索引文件
	with open(index_path) as file:
		tasks = json.load(file)
		if session_id not in tasks:
			print(json.dumps({
				"hookSpecificOutput": {
					"hookEventName":hook_event_name,
					"additionalContext": f".claude/tasks/index.json 缺少 {session_id} 的信息"
				}
			}))

		session = tasks.get(session_id, {})

	status_file_path = os.path.join(get_project_dir(), ".claude", "tasks", session.get("task_id", ""), "metadata.json")
	if not os.path.exists(status_file_path):
		print(json.dumps({
			"hookSpecificOutput": {
				"hookEventName":hook_event_name,
				"additionalContext": f"{status_file_path} 不存在"
			}
		}))
		return

	with open(status_file_path) as file:
		metadata = json.load(file)
		if metadata.get("phase", "") != "completed":
			print(json.dumps({
				"hookSpecificOutput": {
					"hookEventName":hook_event_name,
					"additionalContext": "task not finish，continue"
				}
			}))
			sys.exit(2)
			return

def handle_hook() -> None:
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

		# 路由到不同的处理器
		if hook_event_name == "SessionStart":
			handle_session_start()
		elif hook_event_name == "Stop":
			handle_stop(hook_event_name, input_data.get("session_id", ""))
	except Exception as e:
		logging.error(f"未捕获的异常: {e}\n{traceback.format_exc()}")
		sys.exit(0)
