import json
import traceback
from typing import Dict, Any

from lib import logging
from lib.utils.os import filepath_to_slash


class PreToolUseConfig:
	"""
	PreToolUseConfig 类用于存储 PreToolUse 的配置信息。
	"""

	safe_remove_files: list[str] = []
	safe_edit_files: list[str] = []
	safe_read_files: list[str] = []

	def _before(self):
		self.safe_remove_files = [filepath_to_slash(item) for item in self.safe_remove_files]
		self.safe_edit_files = [filepath_to_slash(item) for item in self.safe_edit_files]
		self.safe_read_files = [filepath_to_slash(item) for item in self.safe_read_files]


def handle_pre_tool_use(input_data: Dict[str, Any], config: PreToolUseConfig) -> bool:
	try:
		if "tool_name" not in input_data:
			return False
		if "tool_input" not in input_data:
			return False

		tool_name = str(input_data.get("tool_name", "")).lower()
		tool_input = input_data.get("tool_input", "")

		if tool_name == "read":
			if len(config.safe_read_files) > 0 and "file_path" in tool_input:
				file_path = tool_input.get("file_path", "")
				for locked_file in config.safe_read_files:
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
						return True
		elif tool_name == "edit":
			if len(config.safe_edit_files) > 0 and "file_path" in tool_input:
				file_path = tool_input.get("file_path", "")
				for locked_file in config.safe_edit_files:
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
						return True
		elif tool_name == "bash":
			if len(config.safe_remove_files) > 0 and "command" in tool_input:
				command = tool_input.get("command", "")
				if command.find("rm") >= 0 or command.find("cp") >= 0 or command.find("mv") >= 0:
					for locked_file in config.safe_remove_files:
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
							return True

	except Exception as e:
		logging.error(f"PreToolUse 处理异常: {e}\n{traceback.format_exc()}")
		return False

	return False