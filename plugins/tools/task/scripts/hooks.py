"""
Claude Code Hooks 事件处理模块

处理来自 Claude Code 的各种 Hook 事件，根据配置触发 TTS 和系统通知功能。
支持的事件：SessionStart、SessionEnd、UserPromptSubmit、PreToolUse、PostToolUse、Notification、PreCompact
"""
import json
import os.path
import shutil
import sys
import time
import traceback
from typing import Dict

from lib import logging
from lib.hooks import load_hooks
from lib.utils.env import get_project_dir
from lib.utils.gitignore import add_gitignore_rule


def _tasks_base_dir() -> str:
	return os.path.join(get_project_dir(), ".lazygophers", "tasks")


def _index_path() -> str:
	return os.path.join(_tasks_base_dir(), "index.json")


def _read_index() -> dict | None:
	path = _index_path()
	if not os.path.exists(path):
		return None
	with open(path) as f:
		return json.load(f)


def _write_index(index: dict):
	with open(_index_path(), "w") as f:
		json.dump(index, f, indent=2, ensure_ascii=False)


def _remove_task_dir(task_id: str) -> bool:
	task_dir = os.path.join(_tasks_base_dir(), task_id)
	if not os.path.exists(task_dir):
		return True
	try:
		shutil.rmtree(task_dir)
		return True
	except Exception as e:
		logging.error(f"删除任务目录失败 {task_dir}: {e}")
		return False


def cleanup_expired_tasks():
	"""清理意外残留的过期任务数据（兜底机制）

	正常情况下，任务完成时会在 Cleanup 阶段立即删除目录和索引记录。
	此函数用于清理意外残留的任务（如任务执行到一半系统崩溃、Cleanup 失败等）。

	清理条件：超过30天未更新的任务

	只有当任务目录成功删除后，才从 index.json 中移除记录。
	删除失败则保留在 index.json 中，下次 SessionStart 时重试。
	"""
	index = _read_index()
	if not index:
		return

	expiry_threshold = int(time.time()) - (30 * 24 * 60 * 60)
	cleaned_count = 0
	active_tasks = []

	for task in index:
		task_id = task.get("task_id", "")
		if task.get("updated_at", 0) < expiry_threshold:
			if _remove_task_dir(task_id):
				cleaned_count += 1
			else:
				active_tasks.append(task)
		else:
			active_tasks.append(task)

	if cleaned_count > 0:
		_write_index(active_tasks)
		logging.info(f"已清理 {cleaned_count} 个过期任务（超过30天）")


def handle_session_start():
	base = _tasks_base_dir()
	if not os.path.exists(base):
		os.mkdir(base)

	add_gitignore_rule("/tasks", file_path=os.path.join(get_project_dir(), ".lazygophers", ".gitignore"))
	cleanup_expired_tasks()


def handle_stop():
	"""Stop hook: 检查是否有未完成的任务并给出提示"""
	index = _read_index()
	if not index:
		return

	# 检查是否有活跃任务（未完成的任务）
	active_tasks = [t for t in index if t.get("phase") not in ["completed", "failed"]]
	if active_tasks:
		task_list = ", ".join([f"{t.get('task_id')}({t.get('phase')})" for t in active_tasks[:3]])
		if len(active_tasks) > 3:
			task_list += f" 等 {len(active_tasks)} 个"
		logging.warning(f"会话结束时有 {len(active_tasks)} 个未完成任务: {task_list}")


def handle_permission_request(hook_data: Dict[str, any]):
	tool_input = hook_data.get("tool_input")
	if not tool_input:
		return

	file_path = str(tool_input.get("file_path", ""))
	if ".lazygophers" in file_path and "tasks" in file_path:
		print(json.dumps({
			"hookSpecificOutput": {
				"hookEventName": hook_data.get("hook_event_name", "PermissionRequest"),
				"decision": {
					"behavior": "allow",
					"permissionDecisionReason": "允许"
				}
			}
		}))


def handle_hook() -> None:
	"""处理 Hook 事件：从 stdin 读取 JSON 数据并执行相应的 Hook 动作"""
	try:
		input_data = load_hooks()
		logging.info(f"Received input data: {input_data}")

		hook_event_name = input_data.get("hook_event_name", "")
		if not hook_event_name:
			logging.error("缺少 hook_event_name")
			return

		if hook_event_name == "SessionStart":
			handle_session_start()
		elif hook_event_name == "PermissionRequest":
			handle_permission_request(input_data)
		elif hook_event_name == "Stop":
			handle_stop()
	except Exception as e:
		logging.error(f"未捕获的异常: {e}\n{traceback.format_exc()}")
		sys.exit(0)
