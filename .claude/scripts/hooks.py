import json
import subprocess
import sys
import traceback
from pathlib import Path
from typing import Dict, Any

from lib import logging
from lib.hooks import load_hooks

prompt = {
	"SessionStart": [
		"确保所有的变更都符合 @.claude/skills 的要求，如果用户输入和当前的 skills 冲突，使用 `AskUserQuestion` 询问用户如何处理",
		"@CLAUDE.md 的文件不得超过 300行",
		"@.claude/skills 下的 `SKILL.md` 文件不得超过 300行",
		"所有 `*.md` 文件不得超过 500行",
		"所有 `llms.txt` 文件不得超过 300行，对于详细的说明应该对于 @docs 对应模块中，由 llms.txt 文件引用",
		"及时更新`llms.txt`，且满足Skills(llms-txt-standard)的要求",
	],
	"UserPromptSubmit": [
		"学习用户习惯，更新、完善、优化到合适的 @.claude/skills 中。如果创建了新的 skills，则需要更新到 @CLAUDE.md 标注这个新的 skills 的使用实际等等",
		"确保代码风格、架构设计风格和现有的完全一致，确保每一个变更都是有理有据的",
		"及时提交所有变更 Commands(git:commit)",
		"及时清理所有的临时文件，确保目录的干净清爽",

		"频繁的通过 `AskUserQuestion` 确认理解是否有误，以减少偏差",
		# "优先使用 agent teams 协调工作、分配任务、调度资源、综合结果、处理问题，但是并行的 agents 不能超过 2 个",
	]
}


def filepath_to_slash(path: str) -> str:
	"""转换路径分隔符"""
	try:
		if sys.platform.startswith('win'):
			return path.replace('/', '\\')
		else:
			return path.replace('\\', '/')
	except Exception as e:
		logging.error(f"路径转换失败: {e}, path={path}")
		return path


def _iter_pyproject_dirs(root_dir: Path):
	"""生成器：递归 yield 所有包含 pyproject.toml 文件的目录"""
	for pyproject_path in root_dir.rglob("pyproject.toml"):
		yield pyproject_path.parent


remove_files = [filepath_to_slash(item) for item in ["pyproject.toml", "uv.lock", ]]

edit_files = [filepath_to_slash(item) for item in ["pyproject.toml", "uv.lock", ]]

read_files = [filepath_to_slash(item) for item in ["go.sum", "uv.lock", ]]


def handle_stop() -> tuple[bool, Path | None, str | None]:
	"""
		1. 遍历所有存在 pyproject.toml 文件的目录
		2. 检查 lib、scripts 和 .claude/scripts 目录
		3. 在每一个目录执行 `uvx ruff check`
		4. 返回 (success, failed_dir, error_output)
	"""
	cwd = Path.cwd()
	root_dir = cwd.joinpath("plugins")
	found_any = False

	# 检查 plugins 目录下所有有 pyproject.toml 的目录
	for dir_path in _iter_pyproject_dirs(root_dir):
		found_any = True
		# 1. ruff 检查
		try:
			result = subprocess.run(["uvx", "ruff", "check"], cwd=dir_path, capture_output=True, text=True, )
			if result.returncode != 0:
				error_output = result.stderr or result.stdout
				return False, dir_path, error_output.strip()
		except Exception as e:
			logging.error(f"执行 ruff check 失败: {e}")
			return False, dir_path, str(e)

		if dir_path.name.find("semantic") >= 0:
			continue

		# 2. 检查 main.py --help（如果存在）
		main_py = dir_path / "scripts" / "main.py"
		if main_py.exists():
			try:
				result = subprocess.run(["uv", "run", "./scripts/main.py", "--help"], cwd=dir_path, capture_output=True,
				                        text=True, timeout=30, )
				if result.returncode != 0:
					error_output = result.stderr or result.stdout
					return False, dir_path, f"main.py --help 失败:\n{error_output.strip()}"
			except subprocess.TimeoutExpired:
				return False, dir_path, "main.py --help 超时"
			except Exception as e:
				logging.error(f"执行 main.py --help 失败: {e}")
				return False, dir_path, str(e)

	# 检查 lib 目录
	lib_dir = cwd.joinpath("lib")
	if lib_dir.exists():
		found_any = True
		try:
			result = subprocess.run(["uvx", "ruff", "check"], cwd=lib_dir, capture_output=True, text=True, )
			if result.returncode != 0:
				error_output = result.stderr or result.stdout
				return False, lib_dir, error_output.strip()
		except Exception as e:
			logging.error(f"执行 ruff check 失败: {e}")
			return False, lib_dir, str(e)

	# 检查 scripts 目录
	scripts_dir = cwd.joinpath("scripts")
	if scripts_dir.exists():
		found_any = True
		try:
			result = subprocess.run(["uvx", "ruff", "check"], cwd=scripts_dir, capture_output=True, text=True, )
			if result.returncode != 0:
				error_output = result.stderr or result.stdout
				return False, scripts_dir, error_output.strip()
		except Exception as e:
			logging.error(f"执行 ruff check 失败: {e}")
			return False, scripts_dir, str(e)

	# 检查 .claude/scripts 目录
	claude_scripts = cwd.joinpath(".claude", "scripts")
	if claude_scripts.exists():
		found_any = True
		try:
			result = subprocess.run(["uvx", "ruff", "check"], cwd=claude_scripts, capture_output=True, text=True, )
			if result.returncode != 0:
				error_output = result.stderr or result.stdout
				return False, claude_scripts, error_output.strip()
		except Exception as e:
			logging.error(f"执行 ruff check 失败: {e}")
			return False, claude_scripts, str(e)

	if not found_any:
		logging.info("未找到任何需要检查的目录")
	return True, None, None


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

		if tool_name == "bash":
			if "command" in tool_input:
				command = tool_input.get("command", "")
				if command.find("rm") >= 0:
					for locked_file in remove_files:
						if command.find(locked_file) >= 0:
							logging.warn(f"检测到受保护文件操作: command={command}, locked_file={locked_file}")
							print(json.dumps({
								"hookSpecificOutput":
									{
										"hookEventName": "PreToolUse",
										"permissionDecision": "deny",
										"permissionDecisionReason": "危险警告，可能涉及修改受保护的文件",
										"updatedInput": tool_input
									}
							}))
							return
				elif command.find("pip install") >= 0:
					logging.warn(f"检测到 pip 操作: command={command}")
					print(json.dumps({
						"hookSpecificOutput": {
							"hookEventName": "PreToolUse",
							"permissionDecision": "deny",
							"permissionDecisionReason": "不允许执行 pip install, 请使用 `uv add` 命令",
							"updatedInput": tool_input,
						}
					}))
					return
				elif command.find("python") >= 0:
					if command.find("uv run python") < 0 or command.find("uv run ./") < 0:
						logging.warn(f"检测到 python 操作: command={command}")
						print(json.dumps({
							"hookSpecificOutput":
								{
									"hookEventName": "PreToolUse",
									"permissionDecision": "deny",
									"permissionDecisionReason": "危险警告，不允许使用 `python` 执行，必须使用 `uv run` 的方式运行",
									"updatedInput": tool_input,
								},
						}))
						return

		elif tool_name == "edit":
			if "file_path" in tool_input:
				file_path = tool_input.get("file_path", "")
				for locked_file in edit_files:
					if file_path.find(locked_file) >= 0:
						logging.warn(f"检测到受保护文件操作: file_path={file_path}, locked_file={locked_file}")
						print(json.dumps({
							"hookSpecificOutput": {
								"hookEventName": "PreToolUse",
								"permissionDecision": "deny",
								"permissionDecisionReason": "危险警告，可能涉及修改受保护文件",
								"updatedInput": tool_input
							}
						}))
						return
		elif tool_name == "read":
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
									"permissionDecisionReason": "危险警告，可能涉及读取受保护文件",
									"updatedInput": tool_input,
								}
						}))
						return

		print(json.dumps({
			"hookSpecificOutput":
				{
					"hookEventName": "PreToolUse",
					"permissionDecision": "allow",
					"updatedInput": tool_input
				}
		}))

	except Exception as e:
		logging.error(f"PreToolUse 处理异常: {e}\n{traceback.format_exc()}")


def main():
	"""主函数，捕获所有异常"""
	try:
		input_data = load_hooks()
		logging.info(f"Received input data: {input_data}")

		hook_event_name = input_data.get("hook_event_name", "")
		if not hook_event_name:
			logging.error("缺少 hook_event_name")
			print(json.dumps({"continue": True, "suppressOutput": False}))
			return

		# 路由到不同的处理器
		if hook_event_name == "Stop":
			success, failed_dir, error_output = handle_stop()
			if not success:
				reason = f"代码检查失败：目录 `{failed_dir}`\n\n{error_output}"
				print(json.dumps({"continue": True, "decision": "block", "reason": reason}))
		elif hook_event_name == "PreToolUse":
			handle_pre_tool_use(input_data)
		else:
			logging.warn(f"未知的 hook 事件: {hook_event_name}")

	except json.JSONDecodeError as e:
		logging.error(f"JSON 解析错误: {e}\n{traceback.format_exc()}")
	except Exception as e:
		logging.error(f"未捕获的异常: {e}\n{traceback.format_exc()}")


if __name__ == '__main__':
	main()