#!/usr/bin/env python3
"""Plugin validation script for single plugin.

Validates:
1. Plugin structure and required files
2. Plugin configuration correctness
3. Hook input testing (if hooks.py exists)

Usage:
  cd /path/to/plugin
  uv run /path/to/check.py

  Or specify plugin path:
  uv run /path/to/check.py -d /path/to/plugin
"""

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

from lib.utils import print_help

console = Console()

VALID_HOOK_EVENTS = frozenset({
	"PreToolUse",
	"PostToolUse",
	"PostToolUseFailure",
	"PermissionRequest",
	"UserPromptSubmit",
	"Notification",
	"Stop",
	"SubagentStart",
	"SubagentStop",
	"SessionStart",
	"SessionEnd",
	"PreCompact",
})

HOOK_EVENT_SAMPLES = {
	"SessionStart": {
		"session_id": "test-session-123",
		"transcript_path": "/tmp/transcript.jsonl",
		"permission_mode": "default",
		"hook_event_name": "SessionStart",
		"source": "startup"
	},
	"SessionEnd": {
		"session_id": "test-session-123",
		"transcript_path": "/tmp/transcript.jsonl",
		"cwd": "/current/working/directory",
		"permission_mode": "default",
		"hook_event_name": "SessionEnd",
		"reason": "other"
	},
	"UserPromptSubmit": {
		"session_id": "test-session-123",
		"transcript_path": "/tmp/transcript.jsonl",
		"cwd": "/current/working/directory",
		"permission_mode": "default",
		"hook_event_name": "UserPromptSubmit",
		"user_prompt": "test prompt"
	},
	"PreToolUse": {
		"session_id": "test-session-123",
		"transcript_path": "/tmp/transcript.jsonl",
		"cwd": "/current/working/directory",
		"permission_mode": "default",
		"hook_event_name": "PreToolUse",
		"tool_name": "Write",
		"tool_input": {
			"file_path": "/tmp/test.txt",
			"content": "test content"
		},
		"tool_use_id": "toolu_01ABC123"
	},
	"PostToolUse": {
		"session_id": "test-session-123",
		"transcript_path": "/tmp/transcript.jsonl",
		"cwd": "/current/working/directory",
		"permission_mode": "default",
		"hook_event_name": "PostToolUse",
		"tool_name": "Write",
		"tool_input": {
			"file_path": "/tmp/test.txt",
			"content": "test content"
		},
		"tool_result": {
			"success": True,
			"message": "File written successfully"
		},
		"tool_use_id": "toolu_01ABC123"
	},
	"PostToolUseFailure": {
		"session_id": "test-session-123",
		"transcript_path": "/tmp/transcript.jsonl",
		"cwd": "/current/working/directory",
		"permission_mode": "default",
		"hook_event_name": "PostToolUseFailure",
		"tool_name": "Write",
		"tool_input": {
			"file_path": "/tmp/test.txt",
			"content": "test content"
		},
		"error": "Write failed",
		"tool_use_id": "toolu_01ABC123"
	},
	"Notification": {
		"session_id": "test-session-123",
		"transcript_path": "/tmp/transcript.jsonl",
		"cwd": "/current/working/directory",
		"permission_mode": "default",
		"hook_event_name": "Notification",
		"message": "Claude needs your permission to use Bash",
		"notification_type": "permission_prompt"
	},
	"Stop": {
		"session_id": "test-session-123",
		"transcript_path": "/tmp/transcript.jsonl",
		"permission_mode": "default",
		"hook_event_name": "Stop",
		"stop_hook_active": True
	},
	"SubagentStart": {
		"session_id": "test-session-123",
		"transcript_path": "/tmp/transcript.jsonl",
		"hook_event_name": "SubagentStart",
		"subagent_type": "Task"
	},
	"SubagentStop": {
		"session_id": "test-session-123",
		"transcript_path": "/tmp/transcript.jsonl",
		"hook_event_name": "SubagentStop",
		"subagent_type": "Task"
	},
	"PermissionRequest": {
		"session_id": "test-session-123",
		"transcript_path": "/tmp/transcript.jsonl",
		"cwd": "/current/working/directory",
		"permission_mode": "default",
		"hook_event_name": "PermissionRequest",
		"tool_name": "Bash",
		"tool_input": {
			"command": "ls -la"
		},
		"message": "Permission required"
	},
	"PreCompact": {
		"session_id": "test-session-123",
		"transcript_path": "/tmp/transcript.jsonl",
		"permission_mode": "default",
		"hook_event_name": "PreCompact",
		"trigger": "manual",
		"custom_instructions": ""
	}
}

REQUIRED_PLUGIN_FIELDS = ["name", "version", "description"]
RECOMMENDED_PLUGIN_FIELDS = ["author", "license", "keywords"]


def expand_env_vars(text: str, plugin_path: Path) -> str:
	"""Expand environment variables in a string.

	Supports:
	- ${VAR} syntax
	- $VAR syntax
	- Special variables: CLAUDE_PLUGIN_ROOT, CLAUDE_PROJECT_DIR

	Args:
		text: String containing environment variables
		plugin_path: Path to plugin directory (for CLAUDE_PLUGIN_ROOT)

	Returns:
		String with environment variables expanded
	"""
	env_vars = {
		'CLAUDE_PLUGIN_ROOT': str(plugin_path),
		'CLAUDE_PROJECT_DIR': str(plugin_path),
	}

	env_vars.update(os.environ)

	def replace_var(match: re.Match) -> str:
		var_name = match.group(1) or match.group(2)
		return env_vars.get(var_name, match.group(0))

	text = re.sub(r'\$\{(\w+)\}', replace_var, text)
	text = re.sub(r'\$(\w+)(?![\w{])', replace_var, text)

	return text


def extract_hook_commands(hooks_config: list[dict[str, Any]], plugin_path: Path) -> list[str]:
	"""Extract and expand hook commands from hooks configuration.

	Args:
		hooks_config: List of hook configurations
		plugin_path: Path to plugin directory

	Returns:
		List of expanded commands
	"""
	commands = []

	for hook_item in hooks_config:
		hooks_list = hook_item.get("hooks", [])
		for hook in hooks_list:
			if hook.get("type") == "command":
				cmd = hook.get("command", "")
				expanded_cmd = expand_env_vars(cmd, plugin_path)
				commands.append(expanded_cmd)

	return commands


@dataclass
class CheckResult:
	"""Result of a single check."""
	category: str
	name: str
	status: str
	message: str
	details: Optional[str] = None


@dataclass
class PluginCheckReport:
	"""Complete check report for a plugin."""
	plugin_name: str
	plugin_path: Path
	results: list[CheckResult] = field(default_factory=list)

	@property
	def passed(self) -> int:
		return sum(1 for r in self.results if r.status == "pass")

	@property
	def warnings(self) -> int:
		return sum(1 for r in self.results if r.status == "warning")

	@property
	def errors(self) -> int:
		return sum(1 for r in self.results if r.status == "error")

	@property
	def skipped(self) -> int:
		return sum(1 for r in self.results if r.status == "skip")

	def add_result(self, result: CheckResult) -> None:
		self.results.append(result)


def load_json_file(path: Path) -> Optional[dict[str, Any]]:
	"""Load and parse a JSON file.

	Args:
		path: Path to JSON file

	Returns:
		Parsed JSON data or None if failed
	"""
	try:
		with open(path, 'r', encoding='utf-8') as f:
			return json.load(f)
	except json.JSONDecodeError:
		return None
	except FileNotFoundError:
		return None


def check_plugin_structure(plugin_path: Path, report: PluginCheckReport) -> None:
	"""Check plugin directory structure.

	Args:
		plugin_path: Path to plugin directory
		report: Check report to update
	"""
	plugin_json_path = plugin_path / '.claude-plugin' / 'plugin.json'

	if not plugin_json_path.exists():
		report.add_result(CheckResult(
			category="structure",
			name="plugin.json",
			status="error",
			message="plugin.json 不存在",
			details=f"期望路径: {plugin_json_path}"
		))
		return

	report.add_result(CheckResult(
		category="structure",
		name="plugin.json",
		status="pass",
		message="plugin.json 存在"
	))

	scripts_dir = plugin_path / 'scripts'
	if scripts_dir.exists():
		report.add_result(CheckResult(
			category="structure",
			name="scripts/",
			status="pass",
			message="scripts 目录存在"
		))

		hooks_py = scripts_dir / 'hooks.py'
		main_py = scripts_dir / 'main.py'

		if hooks_py.exists():
			report.add_result(CheckResult(
				category="structure",
				name="scripts/hooks.py",
				status="pass",
				message="hooks.py 存在"
			))
		else:
			report.add_result(CheckResult(
				category="structure",
				name="scripts/hooks.py",
				status="skip",
				message="hooks.py 不存在（可选）"
			))

		if main_py.exists():
			report.add_result(CheckResult(
				category="structure",
				name="scripts/main.py",
				status="pass",
				message="main.py 存在"
			))
		else:
			report.add_result(CheckResult(
				category="structure",
				name="scripts/main.py",
				status="warning",
				message="main.py 不存在"
			))
	else:
		report.add_result(CheckResult(
			category="structure",
			name="scripts/",
			status="warning",
			message="scripts 目录不存在"
		))

	skills_dir = plugin_path / 'skills'
	if skills_dir.exists():
		skill_mds = list(skills_dir.glob('**/SKILL.md'))
		if skill_mds:
			report.add_result(CheckResult(
				category="structure",
				name="skills/",
				status="pass",
				message=f"找到 {len(skill_mds)} 个 SKILL.md 文件"
			))
		else:
			report.add_result(CheckResult(
				category="structure",
				name="skills/",
				status="warning",
				message="skills 目录存在但无 SKILL.md 文件"
			))

	agents_dir = plugin_path / 'agents'
	if agents_dir.exists():
		agent_mds = list(agents_dir.glob('*.md'))
		if agent_mds:
			report.add_result(CheckResult(
				category="structure",
				name="agents/",
				status="pass",
				message=f"找到 {len(agent_mds)} 个 agent 文件"
			))

	commands_dir = plugin_path / 'commands'
	if commands_dir.exists():
		command_mds = list(commands_dir.glob('*.md'))
		if command_mds:
			report.add_result(CheckResult(
				category="structure",
				name="commands/",
				status="pass",
				message=f"找到 {len(command_mds)} 个 command 文件"
			))

	pyproject = plugin_path / 'pyproject.toml'
	if pyproject.exists():
		report.add_result(CheckResult(
			category="structure",
			name="pyproject.toml",
			status="pass",
			message="pyproject.toml 存在"
		))
	else:
		report.add_result(CheckResult(
			category="structure",
			name="pyproject.toml",
			status="skip",
			message="pyproject.toml 不存在（非 Python 插件）"
		))

	readme = plugin_path / 'README.md'
	if readme.exists():
		report.add_result(CheckResult(
			category="structure",
			name="README.md",
			status="pass",
			message="README.md 存在"
		))
	else:
		report.add_result(CheckResult(
			category="structure",
			name="README.md",
			status="warning",
			message="README.md 不存在"
		))

	llms_txt = plugin_path / 'llms.txt'
	if llms_txt.exists():
		report.add_result(CheckResult(
			category="structure",
			name="llms.txt",
			status="pass",
			message="llms.txt 存在"
		))
	else:
		report.add_result(CheckResult(
			category="structure",
			name="llms.txt",
			status="skip",
			message="llms.txt 不存在（可选）"
		))


def check_plugin_config(plugin_path: Path, report: PluginCheckReport) -> Optional[dict[str, Any]]:
	"""Check plugin.json configuration.

	Args:
		plugin_path: Path to plugin directory
		report: Check report to update

	Returns:
		Plugin JSON data or None if failed
	"""
	plugin_json_path = plugin_path / '.claude-plugin' / 'plugin.json'
	plugin_data = load_json_file(plugin_json_path)

	if plugin_data is None:
		report.add_result(CheckResult(
			category="config",
			name="JSON 语法",
			status="error",
			message="plugin.json JSON 解析失败"
		))
		return None

	report.add_result(CheckResult(
		category="config",
		name="JSON 语法",
		status="pass",
		message="JSON 语法正确"
	))

	for field_name in REQUIRED_PLUGIN_FIELDS:
		if field_name in plugin_data and plugin_data[field_name]:
			value = plugin_data[field_name]
			if isinstance(value, str) and len(value) > 50:
				value = value[:50] + "..."
			report.add_result(CheckResult(
				category="config",
				name=f"字段 {field_name}",
				status="pass",
				message=f"{field_name}: {value}"
			))
		else:
			report.add_result(CheckResult(
				category="config",
				name=f"字段 {field_name}",
				status="error",
				message=f"缺少必需字段: {field_name}"
			))

	for field_name in RECOMMENDED_PLUGIN_FIELDS:
		if field_name in plugin_data and plugin_data[field_name]:
			value = plugin_data[field_name]
			if isinstance(value, str) and len(value) > 50:
				value = value[:50] + "..."
			elif isinstance(value, list):
				value = f"[{len(value)} 项]"
			elif isinstance(value, dict):
				value = "{...}"
			report.add_result(CheckResult(
				category="config",
				name=f"字段 {field_name}",
				status="pass",
				message=f"{field_name}: {value}"
			))
		else:
			report.add_result(CheckResult(
				category="config",
				name=f"字段 {field_name}",
				status="warning",
				message=f"缺少推荐字段: {field_name}"
			))

	hooks = plugin_data.get("hooks", {})
	if hooks:
		for event_name in hooks.keys():
			if event_name in VALID_HOOK_EVENTS:
				report.add_result(CheckResult(
					category="config",
					name=f"Hook {event_name}",
					status="pass",
					message="Hook 事件配置正确"
				))
			else:
				report.add_result(CheckResult(
					category="config",
					name=f"Hook {event_name}",
					status="error",
					message=f"非法 Hook 事件类型: {event_name}（不在 Claude Code 官方文档中）"
				))

	return plugin_data


def test_hook_input(
	plugin_path: Path,
	plugin_data: Optional[dict[str, Any]],
	report: PluginCheckReport
) -> None:
	"""Test hook input for plugins with hooks.py.

	Args:
		plugin_path: Path to plugin directory
		plugin_data: Plugin JSON data
		report: Check report to update
	"""
	if plugin_data is None:
		report.add_result(CheckResult(
			category="hook_test",
			name="配置",
			status="error",
			message="无法测试 hooks（plugin.json 解析失败）"
		))
		return

	hooks_config = plugin_data.get("hooks", {})
	if not hooks_config:
		report.add_result(CheckResult(
			category="hook_test",
			name="配置",
			status="skip",
			message="plugin.json 中无 hooks 配置"
		))
		return

	for event_name, event_hooks in hooks_config.items():
		if event_name not in VALID_HOOK_EVENTS:
			report.add_result(CheckResult(
				category="hook_test",
				name=f"测试 {event_name}",
				status="error",
				message=f"非法 Hook 事件类型: {event_name}（不在 Claude Code 官方文档中）"
			))
			continue

		if event_name not in HOOK_EVENT_SAMPLES:
			report.add_result(CheckResult(
				category="hook_test",
				name=f"测试 {event_name}",
				status="warning",
				message=f"无测试样本数据: {event_name}"
			))
			continue

		commands = extract_hook_commands(event_hooks, plugin_path)
		if not commands:
			report.add_result(CheckResult(
				category="hook_test",
				name=f"测试 {event_name}",
				status="warning",
				message="未找到可执行的 hook 命令"
			))
			continue

		sample_input = HOOK_EVENT_SAMPLES[event_name]

		for cmd in commands:
			try:
				result = subprocess.run(
					cmd,
					shell=True,
					cwd=plugin_path,
					input=json.dumps(sample_input),
					capture_output=True,
					text=True,
					timeout=30,
					env={**os.environ,
					     'CLAUDE_PLUGIN_ROOT': str(plugin_path),
					     }
				)

				if result.returncode == 0:
					report.add_result(CheckResult(
						category="hook_test",
						name=f"测试 {event_name}",
						status="pass",
						message="Hook 执行成功",
						details=result.stdout[:200] if result.stdout else None
					))
				else:
					report.add_result(CheckResult(
						category="hook_test",
						name=f"测试 {event_name}",
						status="error",
						message=f"Hook 执行失败 (exit code: {result.returncode})",
						details=result.stderr[:200] if result.stderr else None
					))
			except subprocess.TimeoutExpired:
				report.add_result(CheckResult(
					category="hook_test",
					name=f"测试 {event_name}",
					status="error",
					message="Hook 执行超时"
				))
			except FileNotFoundError:
				report.add_result(CheckResult(
					category="hook_test",
					name=f"测试 {event_name}",
					status="error",
					message="命令未找到"
				))
			except Exception as e:
				report.add_result(CheckResult(
					category="hook_test",
					name=f"测试 {event_name}",
					status="error",
					message=f"Hook 测试异常: {str(e)}"
				))


def print_report(report: PluginCheckReport) -> None:
	"""Print a plugin check report.

	Args:
		report: Check report to print
	"""
	console.print()
	console.print(Panel.fit(
		f"[bold cyan]插件: {report.plugin_name}[/bold cyan]\n"
		f"[dim]路径: {report.plugin_path}[/dim]",
		border_style="blue",
		box=box.DOUBLE
	))

	categories = {}
	for result in report.results:
		if result.category not in categories:
			categories[result.category] = []
		categories[result.category].append(result)

	category_names = {
		"structure": "目录结构",
		"config": "配置检查",
		"hook_test": "Hook 测试"
	}

	for category, results in categories.items():
		console.print(Rule(title=f"[bold]{category_names.get(category, category)}[/bold]", style="cyan"))

		table = Table(show_header=True, header_style="bold", box=box.ROUNDED, padding=(0, 1))
		table.add_column("检查项", style="cyan", no_wrap=True)
		table.add_column("状态", justify="center", width=8)
		table.add_column("消息")

		for result in results:
			if result.status == "pass":
				status_display = "[green]✓ 通过[/green]"
			elif result.status == "warning":
				status_display = "[yellow]⚠ 警告[/yellow]"
			elif result.status == "error":
				status_display = "[red]✗ 错误[/red]"
			else:
				status_display = "[dim]○ 跳过[/dim]"

			table.add_row(result.name, status_display, result.message)

		console.print(table)

	console.print()

	total = len(report.results)
	if total > 0:
		pass_rate = report.passed / total * 100
		warning_rate = report.warnings / total * 100
		error_rate = report.errors / total * 100

		console.print(Rule(title="[bold]总体进度[/bold]", style="cyan"))

		progress_table = Table(show_header=False, box=box.ROUNDED, padding=(0, 2))
		progress_table.add_column("Label", style="bold")
		progress_table.add_column("Bar", width=50)
		progress_table.add_column("Percent", justify="right", width=8)

		if report.passed > 0:
			progress_table.add_row(
				"[green]✓ 通过[/green]",
				f"[green]{'█' * int(pass_rate / 2)}[/green][dim]{'░' * (50 - int(pass_rate / 2))}[/dim]",
				f"[green]{pass_rate:.1f}%[/green]"
			)

		if report.warnings > 0:
			progress_table.add_row(
				"[yellow]⚠ 警告[/yellow]",
				f"[yellow]{'█' * int(warning_rate / 2)}[/yellow][dim]{'░' * (50 - int(warning_rate / 2))}[/dim]",
				f"[yellow]{warning_rate:.1f}%[/yellow]"
			)

		if report.errors > 0:
			progress_table.add_row(
				"[red]✗ 错误[/red]",
				f"[red]{'█' * int(error_rate / 2)}[/red][dim]{'░' * (50 - int(error_rate / 2))}[/dim]",
				f"[red]{error_rate:.1f}%[/red]"
			)

		if report.skipped > 0:
			skip_rate = report.skipped / total * 100
			progress_table.add_row(
				"[dim]○ 跳过[/dim]",
				f"[dim]{'█' * int(skip_rate / 2)}[/dim][dim]{'░' * (50 - int(skip_rate / 2))}[/dim]",
				f"[dim]{skip_rate:.1f}%[/dim]"
			)

		console.print(progress_table)
		console.print()

	summary_table = Table(show_header=False, box=box.ROUNDED, padding=(0, 2))
	summary_table.add_column("Category", style="bold")
	summary_table.add_column("Count", justify="right")

	summary_table.add_row("✓ 通过", f"[green]{report.passed}[/green]")
	if report.warnings > 0:
		summary_table.add_row("⚠ 警告", f"[yellow]{report.warnings}[/yellow]")
	if report.errors > 0:
		summary_table.add_row("✗ 错误", f"[red]{report.errors}[/red]")
	if report.skipped > 0:
		summary_table.add_row("○ 跳过", f"[dim]{report.skipped}[/dim]")

	console.print(summary_table)


def main() -> int:
	"""Main entry point for plugin check script.

	Returns:
		Exit code (0 for success, 1 for errors)
	"""
	parser = argparse.ArgumentParser(
		prog="check.py",
		description="🔍 CCPlugin 插件校验工具 - 检查插件结构和配置是否正确",
		add_help=False,
	)
	parser.add_argument(
		"-d", "--dir",
		type=str,
		default=None,
		help="插件目录路径 (默认: 当前目录)",
		metavar="PATH",
	)
	parser.add_argument(
		"--skip-hooks",
		action="store_true",
		help="跳过 Hook 测试",
	)
	parser.add_argument(
		"-h", "--help",
		action="store_true",
		help="显示帮助信息",
	)

	args = parser.parse_args()

	if args.help:
		print_help(parser, console)
		return 0

	if args.dir:
		plugin_path = Path(args.dir).resolve()
	else:
		plugin_path = Path.cwd()

	plugin_json_path = plugin_path / '.claude-plugin' / 'plugin.json'
	if not plugin_json_path.exists():
		console.print(Panel.fit(
			"[bold red]错误: 指定的目录不是有效的插件目录[/bold red]\n"
			f"[dim]未找到: {plugin_json_path}[/dim]\n\n"
			"[dim]请使用 -d 参数指定插件目录，或在插件根目录执行此脚本[/dim]",
			border_style="red",
			box=box.DOUBLE
		))
		return 1

	report = PluginCheckReport(
		plugin_name=plugin_path.name,
		plugin_path=plugin_path
	)

	check_plugin_structure(plugin_path, report)
	plugin_data = check_plugin_config(plugin_path, report)

	if not args.skip_hooks:
		test_hook_input(plugin_path, plugin_data, report)

	print_report(report)

	console.print()
	if report.errors > 0:
		console.print(Panel.fit(
			f"[bold red]校验失败[/bold red]\n"
			f"错误: [red bold]{report.errors}[/red bold] | "
			f"警告: [yellow bold]{report.warnings}[/yellow bold]",
			border_style="red",
			box=box.DOUBLE
		))
		return 1
	else:
		msg = f"[bold green]校验通过[/bold green]"
		if report.warnings > 0:
			msg += f"\n警告: [yellow bold]{report.warnings}[/yellow bold]"
		console.print(Panel.fit(msg, border_style="green", box=box.DOUBLE))
		return 0


if __name__ == '__main__':
	exit(main())