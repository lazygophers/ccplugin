#!/usr/bin/env python3
"""
Update enabled plugins using Claude's official plugin update command.

This script:
1. Gets enabled plugins via 'claude plugin list --json'
2. Updates marketplaces via 'claude plugin marketplace update' command
3. Uses 'claude plugin update' command to update all enabled plugins
4. Verifies all plugins are at latest versions after update
"""

import argparse
import json
import os
import random
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any

from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.progress import (
	Progress,
	SpinnerColumn,
	TextColumn,
	BarColumn,
	TaskProgressColumn,
	TimeElapsedColumn,
)
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from lib.utils.env import get_project_dir

LOADING_MESSAGES = [
	"🔍 正在搜索插件市场...",
	"📦 正在加载插件列表...",
	"🚀 正在获取最新数据...",
	"✨ 正在整理插件信息...",
	"🎯 正在匹配已安装插件...",
	"🌐 正在连接市场源...",
	"⚡ 正在加速数据传输...",
	"🔮 正在预测你的需求...",
	"🦄 正在召唤插件精灵...",
	"🌟 正在收集星光数据...",
	"🎭 正在准备精彩展示...",
	"🎪 正在搭建插件舞台...",
	"🔄 正在同步插件版本...",
	"💫 正在施展更新魔法...",
	"🎨 正在绘制更新蓝图...",
]


class NullConsole:
	"""A console that doesn't output anything."""

	def __getattr__(self, name: str) -> Any:
		"""Return a no-op function for any attribute access."""
		return lambda *args, **kwargs: None


console = Console()


def set_quiet_mode(quiet: bool) -> None:
	"""Set quiet mode on or off."""
	global console
	if quiet:
		console = NullConsole()
	else:
		console = Console()


def run_claude_command_with_progress(
	args: list[str],
	description: str = "正在执行命令",
) -> dict[str, Any] | list[Any] | None:
	"""Run a claude CLI command with animated progress bar.

	Args:
		args: Command arguments
		description: Initial description for progress bar

	Returns:
		Parsed JSON data or None if command fails
	"""
	with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
		temp_path = f.name

	result_container = {"done": False, "data": None}

	def run_command():
		try:
			proc = subprocess.run(
				["claude"] + args,
				stdout=open(temp_path, "w"),
				stderr=subprocess.PIPE,
				text=True,
				cwd=get_project_dir(),
			)
			if proc.returncode == 0:
				with open(temp_path, "r", encoding="utf-8") as f:
					content = f.read()
					if content.strip():
						result_container["data"] = json.loads(content)
		except (subprocess.CalledProcessError, json.JSONDecodeError, OSError):
			pass
		finally:
			result_container["done"] = True

	thread = threading.Thread(target=run_command)
	thread.start()

	with Progress(
		SpinnerColumn("dots", style="cyan"),
		TextColumn("[progress.description]{task.description}"),
		BarColumn(complete_style="cyan", finished_style="green"),
		TextColumn("[dim]{task.fields[emoji]}[/dim]"),
		console=console,
		transient=True,
	) as progress:
		task = progress.add_task(description, total=100, emoji="🎯")
		message_idx = 0

		while not result_container["done"]:
			if random.random() < 0.1:
				message_idx = (message_idx + 1) % len(LOADING_MESSAGES)
				progress.update(task, description=LOADING_MESSAGES[message_idx])

			current = progress.tasks[0].completed
			if current < 95:
				advance = random.uniform(0.5, 2.0)
				progress.advance(task, advance=advance)

			emojis = ["✨", "🌟", "💫", "⭐", "🔥", "💎", "🎯", "🚀"]
			progress.update(task, emoji=random.choice(emojis))

			time.sleep(0.1)

		progress.update(task, completed=100, description="✅ 完成!", emoji="🎉")

	thread.join()

	try:
		if os.path.exists(temp_path):
			os.unlink(temp_path)
	except OSError:
		pass

	return result_container["data"]


class UpdateStats:
	"""Statistics for the update process."""

	def __init__(self) -> None:
		self.updated_count = 0
		self.skipped_count = 0
		self.error_count = 0
		self.market_updated = 0
		self.market_failed = 0
		self.uv_sync_count = 0
		self.uv_sync_failed = 0
		self.messages: list[tuple[str, str]] = []
		self.version_mismatches: list[tuple[str, str, str]] = []

	def add_message(self, status: str, message: str) -> None:
		"""Add a message to the log."""
		self.messages.append((status, message))

	def add_mismatch(self, plugin_id: str, expected: str, actual: str) -> None:
		"""Add a version mismatch."""
		self.version_mismatches.append((plugin_id, expected, actual))

	def print_summary(self) -> None:
		"""Print a summary table of the update process."""
		console.print(Rule(title="[bold blue]Update Summary[/bold blue]", style="blue"))

		summary_table = Table(
			show_header=False,
			box=box.ROUNDED,
			padding=(0, 2),
		)
		summary_table.add_column("Category", style="bold")
		summary_table.add_column("Status", justify="right")

		summary_table.add_row(
			"📦 Marketplaces Updated",
			f"[green]{self.market_updated}[/green]",
		)
		if self.market_failed > 0:
			summary_table.add_row(
				"❌ Marketplaces Failed",
				f"[red]{self.market_failed}[/red]",
			)
		summary_table.add_row(
			"✅ Plugins Updated",
			f"[green]{self.updated_count}[/green]",
		)
		summary_table.add_row(
			"⏭️  Plugins Skipped",
			f"[yellow]{self.skipped_count}[/yellow]",
		)
		if self.error_count > 0:
			summary_table.add_row(
				"❌ Errors",
				f"[red bold]{self.error_count}[/red bold]",
			)
		if self.uv_sync_count > 0:
			summary_table.add_row(
				"🔄 UV Sync Completed",
				f"[green]{self.uv_sync_count}[/green]",
			)
		if self.uv_sync_failed > 0:
			summary_table.add_row(
				"❌ UV Sync Failed",
				f"[red]{self.uv_sync_failed}[/red]",
			)
		if self.version_mismatches:
			summary_table.add_row(
				"⚠️  Version Mismatches",
				f"[yellow bold]{len(self.version_mismatches)}[/yellow bold]",
			)

		console.print(summary_table)

		if self.version_mismatches:
			console.print()
			console.print(Rule(title="[bold yellow]Version Mismatches[/bold yellow]", style="yellow"))
			mismatch_table = Table(
				show_header=True,
				header_style="bold yellow",
				box=box.ROUNDED,
			)
			mismatch_table.add_column("Plugin", style="cyan")
			mismatch_table.add_column("Expected", style="green")
			mismatch_table.add_column("Actual", style="red")
			for plugin_id, expected, actual in self.version_mismatches:
				mismatch_table.add_row(plugin_id, expected, actual)
			console.print(mismatch_table)

		if self.messages:
			console.print()
			console.print(Rule(title="[bold]Details[/bold]", style="dim"))
			for status, msg in self.messages:
				if status == "error":
					console.print(f"  [red]✗[/red] {msg}")
				elif status == "warning":
					console.print(f"  [yellow]⚠[/yellow] {msg}")
				elif status == "success":
					console.print(f"  [green]✓[/green] {msg}")
				elif status == "info":
					console.print(f"  [dim]ℹ[/dim] {msg}")


def get_enabled_plugins_list() -> list[dict[str, Any]]:
	"""Get all enabled plugins from 'claude plugin list --json'.

	Returns:
		List of enabled plugin info dicts
	"""
	data = run_claude_command_with_progress(
		["plugin", "list", "--json"],
		description="🔍 正在获取已启用插件..."
	)

	if not isinstance(data, list):
		return []

	enabled_plugins = []
	seen_ids = set()

	for plugin in data:
		if plugin.get("enabled"):
			plugin_id = plugin.get("id", "")
			if plugin_id and plugin_id not in seen_ids:
				seen_ids.add(plugin_id)
				enabled_plugins.append(plugin)

	return enabled_plugins


def get_all_plugins_list() -> list[dict[str, Any]]:
	"""Get all plugins (including disabled) from 'claude plugin list --json'.

	Returns:
		List of all plugin info dicts
	"""
	data = run_claude_command_with_progress(
		["plugin", "list", "--json"],
		description="🔍 正在获取所有插件..."
	)

	if not isinstance(data, list):
		return []

	all_plugins = []
	seen_ids = set()

	for plugin in data:
		plugin_id = plugin.get("id", "")
		if plugin_id and plugin_id not in seen_ids:
			seen_ids.add(plugin_id)
			all_plugins.append(plugin)

	return all_plugins


def get_latest_versions_from_marketplace() -> dict[str, str]:
	"""Get latest available versions for all plugins from marketplace.

	Returns:
		Dict mapping plugin_id to latest version string
	"""
	data = run_claude_command_with_progress(
		["plugin", "list", "--json", "--all"],
		description="🌐 正在获取最新版本信息..."
	)

	if not isinstance(data, list):
		return {}

	latest_versions: dict[str, str] = {}
	for plugin in data:
		plugin_id = plugin.get("id", "")
		version = plugin.get("version", "")
		if plugin_id and version:
			if plugin_id not in latest_versions:
				latest_versions[plugin_id] = version

	return latest_versions


def run_claude_plugin_update(
	plugin_key: str,
	dry_run: bool = False,
) -> tuple[bool, str]:
	"""Run 'claude plugin update' command for a specific plugin.

	Args:
		plugin_key: Plugin key in format 'plugin@market'
		dry_run: If True, show what would be done without making changes

	Returns:
		Tuple of (success, output) where success is True if command succeeded
	"""
	cmd = ["claude", "plugin", "update", plugin_key]

	if dry_run:
		console.print(f"[dim][DRY RUN] Would run: {' '.join(cmd)}[/dim]")
		return True, ""

	result = subprocess.run(
		cmd,
		cwd=get_project_dir(),
		stdout=subprocess.PIPE,
		stderr=subprocess.STDOUT,
		text=True,
	)

	return result.returncode == 0, result.stdout


def get_marketplace_list() -> list[dict[str, str]]:
	"""Get list of installed marketplaces using 'claude plugin marketplace list --json'.

	Returns:
		List of marketplace info dicts with keys: name, source, url, installLocation
	"""
	data = run_claude_command_with_progress(
		["plugin", "marketplace", "list", "--json"],
		description="📦 正在获取市场列表..."
	)

	if isinstance(data, list):
		return data
	return []


def update_marketplace(market: str, stats: UpdateStats, dry_run: bool = False) -> bool:
	"""Update marketplace using 'claude plugin marketplace update' command.

	Args:
		market: Marketplace name
		stats: Statistics object to track results
		dry_run: If True, show what would be done without making changes

	Returns:
		True if successful, False otherwise
	"""
	if dry_run:
		console.print(f"[dim][DRY RUN] Would run: claude plugin marketplace update {market}[/dim]")
		return True

	result = subprocess.run(
		["claude", "plugin", "marketplace", "update", market],
		cwd=get_project_dir(),
		stdout=subprocess.PIPE,
		stderr=subprocess.STDOUT,
		text=True,
	)

	if result.returncode != 0:
		stats.market_failed += 1
		return False

	stats.market_updated += 1
	return True


def parse_plugin_key(key: str) -> tuple[str, str] | None:
	"""Parse plugin key in format 'plugin@market'.

	Args:
		key: Plugin key string

	Returns:
		Tuple of (plugin, market) or None if invalid format
	"""
	if "@" not in key:
		return None

	parts = key.split("@")
	if len(parts) != 2:
		return None

	plugin, market = parts
	if not plugin or not market:
		return None

	return plugin, market


def run_uv_sync(plugin_path: str, plugin_name: str, stats: UpdateStats, dry_run: bool = False) -> bool:
	"""Run 'uv sync' in plugin directory if pyproject.toml exists.

	Args:
		plugin_path: Path to plugin directory
		plugin_name: Name of the plugin for display
		stats: Statistics object to track results
		dry_run: If True, show what would be done without making changes

	Returns:
		True if uv sync was executed successfully or skipped, False on error
	"""
	from pathlib import Path

	plugin_dir = Path(plugin_path)
	pyproject_path = plugin_dir / "pyproject.toml"

	if not pyproject_path.exists():
		return True

	if dry_run:
		console.print(f"[dim][DRY RUN] Would run: uv sync in {plugin_dir}[/dim]")
		return True

	result = subprocess.run(
		["uv", "sync"],
		cwd=plugin_dir,
		stdout=subprocess.PIPE,
		stderr=subprocess.STDOUT,
		text=True,
	)

	if result.returncode == 0:
		stats.uv_sync_count += 1
		stats.add_message("success", f"uv sync completed for [cyan]{plugin_name}[/cyan] [dim]({plugin_dir.name})[/dim]")
		return True
	else:
		stats.uv_sync_failed += 1
		stats.add_message("error", f"uv sync failed for {plugin_name}: {result.stdout.strip()}")
		return False


def enable_plugin(plugin_id: str, dry_run: bool = False) -> bool:
	"""Enable a plugin using 'claude plugin enable' command.

	Args:
		plugin_id: Plugin ID in format 'plugin@market'
		dry_run: If True, show what would be done without making changes

	Returns:
		True if successful, False otherwise
	"""
	if dry_run:
		console.print(f"[dim][DRY RUN] Would run: claude plugin enable {plugin_id}[/dim]")
		return True

	result = subprocess.run(
		["claude", "plugin", "enable", plugin_id],
		stdout=subprocess.PIPE,
		stderr=subprocess.STDOUT,
		text=True,
	)

	return result.returncode == 0


def create_plugin_table(plugins: list[dict[str, Any]]) -> Table:
	"""Create a rich table for displaying plugins."""
	table = Table(
		title="[bold]Enabled Plugins[/bold]",
		show_header=True,
		header_style="bold cyan",
		box=box.ROUNDED,
		pad_edge=False,
	)
	table.add_column("Plugin", style="green", no_wrap=True)
	table.add_column("Market", style="blue", no_wrap=True)
	table.add_column("Scope", style="cyan", justify="center")
	table.add_column("Version", style="yellow", justify="right")

	for plugin in plugins:
		plugin_id = plugin.get("id", "")
		parsed = parse_plugin_key(plugin_id)
		if parsed:
			plugin_name, market = parsed
			scope = plugin.get("scope", "unknown")
			version = plugin.get("version", "-")
			if scope == "user":
				scope_display = "[cyan]user[/cyan]"
			else:
				scope_display = "[magenta]project[/magenta]"
			table.add_row(plugin_name, market, scope_display, version)

	return table


def verify_versions(
	enabled_plugins: list[dict[str, Any]],
	latest_versions: dict[str, str],
	stats: UpdateStats,
) -> bool:
	"""Verify all enabled plugins are at latest versions.

	Args:
		enabled_plugins: List of enabled plugin info dicts
		latest_versions: Dict of plugin_id -> latest version
		stats: Statistics object to track mismatches

	Returns:
		True if all versions match, False otherwise
	"""
	all_match = True

	for plugin in enabled_plugins:
		plugin_id = plugin.get("id", "")
		current_version = plugin.get("version", "")
		latest_version = latest_versions.get(plugin_id, "")

		if latest_version and current_version != latest_version:
			stats.add_mismatch(plugin_id, latest_version, current_version)
			all_match = False

	return all_match


def main() -> int:
	parser = argparse.ArgumentParser(
		prog="update.py",
		description="🔌 CCPlugin 插件更新工具 - 使用 Claude 官方命令更新已启用的插件",
		add_help=False,
	)
	parser.add_argument(
		"--dry-run",
		action="store_true",
		help="模拟运行，仅显示将要执行的操作",
	)
	parser.add_argument(
		"--quiet",
		action="store_true",
		help="静默模式，不输出任何信息",
	)
	parser.add_argument(
		"--no-market-update",
		action="store_true",
		help="跳过市场更新（更快，但可能使用过时数据）",
	)
	parser.add_argument(
		"--no-verify",
		action="store_true",
		help="跳过更新后的版本验证",
	)
	parser.add_argument(
		"--auto-enable",
		action="store_true",
		help="自动启用被禁用的插件",
	)
	parser.add_argument(
		"--no-uv-sync",
		action="store_true",
		help="跳过插件目录的 uv sync 操作",
	)
	parser.add_argument(
		"-h", "--help",
		action="store_true",
		help="显示帮助信息",
	)

	args = parser.parse_args()

	if args.help:
		from lib.utils import print_help
		print_help(parser, console)
		return 0

	set_quiet_mode(args.quiet)

	console.print(
		Panel.fit(
			"[bold cyan]🔌 Plugin Update Tool[/bold cyan]\n"
			f"[dim]Project:[/dim] [white]{get_project_dir()}[/white]",
			border_style="blue",
			box=box.DOUBLE,
		)
	)
	console.print()

	stats = UpdateStats()

	if args.auto_enable:
		console.print(Rule(title="[bold cyan]Auto-Enabling Plugins[/bold cyan]", style="cyan"))
		all_plugins = get_all_plugins_list()
		disabled_plugins = [p for p in all_plugins if not p.get("enabled")]

		if disabled_plugins:
			console.print(f"[yellow]Found {len(disabled_plugins)} disabled plugin(s)[/yellow]")
			with Progress(
				SpinnerColumn(spinner_name="dots"),
				TextColumn("[progress.description]{task.description}"),
				BarColumn(bar_width=40, complete_style="green", finished_style="bold green"),
				TaskProgressColumn(),
				TimeElapsedColumn(),
				console=console,
				disable=args.quiet,
			) as progress:
				task = progress.add_task("[cyan]Enabling plugins...[/cyan]", total=len(disabled_plugins))
				for plugin in disabled_plugins:
					plugin_id = plugin.get("id", "")
					plugin_name = plugin_id.split("@")[0] if plugin_id else "unknown"
					progress.update(task, description=f"[cyan]Enabling {plugin_name}...[/cyan]")
					if enable_plugin(plugin_id, dry_run=args.dry_run):
						stats.add_message("success", f"Enabled plugin: {plugin_name}")
					else:
						stats.add_message("error", f"Failed to enable plugin: {plugin_name}")
					progress.advance(task)
			console.print()
		else:
			console.print("[green]All plugins are already enabled[/green]")
			console.print()

	enabled_plugins = get_enabled_plugins_list()

	plugin_count_text = Text()
	plugin_count_text.append("Found ")
	plugin_count_text.append(str(len(enabled_plugins)), style="bold green")
	plugin_count_text.append(" enabled plugin(s)")
	console.print(plugin_count_text)
	console.print()

	if not enabled_plugins:
		console.print(Panel(
			"[yellow]No enabled plugins found[/yellow]",
			border_style="yellow",
			box=box.ROUNDED,
		))
		return 0

	console.print(create_plugin_table(enabled_plugins))
	console.print()

	marketplaces = get_marketplace_list()
	market_count_text = Text()
	market_count_text.append("Found ")
	market_count_text.append(str(len(marketplaces)), style="bold blue")
	market_count_text.append(" marketplace(s)")
	console.print(market_count_text)
	console.print()

	if marketplaces and not args.no_market_update:
		console.print(Rule(title="[bold cyan]Updating Marketplaces[/bold cyan]", style="cyan"))
		with Progress(
			SpinnerColumn(spinner_name="dots"),
			TextColumn("[progress.description]{task.description}"),
			BarColumn(bar_width=40, complete_style="green", finished_style="bold green"),
			TaskProgressColumn(),
			TimeElapsedColumn(),
			console=console,
			disable=args.quiet,
		) as progress:
			task = progress.add_task("[cyan]Updating markets...[/cyan]", total=len(marketplaces))
			for marketplace in marketplaces:
				market_name = marketplace.get("name", "unknown")
				progress.update(task, description=f"[cyan]Updating {market_name}...[/cyan]")
				update_marketplace(market_name, stats, dry_run=args.dry_run)
				progress.advance(task)
		console.print()

	console.print(Rule(title="[bold cyan]Updating Plugins[/bold cyan]", style="cyan"))
	console.print("[dim]Using 'claude plugin update' command[/dim]")
	console.print()

	update_outputs: list[tuple[str, bool, str]] = []

	with Progress(
		SpinnerColumn(spinner_name="dots"),
		TextColumn("[progress.description]{task.description}"),
		BarColumn(bar_width=40, complete_style="green", finished_style="bold green"),
		TaskProgressColumn(),
		TimeElapsedColumn(),
		console=console,
		disable=args.quiet,
	) as progress:
		task = progress.add_task("[cyan]Updating plugins...[/cyan]", total=len(enabled_plugins))

		for plugin in enabled_plugins:
			plugin_id = plugin.get("id", "")
			plugin_name = plugin_id.split("@")[0] if plugin_id else "unknown"
			progress.update(task, description=f"[cyan]Updating {plugin_name}...[/cyan]")

			success, output = run_claude_plugin_update(plugin_id, dry_run=args.dry_run)
			update_outputs.append((plugin_name, success, output))

			if success:
				stats.updated_count += 1
			else:
				stats.error_count += 1

			progress.advance(task)

	console.print()

	if update_outputs:
		console.print(Rule(title="[bold]Update Details[/bold]", style="dim"))
		for plugin_name, success, output in update_outputs:
			if output.strip():
				for line in output.strip().split("\n"):
					if line.strip():
						if success:
							console.print(f"  [dim]{line}[/dim]")
						else:
							console.print(f"  [red]{line}[/red]")
		console.print()

	if not args.no_uv_sync and not args.dry_run:
		console.print(Rule(title="[bold cyan]Running UV Sync[/bold cyan]", style="cyan"))
		console.print("[dim]Checking for pyproject.toml in plugin directories...[/dim]")
		console.print()

		plugins_with_pyproject = []
		for plugin in enabled_plugins:
			install_path = plugin.get("installPath", "")
			plugin_id = plugin.get("id", "")
			if install_path:
				from pathlib import Path
				plugin_dir = Path(install_path)
				pyproject_path = plugin_dir / "pyproject.toml"
				if pyproject_path.exists():
					plugins_with_pyproject.append((plugin_id, install_path))

		if plugins_with_pyproject:
			console.print(f"[cyan]Found {len(plugins_with_pyproject)} plugin(s) with pyproject.toml[/cyan]")
			console.print()

			with Progress(
				SpinnerColumn(spinner_name="dots"),
				TextColumn("[progress.description]{task.description}"),
				BarColumn(bar_width=40, complete_style="green", finished_style="bold green"),
				TaskProgressColumn(),
				TimeElapsedColumn(),
				console=console,
				disable=args.quiet,
			) as progress:
				task = progress.add_task("[cyan]Running uv sync...[/cyan]", total=len(plugins_with_pyproject))
				for plugin_id, install_path in plugins_with_pyproject:
					plugin_name = plugin_id.split("@")[0] if plugin_id else "unknown"
					progress.update(task, description=f"[cyan]Syncing {plugin_name}...[/cyan]")
					run_uv_sync(install_path, plugin_name, stats, dry_run=args.dry_run)
					progress.advance(task)
			console.print()
		else:
			console.print("[dim]No plugins with pyproject.toml found[/dim]")
			console.print()

	if not args.no_verify and not args.dry_run:
		console.print(Rule(title="[bold cyan]Verifying Versions[/bold cyan]", style="cyan"))

		latest_versions = get_latest_versions_from_marketplace()
		enabled_plugins = get_enabled_plugins_list()

		if verify_versions(enabled_plugins, latest_versions, stats):
			console.print("[green]✓ All plugins are at latest versions[/green]")
		else:
			console.print(f"[yellow]⚠ Found {len(stats.version_mismatches)} plugin(s) with version mismatches[/yellow]")

		console.print()

	stats.print_summary()

	if stats.version_mismatches:
		console.print()
		console.print(Panel(
			"[yellow]Some plugins may need manual update. Try running 'update' again or check the marketplace.[/yellow]",
			border_style="yellow",
			box=box.ROUNDED,
		))
		return 1

	return 0 if stats.error_count == 0 else 1


if __name__ == "__main__":
	sys.exit(main())
