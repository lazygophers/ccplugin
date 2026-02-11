import json
import sys
import traceback
from typing import Dict, Any

from lib import logging
from lib.hooks import load_hooks
from lib.utils.os import filepath_to_slash

remove_files = [filepath_to_slash(item) for item in [
	"go.mod",
	"go.sum",
]]

edit_files = [filepath_to_slash(item) for item in [
	"go.mod",
	"go.sum",
]]

read_files = [filepath_to_slash(item) for item in [
	"go.sum",
]]


def handle_pre_tool_use(input_data: Dict[str, Any]):
	"""处理 PreToolUse 事件"""
	try:
		tool_name = input_data.get("tool_name")
		tool_input = input_data.get("tool_input")

		if tool_name is None or tool_input is None:
			logging.debug(f"PreToolUse: 缺少必要字段, tool_name={tool_name}, tool_input={tool_input}")
			return

		if tool_name is None or tool_input is None:
			return

		tool_name = str(tool_name).lower()

		if tool_name == "read":
			if "file_path" in tool_input:
				file_path = tool_input.get("file_path", "")
				for locked_file in read_files:
					if file_path.find(locked_file) >= 0:
						logging.warn(f"检测到受保护文件操作: file_path={file_path}, locked_file={locked_file}")
						print(json.dumps({
							"hookSpecificOutput":
								{
									"hookEventName": "PreToolUse",
									"permissionDecision": "deny",
									"permissionDecisionReason": "危险警告，不允许读取文件",
									"updatedInput": tool_input,
								}
						}))
						return
		elif tool_name == "edit":
			if "file_path" in tool_input:
				file_path = tool_input.get("file_path", "")
				for locked_file in edit_files:
					if file_path.find(locked_file) >= 0:
						logging.warn(f"检测到受保护文件操作: file_path={file_path}, locked_file={locked_file}")
						print(json.dumps({
							"hookSpecificOutput":
								{
									"hookEventName": "PreToolUse",
									"permissionDecision": "deny",
									"permissionDecisionReason": "危险警告，不允许修改文件",
									"updatedInput": tool_input,
								}
						}))
						return
		elif tool_name == "bash":
			if "command" in tool_input:
				command = tool_input.get("command", "")
				if command.find("rm") >= 0:
					for locked_file in remove_files:
						if command.find(locked_file) >= 0:
							logging.warning(f"检测到受保护文件操作: command={command}, locked_file={locked_file}")
							print(json.dumps({
								"hookSpecificOutput": {
									"hookEventName": "PreToolUse",
									"permissionDecision": "deny",
									"permissionDecisionReason": "危险警告，不允许删除文件",
									"updatedInput": tool_input
								}
							}))
							return

	except Exception as e:
		logging.error(f"PreToolUse 处理异常: {e}\n{traceback.format_exc()}")


def handle_hook() -> None:
	"""处理 hook 模式：从 stdin 读取 JSON 并记录。"""
	try:
		hook_data = load_hooks()
		event_name = hook_data.get("hook_event_name")

		if event_name == "PreToolUse":
			handle_pre_tool_use(hook_data)

	except json.JSONDecodeError as e:
		logging.error(f"JSON 解析失败: {e}")
		sys.exit(1)
	except Exception as e:
		logging.error(f"Hook 处理失败: {e}")
		sys.exit(1)