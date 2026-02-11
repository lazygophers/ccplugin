#!/usr/bin/env python3
"""
Update enabled plugins using Claude's official plugin update command.

This script:
1. Reads system (user scope) plugins via 'claude plugin list'
2. Reads project plugins from .claude/settings.json and .claude/settings.local.json
3. Merges system and project plugins
4. Optionally updates marketplaces via git pull
5. Uses 'claude plugin update' command to update all enabled plugins
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
	Progress,
	SpinnerColumn,
	TextColumn,
	BarColumn,
	TaskProgressColumn,
)
from rich.table import Table


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
		console = NullConsole()  # type: ignore
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
		self.messages: list[tuple[str, str]] = []  # (status, message)

	def add_message(self, status: str, message: str) -> None:
		"""Add a message to the log."""
		self.messages.append((status, message))

	def print_summary(self) -> None:
		"""Print a summary table of the update process."""
		table = Table(
			title="[bold blue]Update Summary[/bold blue]",
			show_header=True,
			header_style="bold magenta",
		)
		table.add_column("Category", style="cyan", width=20)
		table.add_column("Count", justify="right", style="green")

		table.add_row("Marketplaces Updated", str(self.market_updated))
		if self.market_failed > 0:
			table.add_row("Marketplaces Failed", f"[red]{self.market_failed}[/red]")
		table.add_row("Plugins Updated", str(self.updated_count))
		table.add_row("Plugins Skipped", str(self.skipped_count))
		if self.error_count > 0:
			table.add_row("Errors", f"[red]{self.error_count}[/red]")

		console.print(table)

		if self.messages:
			console.print("\n[bold]Details:[/bold]")
			for status, msg in self.messages:
				if status == "error":
					console.print(f"  [red]✗[/red] {msg}")
				elif status == "warning":
					console.print(f"  [yellow]⚠[/yellow] {msg}")
				elif status == "success":
					console.print(f"  [green]✓[/green] {msg}")
				elif status == "info":
					console.print(f"  [dim]ℹ[/dim] {msg}")


def run_command(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
	"""Run a command and return the result.

	Args:
		cmd: Command and arguments to run
		cwd: Working directory for the command

	Returns:
		Completed process result
	"""
	return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)


def get_system_plugins() -> dict[str, bool]:
	"""Get system (user scope) enabled plugins from claude plugin list.

	Returns:
		Dictionary of enabled plugins (plugin@market -> bool)
	"""
	import tempfile

	try:
		# Use shell output redirection to avoid encoding issues
		with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
			temp_path = f.name

		# Run command with output redirection to file
		with open(temp_path, "w", encoding="utf-8") as f:
			result = subprocess.run(
				["claude", "plugin", "list", "--json"],
				stdout=f,
				stderr=subprocess.DEVNULL,
				check=False,
			)

		if result.returncode != 0:
			Path(temp_path).unlink(missing_ok=True)
			return {}

		# Read from temp file
		with open(temp_path, "r", encoding="utf-8") as f:
			plugins = json.load(f)

		# Clean up temp file
		Path(temp_path).unlink(missing_ok=True)

		system_plugins = {}

		for plugin in plugins:
			# Only include user scope plugins that are enabled
			if plugin.get("scope") == "user" and plugin.get("enabled"):
				plugin_id = plugin.get("id", "")
				if plugin_id and plugin_id not in system_plugins:
					system_plugins[plugin_id] = True

		return system_plugins
	except (json.JSONDecodeError, Exception):
		return {}


def run_claude_plugin_update(
	plugin_key: str,
	dry_run: bool = False,
	quiet: bool = False,
) -> bool:
	"""Run 'claude plugin update' command for a specific plugin.

	Args:
		plugin_key: Plugin key in format 'plugin@market'
		dry_run: If True, show what would be done without making changes
		quiet: If True, suppress output

	Returns:
		True if successful, False otherwise
	"""
	cmd = ["claude", "plugin", "update", plugin_key]

	if dry_run:
		console.print(f"[dim][DRY RUN] Would run: {' '.join(cmd)}[/dim]")
		return True

	result = subprocess.run(cmd, capture_output=True, text=True)

	if result.returncode == 0:
		return True
	else:
		error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
		if not quiet:
			console.print(f"[red]Error updating {plugin_key}:[/red] {error_msg}")
		return False


def read_settings_json(project_dir: Path) -> dict[str, bool]:
	"""Read enabledPlugins from .claude/settings.json.

	Args:
		project_dir: Path to the project directory

	Returns:
		Dictionary of enabled plugins (plugin@market -> bool)
	"""
	settings_path = project_dir / ".claude" / "settings.json"

	if not settings_path.exists():
		return {}

	with open(settings_path, "r", encoding="utf-8") as f:
		data = json.load(f)

	return data.get("enabledPlugins", {})


def read_settings_local_json(project_dir: Path) -> dict[str, bool]:
	"""Read enabledPlugins from .claude/settings.local.json.

	Args:
		project_dir: Path to the project directory

	Returns:
		Dictionary of enabled plugins (plugin@market -> bool)
	"""
	settings_local_path = project_dir / ".claude" / "settings.local.json"

	if not settings_local_path.exists():
		return {}

	with open(settings_local_path, "r", encoding="utf-8") as f:
		data = json.load(f)

	return data.get("enabledPlugins", {})


def get_enabled_plugins(project_dir: Path) -> dict[str, bool]:
	"""Read and merge enabledPlugins from settings.json and settings.local.json.

	Args:
		project_dir: Path to the project directory

	Returns:
		Dictionary of enabled plugins (plugin@market -> bool), merged and deduplicated
	"""
	enabled_plugins = read_settings_json(project_dir)
	local_plugins = read_settings_local_json(project_dir)

	# Merge: local plugins override
	enabled_plugins.update(local_plugins)

	return enabled_plugins


def get_marketplace_dir(market: str) -> Path:
	"""Get the marketplace directory path.

	Args:
		market: Marketplace name (e.g., 'ccplugin-market')

	Returns:
		Path to the marketplace directory
	"""
	return Path.home() / ".claude" / "plugins" / "marketplaces" / market


def update_marketplace(market: str, stats: UpdateStats) -> bool:
	"""Update marketplace via git pull.

	Args:
		market: Marketplace name
		stats: Statistics object to track results

	Returns:
		True if successful, False otherwise
	"""
	market_dir = get_marketplace_dir(market)

	if not market_dir.exists():
		stats.add_message("warning", f"Marketplace directory not found: {market_dir}")
		stats.market_failed += 1
		return False

	result = run_command(["git", "pull"], cwd=market_dir)

	if result.returncode != 0:
		stats.add_message(
			"error", f"Failed to update {market}: {result.stderr.strip()}"
		)
		stats.market_failed += 1
		run_command(["git", "rebase"], cwd=market_dir)
		return False

	stats.market_updated += 1
	return True


def read_marketplace_json(market: str) -> dict[str, Any] | None:
	"""Read marketplace.json from marketplace directory.

	Args:
		market: Marketplace name

	Returns:
		Marketplace data or None if not found
	"""
	market_dir = get_marketplace_dir(market)
	marketplace_json = market_dir / ".claude-plugin" / "marketplace.json"

	if not marketplace_json.exists():
		return None

	with open(marketplace_json, "r", encoding="utf-8") as f:
		return json.load(f)


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


def main() -> int:
	parser = argparse.ArgumentParser(
		description="Update enabled plugins using Claude's official plugin update command"
	)
	parser.add_argument(
		"project_path",
		nargs="?",
		type=Path,
		default=Path.cwd(),
		help="Path to the project directory (default: current directory)",
	)
	parser.add_argument(
		"--dry-run",
		action="store_true",
		help="Show what would be done without making changes",
	)
	parser.add_argument(
		"--quiet",
		action="store_true",
		help="Suppress all output",
	)
	parser.add_argument(
		"--no-market-update",
		action="store_true",
		help="Skip marketplace git pull (faster, but may use stale data)",
	)

	args = parser.parse_args()
	project_path = args.project_path.resolve()

	# Set quiet mode
	set_quiet_mode(args.quiet)

	# Print header
	console.print(
		Panel.fit(
			f"[bold cyan]Plugin Update Tool (Claude Official)[/bold cyan]\n"
			f"[dim]Project:[/dim] {project_path}",
			border_style="blue",
		)
	)

	stats = UpdateStats()

	# Read system (user scope) plugins
	system_plugins = get_system_plugins()
	console.print(f"[dim]Found {len(system_plugins)} system plugin(s)[/dim]")

	# Read project plugins from settings files
	project_plugins = get_enabled_plugins(project_path)
	console.print(f"[dim]Found {len(project_plugins)} project plugin(s)[/dim]")

	# Merge system and project plugins (project plugins take precedence)
	enabled_plugins = {**system_plugins, **project_plugins}

	if not enabled_plugins:
		console.print(
			"[yellow]No enabled plugins found in system or project settings[/yellow]"
		)
		return 0

	console.print(f"[dim]Total: {len(enabled_plugins)} unique plugin(s)[/dim]\n")

	# Display enabled plugins
	enabled_table = Table(
		title="[bold]Enabled Plugins[/bold]", show_header=True, header_style="bold cyan"
	)
	enabled_table.add_column("Plugin", style="green")
	enabled_table.add_column("Market", style="blue")
	enabled_table.add_column("Scope", style="cyan")
	enabled_table.add_column("Status", style="yellow")

	enabled_list = []
	for plugin_key, enabled in enabled_plugins.items():
		parsed = parse_plugin_key(plugin_key)
		if parsed:
			plugin, market = parsed
			scope = (
				"[cyan]System[/cyan]"
				if plugin_key in system_plugins and plugin_key not in project_plugins
				else "[magenta]Project[/magenta]"
				if plugin_key in project_plugins and plugin_key not in system_plugins
				else "[white]Both[/white]"
			)
			status = "[green]Enabled[/green]" if enabled else "[dim]Disabled[/dim]"
			enabled_table.add_row(plugin, market, scope, status)
			if enabled:
				enabled_list.append(plugin_key)

	console.print(enabled_table)
	console.print(f"[dim]Found {len(enabled_list)} enabled plugin(s)[/dim]\n")

	# Collect unique markets
	markets = set()
	for plugin_key in enabled_plugins:
		parsed = parse_plugin_key(plugin_key)
		if parsed:
			_, market = parsed
			markets.add(market)

	# Update marketplaces (optional)
	if markets and not args.no_market_update:
		if not args.quiet:
			console.print("[bold cyan]Updating Marketplaces[/bold cyan]")
		with Progress(
			SpinnerColumn(),
			TextColumn("[progress.description]{task.description}"),
			BarColumn(),
			TaskProgressColumn(),
			console=console,
			disable=args.quiet,
		) as progress:
			if not args.quiet:
				task = progress.add_task(
					"[cyan]Updating markets...[/cyan]", total=len(markets)
				)
				for market in sorted(markets):
					progress.update(task, description=f"[cyan]Updating {market}...[/cyan]")
					update_marketplace(market, stats)
					progress.advance(task)
			else:
				for market in sorted(markets):
					update_marketplace(market, stats)
		if not args.quiet:
			console.print()

	# Update plugins using Claude's official command
	console.print("[bold cyan]Updating Plugins[/bold cyan]")
	console.print("[dim]Using 'claude plugin update' command[/dim]\n")

	if not args.quiet:
		with Progress(
			SpinnerColumn(),
			TextColumn("[progress.description]{task.description}"),
			BarColumn(),
			TaskProgressColumn(),
			console=console,
			disable=args.quiet,
		) as progress:
			task = progress.add_task(
				"[cyan]Updating plugins...[/cyan]", total=len(enabled_list)
			)

			for plugin_key in enabled_list:
				plugin = plugin_key.split("@")[0]
				progress.update(task, description=f"[cyan]Updating {plugin}...[/cyan]")

				if run_claude_plugin_update(plugin_key, dry_run=args.dry_run, quiet=args.quiet):
					stats.updated_count += 1
				else:
					stats.error_count += 1

				progress.advance(task)
	else:
		# Quiet mode: update without progress bar
		for plugin_key in enabled_list:
			if run_claude_plugin_update(plugin_key, dry_run=args.dry_run, quiet=args.quiet):
				stats.updated_count += 1
			else:
				stats.error_count += 1

	# Print summary
	console.print()
	stats.print_summary()

	return 0 if stats.error_count == 0 else 1


if __name__ == "__main__":
	sys.exit(main())