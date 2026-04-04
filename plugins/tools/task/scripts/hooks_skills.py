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
from lib.hooks import load_hooks

def handle_session_start(session_id: str):
	"""检查 session_id 是否在任务索引中（index.json 格式：{session_id: [{task_id, ...}]}）"""
	index_path = os.path.join(get_project_dir(), ".claude", "tasks", "index.json")

	# 如果文件不存在，当做 session 不存在处理
	if not os.path.exists(index_path):
		print(json.dumps({
			"hookSpecificOutput": {
				"hookEventName": "SessionStart",
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
					"hookEventName": "SessionStart",
					"additionalContext": f".claude/tasks/index.json 缺少 {session_id} 的信息"
				}
			}))

def handle_pretooluse(tool_name: str, tool_input: dict, session_id: str):
	"""PreToolUse: 阻止未索引的 task agent 启动"""
	# 只检查 Agent 工具调用
	if tool_name != "Agent":
		sys.exit(0)

	# 提取 subagent_type
	subagent_type = tool_input.get("subagent_type", "")

	# 只检查 task:* agents（排除 task:loop）
	if not subagent_type.startswith("task:") or subagent_type == "task:loop":
		sys.exit(0)

	# 检查 index.json 是否存在
	index_path = os.path.join(get_project_dir(), ".claude", "tasks", "index.json")
	if not os.path.exists(index_path):
		print(f"阻止 {subagent_type} 启动：.claude/tasks/index.json 不存在", file=sys.stderr)
		sys.exit(2)

	# 检查 session_id 是否已索引（index.json 格式：{session_id: [{task_id, ...}]}）
	with open(index_path) as file:
		index = json.load(file)
		if session_id not in index:
			print(f"阻止 {subagent_type} 启动：session {session_id} 未在 index.json 中索引", file=sys.stderr)
			sys.exit(2)

		# 验证 session_id 对应的任务列表非空
		task_list = index.get(session_id, [])
		if not task_list:
			print(f"阻止 {subagent_type} 启动：session {session_id} 的任务列表为空", file=sys.stderr)
			sys.exit(2)

	# 通过检查，允许启动
	sys.exit(0)

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
		elif hook_event_name == "SubagentStart":
			handle_session_start(session_id)
		elif hook_event_name == "PreToolUse":
			tool_name = input_data.get("tool_name", "")
			tool_input = input_data.get("tool_input", {})
			handle_pretooluse(tool_name, tool_input, session_id)
	except Exception as e:
		logging.error(f"未捕获的异常: {e}\n{traceback.format_exc()}")
		sys.exit(0)
