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
import subprocess
import sys
import tempfile
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
from rich.status import Status
from rich.table import Table
from rich.text import Text

from lib.utils.env import get_project_dir


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


class UpdateStats:
	"""Statistics for the update process."""

	def __init__(self) -> None:
		self.updated_count = 0
		self.skipped_count = 0
		self.error_count = 0
		self.market_updated = 0
		self.market_failed = 0
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
	try:
		with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
			tmpfile = f.name

		try:
			with open(tmpfile, "w") as f:
				result = subprocess.run(
					["claude", "plugin", "list", "--json"],
					stdout=f,
					stderr=subprocess.PIPE,
					text=True,
					cwd=get_project_dir(),
				)

			if result.returncode != 0:
				return []

			with open(tmpfile, "r") as f:
				plugins = json.load(f)

			enabled_plugins = []
			seen_ids = set()

			for plugin in plugins:
				if plugin.get("enabled"):
					plugin_id = plugin.get("id", "")
					if plugin_id and plugin_id not in seen_ids:
						seen_ids.add(plugin_id)
						enabled_plugins.append(plugin)

			return enabled_plugins

		finally:
			os.unlink(tmpfile)

	except (json.JSONDecodeError, Exception):
		return []


def get_latest_versions_from_marketplace() -> dict[str, str]:
	"""Get latest available versions for all plugins from marketplace.

	Returns:
		Dict mapping plugin_id to latest version string
	"""
	try:
		with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
			tmpfile = f.name

		try:
			with open(tmpfile, "w") as f:
				result = subprocess.run(
					["claude", "plugin", "list", "--json", "--all"],
					stdout=f,
					stderr=subprocess.PIPE,
					text=True,
					cwd=get_project_dir(),
				)

			if result.returncode != 0:
				return {}

			with open(tmpfile, "r") as f:
				all_plugins = json.load(f)

			latest_versions: dict[str, str] = {}
			for plugin in all_plugins:
				plugin_id = plugin.get("id", "")
				version = plugin.get("version", "")
				if plugin_id and version:
					if plugin_id not in latest_versions:
						latest_versions[plugin_id] = version

			return latest_versions

		finally:
			os.unlink(tmpfile)

	except (json.JSONDecodeError, Exception):
		return {}


def run_claude_plugin_update(
	plugin_key: str,
	dry_run: bool = False,
) -> bool:
	"""Run 'claude plugin update' command for a specific plugin.

	Args:
		plugin_key: Plugin key in format 'plugin@market'
		dry_run: If True, show what would be done without making changes

	Returns:
		True if successful, False otherwise
	"""
	cmd = ["claude", "plugin", "update", plugin_key]

	if dry_run:
		console.print(f"[dim][DRY RUN] Would run: {' '.join(cmd)}[/dim]")
		return True

	result = subprocess.run(cmd, cwd=get_project_dir())

	return result.returncode == 0


def get_marketplace_list() -> list[dict[str, str]]:
	"""Get list of installed marketplaces using 'claude plugin marketplace list --json'.

	Returns:
		List of marketplace info dicts with keys: name, source, url, installLocation
	"""
	try:
		with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
			tmpfile = f.name

		try:
			with open(tmpfile, "w") as f:
				result = subprocess.run(
					["claude", "plugin", "marketplace", "list", "--json"],
					stdout=f,
					stderr=subprocess.PIPE,
					text=True,
					cwd=get_project_dir(),
				)

			if result.returncode != 0:
				return []

			with open(tmpfile, "r") as f:
				return json.load(f)

		finally:
			os.unlink(tmpfile)

	except (json.JSONDecodeError, Exception):
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

	result = subprocess.run(["claude", "plugin", "marketplace", "update", market], cwd=get_project_dir())

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

	with Status("[bold cyan]Fetching enabled plugins...[/bold cyan]", console=console, spinner="dots"):
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

			if run_claude_plugin_update(plugin_id, dry_run=args.dry_run):
				stats.updated_count += 1
			else:
				stats.error_count += 1

			progress.advance(task)

	console.print()

	if not args.no_verify and not args.dry_run:
		console.print(Rule(title="[bold cyan]Verifying Versions[/bold cyan]", style="cyan"))

		with Status("[bold cyan]Fetching latest versions...[/bold cyan]", console=console, spinner="dots"):
			latest_versions = get_latest_versions_from_marketplace()

		with Status("[bold cyan]Verifying installed versions...[/bold cyan]", console=console, spinner="dots"):
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
