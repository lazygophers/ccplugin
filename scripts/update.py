#!/usr/bin/env python3
"""
Update enabled plugins using Claude's official plugin update command.

This script:
1. Gets enabled plugins via 'claude plugin list --json'
2. Updates marketplaces via 'claude plugin marketplace update' command
3. Uses 'claude plugin update' command to update all enabled plugins
"""

import argparse
import json
import subprocess
import sys
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


def get_enabled_plugins_list() -> list[dict[str, Any]]:
	"""Get all enabled plugins from 'claude plugin list --json'.

	Returns:
		List of enabled plugin info dicts
	"""
	try:
		result = subprocess.run(
			["claude", "plugin", "list", "--json"],
			capture_output=True,
			text=True,
			check=False,
		)

		if result.returncode != 0:
			return []

		plugins = json.loads(result.stdout)

		enabled_plugins = []
		seen_ids = set()

		for plugin in plugins:
			if plugin.get("enabled"):
				plugin_id = plugin.get("id", "")
				if plugin_id and plugin_id not in seen_ids:
					seen_ids.add(plugin_id)
					enabled_plugins.append(plugin)

		return enabled_plugins

	except (json.JSONDecodeError, Exception):
		return []


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


def get_marketplace_list() -> list[dict[str, str]]:
	"""Get list of installed marketplaces using 'claude plugin marketplace list --json'.

	Returns:
		List of marketplace info dicts with keys: name, source, url, installLocation
	"""
	try:
		result = subprocess.run(
			["claude", "plugin", "marketplace", "list", "--json"],
			capture_output=True,
			text=True,
			check=False,
		)

		if result.returncode != 0:
			return []

		return json.loads(result.stdout)

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

	result = subprocess.run(
		["claude", "plugin", "marketplace", "update", market],
		capture_output=True,
		text=True,
	)

	if result.returncode != 0:
		error_msg = result.stderr.strip() if result.stderr else result.stdout.strip()
		stats.add_message("error", f"Failed to update {market}: {error_msg}")
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


def main() -> int:
	parser = argparse.ArgumentParser(
		description="Update enabled plugins using Claude's official plugin update command"
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
		help="Skip marketplace update (faster, but may use stale data)",
	)

	args = parser.parse_args()

	set_quiet_mode(args.quiet)

	console.print(
		Panel.fit(
			"[bold cyan]Plugin Update Tool (Claude Official)[/bold cyan]",
			border_style="blue",
		)
	)

	stats = UpdateStats()

	enabled_plugins = get_enabled_plugins_list()
	console.print(f"[dim]Found {len(enabled_plugins)} enabled plugin(s)[/dim]\n")

	if not enabled_plugins:
		console.print("[yellow]No enabled plugins found[/yellow]")
		return 0

	# Display enabled plugins
	enabled_table = Table(
		title="[bold]Enabled Plugins[/bold]", show_header=True, header_style="bold cyan"
	)
	enabled_table.add_column("Plugin", style="green")
	enabled_table.add_column("Market", style="blue")
	enabled_table.add_column("Scope", style="cyan")
	enabled_table.add_column("Version", style="yellow")

	for plugin in enabled_plugins:
		plugin_id = plugin.get("id", "")
		parsed = parse_plugin_key(plugin_id)
		if parsed:
			plugin_name, market = parsed
			scope = plugin.get("scope", "unknown")
			version = plugin.get("version", "-")
			scope_display = f"[cyan]{scope}[/cyan]" if scope == "user" else f"[magenta]{scope}[/magenta]"
			enabled_table.add_row(plugin_name, market, scope_display, version)

	console.print(enabled_table)
	console.print()

	# Get installed marketplaces
	marketplaces = get_marketplace_list()
	console.print(f"[dim]Found {len(marketplaces)} marketplace(s)[/dim]\n")

	# Update marketplaces (optional)
	if marketplaces and not args.no_market_update:
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
					"[cyan]Updating markets...[/cyan]", total=len(marketplaces)
				)
				for marketplace in marketplaces:
					market_name = marketplace.get("name", "unknown")
					progress.update(task, description=f"[cyan]Updating {market_name}...[/cyan]")
					update_marketplace(market_name, stats, dry_run=args.dry_run)
					progress.advance(task)
			else:
				for marketplace in marketplaces:
					market_name = marketplace.get("name", "unknown")
					update_marketplace(market_name, stats, dry_run=args.dry_run)
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
				"[cyan]Updating plugins...[/cyan]", total=len(enabled_plugins)
			)

			for plugin in enabled_plugins:
				plugin_id = plugin.get("id", "")
				plugin_name = plugin_id.split("@")[0] if plugin_id else "unknown"
				progress.update(task, description=f"[cyan]Updating {plugin_name}...[/cyan]")

				if run_claude_plugin_update(plugin_id, dry_run=args.dry_run, quiet=args.quiet):
					stats.updated_count += 1
				else:
					stats.error_count += 1

				progress.advance(task)
	else:
		for plugin in enabled_plugins:
			plugin_id = plugin.get("id", "")
			if run_claude_plugin_update(plugin_id, dry_run=args.dry_run, quiet=args.quiet):
				stats.updated_count += 1
			else:
				stats.error_count += 1

	# Print summary
	console.print()
	stats.print_summary()

	return 0 if stats.error_count == 0 else 1


if __name__ == "__main__":
	sys.exit(main())