#!/usr/bin/env python3
"""Clean old plugin versions from ~/.claude/plugins/cache/

This script:
1. Scans ~/.claude/plugins/cache/ for plugin versions
2. Reads installed_plugins.json to identify currently active versions
3. Keeps only the latest version of each plugin
4. Protects currently installed plugins from deletion
5. Shows metadata (install time, last updated) for each version

Directory structure:
~/.claude/plugins/cache/
├── ccplugin-market/
│   ├── git/
│   │   ├── 0.0.10/
│   │   ├── 0.0.11/
│   │   └── ...
│   ├── semantic/
│   │   └── ...
│   └── ...
└── ...
"""
import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

console = Console()


def get_cache_dir() -> Path:
	"""Get the plugin cache directory."""
	return Path.home() / '.claude' / 'plugins' / 'cache'


def get_installed_plugins() -> Dict[str, str]:
	"""Read installed plugins from installed_plugins.json.

	Returns a dict mapping plugin_key to version.
	For example: {"ccplugin-market/git": "0.0.121", ...}
	"""
	installed_path = Path.home() / '.claude' / 'plugins' / 'installed_plugins.json'

	if not installed_path.exists():
		return {}

	try:
		with open(installed_path, 'r', encoding='utf-8') as f:
			data = json.load(f)
	except (json.JSONDecodeError, IOError):
		return {}

	installed = {}

	for plugin_key, installations in data.get('plugins', {}).items():
		# installations is a list of install records
		for install in installations:
			install_path = Path(install.get('installPath', ''))
			version = install.get('version', '')

			# Extract market/plugin from install path
			# Path format: ~/.claude/plugins/cache/<market>/<plugin>/<version>/
			parts = install_path.parts
			try:
				cache_idx = parts.index('cache')
				if cache_idx + 3 < len(parts):
					market = parts[cache_idx + 1]
					plugin = parts[cache_idx + 2]
					key = f"{market}/{plugin}"
					if version:
						installed[key] = version
			except (ValueError, IndexError):
				continue

	return installed


def get_plugin_metadata(version_dir: Path) -> Dict[str, Optional[str]]:
	"""Get metadata for a plugin version directory.

	Returns dict with 'installed_at' and 'last_updated' timestamps.
	"""
	metadata = {
		'installed_at': None,
		'last_updated': None,
		'commit_sha': None,
	}

	# Try to read from .git-commit-sha file
	commit_sha_file = version_dir / '.git-commit-sha'
	if commit_sha_file.exists():
		try:
			metadata['commit_sha'] = commit_sha_file.read_text().strip()
		except (IOError, OSError):
			pass

	# Get directory modification time as last updated
	try:
		stat = version_dir.stat()
		mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
		metadata['last_updated'] = mtime.isoformat(timespec='seconds')
	except (OSError, ValueError):
		pass

	# Try to find installed_plugins.json entry for this version
	installed_path = Path.home() / '.claude' / 'plugins' / 'installed_plugins.json'
	if installed_path.exists():
		try:
			with open(installed_path, 'r', encoding='utf-8') as f:
				data = json.load(f)

			for plugin_key, installations in data.get('plugins', {}).items():
				for install in installations:
					install_path = Path(install.get('installPath', ''))
					if install_path == version_dir:
						installed_at = install.get('installedAt')
						if installed_at:
							metadata['installed_at'] = installed_at
						last_updated = install.get('lastUpdated')
						if last_updated:
							metadata['last_updated'] = last_updated
						break
		except (json.JSONDecodeError, IOError, OSError):
			pass

	return metadata


def format_timestamp(timestamp_str: Optional[str]) -> str:
	"""Format ISO timestamp for display."""
	if not timestamp_str:
		return "[dim]N/A[/dim]"

	try:
		dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
		# Format as relative time if recent, else as date
		now = datetime.now(timezone.utc)
		delta = now - dt

		if delta.days < 1:
			hours = delta.seconds // 3600
			if hours < 1:
				minutes = delta.seconds // 60
				return f"[cyan]{minutes}m ago[/cyan]"
			return f"[cyan]{hours}h ago[/cyan]"
		elif delta.days < 7:
			return f"[cyan]{delta.days}d ago[/cyan]"
		else:
			return dt.strftime('%Y-%m-%d')
	except (ValueError, AttributeError):
		return str(timestamp_str)


def parse_version(version_str: str) -> Tuple[int, int, int]:
	"""Parse version string to tuple for comparison.

	Examples:
		'0.0.11' -> (0, 0, 11)
		'1.2' -> (1, 2, 0)
		'1' -> (1, 0, 0)
	"""
	try:
		parts = version_str.split('.')
		if len(parts) >= 3:
			return (int(parts[0]), int(parts[1]), int(parts[2]))
		elif len(parts) == 2:
			return (int(parts[0]), int(parts[1]), 0)
		elif len(parts) == 1:
			return (int(parts[0]), 0, 0)
	except (ValueError, AttributeError):
		pass
	return (0, 0, 0)


def get_plugin_versions(cache_dir: Path) -> Dict[str, List[Path]]:
	"""Get all plugin versions grouped by plugin name.

	Scans: cache_dir/<market>/<plugin>/<version>/

	Returns a dict mapping "market/plugin" keys to list of version directories.
	"""
	plugins: Dict[str, List[Path]] = {}

	if not cache_dir.exists():
		return plugins

	# Iterate through market directories
	for market_dir in cache_dir.iterdir():
		if not market_dir.is_dir():
			continue

		# Iterate through plugin directories within each market
		for plugin_dir in market_dir.iterdir():
			if not plugin_dir.is_dir():
				continue

			plugin_key = f"{market_dir.name}/{plugin_dir.name}"

			# Iterate through version directories
			version_dirs = []
			for version_dir in plugin_dir.iterdir():
				if version_dir.is_dir():
					version_dirs.append(version_dir)

			if version_dirs:
				plugins[plugin_key] = version_dirs

	return plugins


def calculate_dir_size(path: Path) -> int:
	"""Calculate total size of a directory in bytes."""
	total = 0
	try:
		for entry in path.rglob('*'):
			if entry.is_file():
				total += entry.stat().st_size
	except OSError:
		pass
	return total


def format_size(size_bytes: int) -> str:
	"""Format bytes to human-readable size."""
	for unit in ['B', 'KB', 'MB', 'GB']:
		if size_bytes < 1024:
			return f"{size_bytes:.1f}{unit}"
		size_bytes /= 1024
	return f"{size_bytes:.1f}TB"


def clean_old_versions(
	cache_dir: Path,
	installed_plugins: Dict[str, str],
	dry_run: bool = False
) -> Tuple[int, int, List[Tuple[str, str, str, bool]]]:
	"""Clean old plugin versions, keeping only the latest.

	For each plugin in each market, deletes all versions except the newest.
	Protects currently installed versions from deletion.

	Args:
		cache_dir: Path to the cache directory
		installed_plugins: Dict of plugin_key -> currently installed version
		dry_run: If True, only show what would be deleted without actually deleting

	Returns:
		- Number of deleted directories
		- Total freed space in bytes
		- List of (plugin_key, version, size, is_protected) tuples
	"""
	plugins = get_plugin_versions(cache_dir)
	deleted_count = 0
	freed_space = 0
	cleaned_info: List[Tuple[str, str, str, bool]] = []

	for plugin_key, versions in plugins.items():
		if len(versions) <= 1:
			continue

		# Sort by version (descending) to find the latest
		sorted_versions = sorted(
			versions,
			key=lambda p: parse_version(p.name),
			reverse=True
		)

		installed_version = installed_plugins.get(plugin_key)

		# Keep the first (latest), delete the rest
		# But skip if the version is currently installed
		to_delete = sorted_versions[1:]

		for version_dir in to_delete:
			version = version_dir.name

			# Skip if this version is currently installed
			if installed_version and version == installed_version:
				cleaned_info.append((plugin_key, version, "0B (protected)", True))
				continue

			try:
				size = calculate_dir_size(version_dir)
				size_str = format_size(size)

				if dry_run:
					# In dry-run mode, just count and report
					deleted_count += 1
					freed_space += size
					cleaned_info.append((plugin_key, version, size_str, False))
				else:
					# Actually delete the directory
					shutil.rmtree(version_dir)
					deleted_count += 1
					freed_space += size
					cleaned_info.append((plugin_key, version, size_str, False))
			except Exception as e:
				console.print(f"  [red]Failed to delete[/red] {plugin_key}/{version_dir.name}: {e}")

	return deleted_count, freed_space, cleaned_info


def display_cleanup_tree(
	cleaned_info: List[Tuple[str, str, str, bool]],
	dry_run: bool
) -> None:
	"""Display cleanup information in a tree structure."""
	if not cleaned_info:
		return

	action_label = "[yellow]Would delete[/yellow]" if dry_run else "[red]Deleted[/red]"
	root = Tree(f"{action_label} old plugin versions:")

	# Group by plugin key
	grouped: Dict[str, List[Tuple[str, str, bool]]] = {}
	for plugin_key, version, size, is_protected in cleaned_info:
		if plugin_key not in grouped:
			grouped[plugin_key] = []
		grouped[plugin_key].append((version, size, is_protected))

	for plugin_key, versions in sorted(grouped.items()):
		branch = root.add(f"[cyan]{plugin_key}[/cyan]")
		for version, size, is_protected in sorted(versions):
			if is_protected:
				branch.add(f"  [green]✓[/green] [dim]{version}[/dim] [yellow](protected, {size})[/yellow]")
			else:
				branch.add(f"  [dim]{version}[/dim] [yellow]({size})[/yellow]")

	console.print(root)


def display_plugins_table(
	plugins: Dict[str, List[Path]],
	installed_plugins: Dict[str, str]
) -> None:
	"""Display detailed table of all plugins with metadata."""
	status_table = Table(
		title="[bold]Plugin Versions Details[/bold]",
		show_header=True,
		header_style="bold cyan"
	)
	status_table.add_column("Market/Plugin", style="cyan", width=30)
	status_table.add_column("Version", style="green", width=12)
	status_table.add_column("Status", style="yellow", width=15)
	status_table.add_column("Size", justify="right", style="blue", width=10)
	status_table.add_column("Last Updated", style="magenta", width=15)

	total_plugins = 0
	total_versions = 0
	outdated_plugins = 0
	protected_count = 0

	for plugin_key, versions in sorted(plugins.items()):
		sorted_versions = sorted(
			versions,
			key=lambda p: parse_version(p.name),
			reverse=True
		)
		latest = sorted_versions[0].name
		installed_version = installed_plugins.get(plugin_key)
		version_count = len(versions)

		total_plugins += 1
		total_versions += version_count

		# Mark if multiple versions exist
		if version_count > 1:
			outdated_plugins += 1

		# Show each version
		for i, version_dir in enumerate(sorted_versions):
			version = version_dir.name
			is_latest = version == latest
			is_installed = installed_version and version == installed_version

			# Calculate size
			size = calculate_dir_size(version_dir)
			size_str = format_size(size)

			# Get metadata
			metadata = get_plugin_metadata(version_dir)
			last_updated = format_timestamp(metadata.get('last_updated'))

			# Determine status
			if is_installed:
				status = "[green]✓ Installed[/green]"
				protected_count += 1
			elif is_latest and not is_installed:
				status = "[cyan]Latest[/cyan]"
			else:
				status = "[red]× Old[/red]"

			# Add row
			market_plugin = plugin_key if i == 0 else ""
			ver_str = version
			status_table.add_row(market_plugin, ver_str, status, size_str, last_updated)

	console.print(status_table)
	console.print(
		f"[dim]Total: {total_plugins} plugins, {total_versions} versions, "
		f"{outdated_plugins} with old versions, {protected_count} protected[/dim]\n"
	)


def main():
	parser = argparse.ArgumentParser(
		description="Clean old plugin versions from cache"
	)
	parser.add_argument(
		'--dry-run', '-d',
		action='store_true',
		help='Show what would be deleted without actually deleting'
	)

	args = parser.parse_args()
	dry_run = args.dry_run

	cache_dir = get_cache_dir()
	installed_plugins = get_installed_plugins()

	# Print header
	mode = "[yellow]DRY-RUN[/yellow]" if dry_run else "[bold red]CLEAN[/bold red]"
	console.print(Panel.fit(
		f"[bold cyan]Plugin Cache Cleaner[/bold cyan]\n"
		f"[dim]Mode:[/dim] {mode}\n"
		f"[dim]Cache:[/dim] {cache_dir}\n"
		f"[dim]Protected:[/dim] {len(installed_plugins)} installed plugin(s)",
		border_style="blue"
	))

	if not cache_dir.exists():
		console.print("[yellow]Cache directory not found. Nothing to clean.[/yellow]")
		return 0

	# Scan cache directory
	plugins = get_plugin_versions(cache_dir)

	if not plugins:
		console.print("[yellow]No plugins found in cache.[/yellow]")
		return 0

	# Display detailed plugin table
	display_plugins_table(plugins, installed_plugins)

	# Count plugins with old versions
	outdated_plugins = sum(1 for versions in plugins.values() if len(versions) > 1)

	if outdated_plugins == 0:
		console.print("[green]✓ No old plugin versions found. Cache is clean.[/green]")
		return 0

	# Perform cleanup
	deleted_count, freed_space, cleaned_info = clean_old_versions(
		cache_dir,
		installed_plugins,
		dry_run=dry_run
	)

	# Display cleanup tree
	display_cleanup_tree(cleaned_info, dry_run)

	# Display summary table
	summary_table = Table(title="[bold blue]Cleanup Summary[/bold blue]", show_header=True)
	summary_table.add_column("Metric", style="cyan", width=25)
	summary_table.add_column("Value", justify="right", style="green")

	# Count protected versions
	protected_count = sum(1 for _, _, _, is_protected in cleaned_info if is_protected)
	summary_table.add_row("Versions processed", str(deleted_count + protected_count))
	summary_table.add_row("Versions protected (installed)", str(protected_count))
	summary_table.add_row("Versions to delete/cleaned", str(deleted_count))
	summary_table.add_row("Space freed", f"[bold green]{format_size(freed_space)}[/bold green]")

	console.print(summary_table)

	if dry_run:
		console.print("\n[yellow]To actually delete these versions, run:[/yellow] [cyan]clean[/cyan]")

	return 0


if __name__ == '__main__':
	exit(main())
