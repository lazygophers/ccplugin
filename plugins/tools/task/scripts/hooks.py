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

from lib import logging
from lib.utils.env import get_project_dir
from lib.utils.gitignore import add_gitignore_rule
from lib.hooks import load_hooks

def cleanup_expired_tasks():
	"""清理超过30天的过期任务数据

	只有当任务的所有关联文件都成功删除后，才从 index.json 中移除记录。
	如果删除失败，保留在 index.json 中，下次 SessionStart 时重试。
	"""

	index_path = os.path.join(get_project_dir(), ".claude", "tasks", "index.json")
	if not os.path.exists(index_path):
		return

	# 读取索引
	with open(index_path) as f:
		index = json.load(f)

	# 30天前的时间戳
	expiry_threshold = int(time.time()) - (30 * 24 * 60 * 60)

	# 遍历所有会话
	cleaned_count = 0
	index_modified = False

	for session_id, tasks in list(index.items()):
		# 过滤掉成功清理的过期任务
		active_tasks = []
		for task in tasks:
			task_id = task.get("task_id", "")
			updated_at = task.get("updated_at", 0)

			# 检查是否过期
			if updated_at < expiry_threshold:
				# 尝试删除所有关联文件
				all_deleted = True

				# 1. 删除任务目录
				task_dir = os.path.join(get_project_dir(), ".claude", "tasks", task_id)
				if os.path.exists(task_dir):
					try:
						shutil.rmtree(task_dir)
					except Exception as e:
						logging.error(f"删除任务目录失败 {task_dir}: {e}")
						all_deleted = False

				# 2. 删除检查点
				checkpoint_path = os.path.join(get_project_dir(), ".claude", "checkpoints", f"{task_id}.json")
				if os.path.exists(checkpoint_path):
					try:
						os.remove(checkpoint_path)
					except Exception as e:
						logging.error(f"删除检查点失败 {checkpoint_path}: {e}")
						all_deleted = False

				# 3. 删除上下文快照目录
				context_dir = os.path.join(get_project_dir(), ".claude", "context", task_id)
				if os.path.exists(context_dir):
					try:
						shutil.rmtree(context_dir)
					except Exception as e:
						logging.error(f"删除上下文快照失败 {context_dir}: {e}")
						all_deleted = False

				# 只有全部成功删除才从索引中移除
				if all_deleted:
					cleaned_count += 1
					index_modified = True
					# 不添加到 active_tasks，从索引中移除
				else:
					# 删除失败，保留在索引中，下次重试
					active_tasks.append(task)
					logging.warning(f"任务 {task_id} 清理未完成，保留在索引中待下次重试")
			else:
				# 未过期，保留
				active_tasks.append(task)

		# 更新会话的任务列表
		if active_tasks:
			index[session_id] = active_tasks
		else:
			# 如果会话所有任务都已清理，删除整个会话键
			del index[session_id]
			index_modified = True

	# 只有索引被修改时才写回
	if index_modified:
		with open(index_path, "w") as f:
			json.dump(index, f, indent=2, ensure_ascii=False)
		if cleaned_count > 0:
			logging.info(f"已清理 {cleaned_count} 个过期任务（超过30天）")

def handle_session_start():
	if not os.path.exists(os.path.join(get_project_dir(), ".claude", "tasks")):
		os.mkdir(os.path.join(get_project_dir(), ".claude", "tasks"))

	add_gitignore_rule("/tasks", file_path=os.path.join(get_project_dir(), ".claude", ".gitignore"))

	# 清理过期任务
	cleanup_expired_tasks()

def handle_stop(hook_event_name: str, session_id: str):
	"""Stop hook: 检查任务是否完成（index.json 格式：{session_id: [{task_id, ...}]}）"""
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

	# 读取索引文件（Map 结构，key 为 session_id 哈希）
	with open(index_path) as file:
		index = json.load(file)
		if session_id not in index:
			print(json.dumps({
				"hookSpecificOutput": {
					"hookEventName":hook_event_name,
					"additionalContext": f".claude/tasks/index.json 缺少 {session_id} 的信息"
				}
			}))
			return

		# session_id 对应的是任务数组，取最新任务（数组最后一个元素）
		task_list = index.get(session_id, [])
		if not task_list:
			print(json.dumps({
				"hookSpecificOutput": {
					"hookEventName":hook_event_name,
					"additionalContext": f"session {session_id} 的任务列表为空"
				}
			}))
			return

		# 取最新的任务（数组最后一个元素）
		current_task = task_list[-1]
		task_id = current_task.get("task_id", "")

	status_file_path = os.path.join(get_project_dir(), ".claude", "tasks", task_id, "metadata.json")
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
