#!/usr/bin/env python3
"""Clean old plugin versions from ~/.claude/plugins/cache/

This script:
1. Scans ~/.claude/plugins/cache/ for plugin versions
2. Reads installed_plugins.json to identify currently installed versions
3. Only cleans versions that are NOT in installed_plugins.json
4. Shows metadata (install time, last updated) for each version

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
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.tree import Tree
from lib.utils import print_help, parse_version, format_size, format_timestamp, safe_load_json

console = Console()

# Path constants
CACHE_DIR = Path.home() / '.claude' / 'plugins' / 'cache'
INSTALLED_PLUGINS_JSON = Path.home() / '.claude' / 'plugins' / 'installed_plugins.json'


def get_cache_dir() -> Path:
	"""Get the plugin cache directory."""
	return CACHE_DIR


def get_installed_plugins(installed_data: Optional[Dict] = None) -> Dict[str, Set[str]]:
	"""Read installed plugins from installed_plugins.json.

	Args:
		installed_data: Pre-loaded JSON data (optional, for performance)

	Returns a dict mapping plugin_key to set of installed versions.
	For example: {"ccplugin-market/git": {"0.0.121", "0.0.122"}, ...}
	"""
	if installed_data is None:
		installed_data = safe_load_json(INSTALLED_PLUGINS_JSON)

	if not installed_data:
		return {}

	installed: Dict[str, Set[str]] = {}

	for plugin_key, installations in installed_data.get('plugins', {}).items():
		for install in installations:
			install_path = Path(install.get('installPath', ''))
			version = install.get('version', '')

			parts = install_path.parts
			try:
				cache_idx = parts.index('cache')
				if cache_idx + 3 < len(parts):
					market = parts[cache_idx + 1]
					plugin = parts[cache_idx + 2]
					key = f"{market}/{plugin}"
					if version:
						if key not in installed:
							installed[key] = set()
						installed[key].add(version)
			except (ValueError, IndexError):
				continue

	return installed


def get_plugin_metadata(version_dir: Path, installed_data: Optional[Dict] = None) -> Dict[str, Optional[str]]:
	"""Get metadata for a plugin version directory.

	Args:
		version_dir: Path to plugin version directory
		installed_data: Pre-loaded installed_plugins.json data (optional)

	Returns dict with 'installed_at' and 'last_updated' timestamps.
	"""
	metadata = {
		'installed_at': None,
		'last_updated': None,
		'commit_sha': None,
	}

	commit_sha_file = version_dir / '.git-commit-sha'
	if commit_sha_file.exists():
		try:
			metadata['commit_sha'] = commit_sha_file.read_text().strip()
		except (IOError, OSError):
			pass

	try:
		stat = version_dir.stat()
		mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
		metadata['last_updated'] = mtime.isoformat(timespec='seconds')
	except (OSError, ValueError):
		pass

	if installed_data is None:
		installed_data = safe_load_json(INSTALLED_PLUGINS_JSON)

	if installed_data:
		for plugin_key, installations in installed_data.get('plugins', {}).items():
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

	return metadata


def get_plugin_versions(cache_dir: Path) -> Dict[str, List[Path]]:
	"""Get all plugin versions grouped by plugin name.

	Scans: cache_dir/<market>/<plugin>/<version>/

	Returns a dict mapping "market/plugin" keys to list of version directories.
	"""
	plugins: Dict[str, List[Path]] = {}

	if not cache_dir.exists():
		return plugins

	for market_dir in cache_dir.iterdir():
		if not market_dir.is_dir():
			continue

		for plugin_dir in market_dir.iterdir():
			if not plugin_dir.is_dir():
				continue

			plugin_key = f"{market_dir.name}/{plugin_dir.name}"

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


def clean_orphaned_versions(
	cache_dir: Path,
	installed_plugins: Dict[str, Set[str]],
	dry_run: bool = False
) -> Tuple[int, int, List[Tuple[str, str, str, bool]]]:
	"""Clean versions that are NOT in installed_plugins.json.

	Only deletes versions that are not recorded as installed.
	All versions in installed_plugins.json are protected.

	Args:
		cache_dir: Path to the cache directory
		installed_plugins: Dict of plugin_key -> set of installed versions
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
		installed_versions = installed_plugins.get(plugin_key, set())

		for version_dir in versions:
			version = version_dir.name

			if version in installed_versions:
				continue

			try:
				size = calculate_dir_size(version_dir)
				size_str = format_size(size)

				if dry_run:
					deleted_count += 1
					freed_space += size
					cleaned_info.append((plugin_key, version, size_str, False))
				else:
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
	root = Tree(f"{action_label} orphaned plugin versions:")

	grouped: Dict[str, List[Tuple[str, str, bool]]] = {}
	for plugin_key, version, size, is_protected in cleaned_info:
		if plugin_key not in grouped:
			grouped[plugin_key] = []
		grouped[plugin_key].append((version, size, is_protected))

	for plugin_key, versions in sorted(grouped.items()):
		branch = root.add(f"[cyan]{plugin_key}[/cyan]")
		for version, size, is_protected in sorted(versions):
			branch.add(f"  [dim]{version}[/dim] [yellow]({size})[/yellow]")

	console.print(root)


def display_plugins_table(
	plugins: Dict[str, List[Path]],
	installed_plugins: Dict[str, Set[str]],
	installed_data: Optional[Dict] = None
) -> None:
	"""Display detailed table of all plugins with metadata.

	Args:
		plugins: Dict of plugin_key -> list of version directories
		installed_plugins: Dict of plugin_key -> set of installed versions
		installed_data: Pre-loaded installed_plugins.json data (for performance)
	"""
	status_table = Table(
		title="[bold]Plugin Versions Details[/bold]",
		show_header=True,
		header_style="bold cyan",
		box=box.ROUNDED,
	)
	status_table.add_column("Market/Plugin", style="cyan", width=30)
	status_table.add_column("Version", style="green", width=12)
	status_table.add_column("Status", style="yellow", width=15)
	status_table.add_column("Size", justify="right", style="blue", width=10)
	status_table.add_column("Last Updated", style="magenta", width=15)

	total_plugins = 0
	total_versions = 0
	orphaned_count = 0
	protected_count = 0
	size_cache: Dict[Path, int] = {}

	for plugin_key, versions in sorted(plugins.items()):
		sorted_versions = sorted(
			versions,
			key=lambda p: parse_version(p.name),
			reverse=True
		)
		installed_versions = installed_plugins.get(plugin_key, set())
		version_count = len(versions)

		total_plugins += 1
		total_versions += version_count

		for i, version_dir in enumerate(sorted_versions):
			version = version_dir.name
			is_installed = version in installed_versions

			if version_dir not in size_cache:
				size_cache[version_dir] = calculate_dir_size(version_dir)
			size = size_cache[version_dir]
			size_str = format_size(size)

			metadata = get_plugin_metadata(version_dir, installed_data)
			last_updated = format_timestamp(metadata.get('last_updated'))

			if is_installed:
				status = "[green]✓ Installed[/green]"
				protected_count += 1
			else:
				status = "[red]× Orphaned[/red]"
				orphaned_count += 1

			market_plugin = plugin_key if i == 0 else ""
			ver_str = version
			status_table.add_row(market_plugin, ver_str, status, size_str, last_updated)

	console.print(status_table)
	console.print(
		f"[dim]Total: {total_plugins} plugins, {total_versions} versions, "
		f"{orphaned_count} orphaned, {protected_count} protected[/dim]\n"
	)


def main():
	parser = argparse.ArgumentParser(
		prog="clean.py",
		description="🗑️ CCPlugin 缓存清理工具 - 清理未安装的插件版本",
		add_help=False,
	)
	parser.add_argument(
		'--dry-run', '-d',
		action='store_true',
		help='模拟运行，仅显示将要删除的内容',
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
	
	dry_run = args.dry_run

	cache_dir = get_cache_dir()
	installed_data = safe_load_json(INSTALLED_PLUGINS_JSON)
	installed_plugins = get_installed_plugins(installed_data)

	total_installed = sum(len(versions) for versions in installed_plugins.values())

	mode = "[yellow]DRY-RUN[/yellow]" if dry_run else "[bold red]CLEAN[/bold red]"
	console.print(Panel.fit(
		f"[bold cyan]🗑️  Plugin Cache Cleaner[/bold cyan]\n"
		f"[dim]Mode:[/dim] {mode}\n"
		f"[dim]Cache:[/dim] {cache_dir}\n"
		f"[dim]Protected:[/dim] {total_installed} installed version(s)",
		border_style="blue",
		box=box.DOUBLE,
	))
	console.print()

	if not cache_dir.exists():
		console.print(Panel(
			"[yellow]Cache directory not found. Nothing to clean.[/yellow]",
			border_style="yellow",
			box=box.ROUNDED,
		))
		return 0

	plugins = get_plugin_versions(cache_dir)

	if not plugins:
		console.print(Panel(
			"[yellow]No plugins found in cache.[/yellow]",
			border_style="yellow",
			box=box.ROUNDED,
		))
		return 0

	display_plugins_table(plugins, installed_plugins, installed_data)

	orphaned_count = 0
	for plugin_key, versions in plugins.items():
		installed_versions = installed_plugins.get(plugin_key, set())
		for version_dir in versions:
			if version_dir.name not in installed_versions:
				orphaned_count += 1

	if orphaned_count == 0:
		console.print(Panel(
			"[green]✓ No orphaned plugin versions found. All versions are installed.[/green]",
			border_style="green",
			box=box.ROUNDED,
		))
		return 0

	deleted_count, freed_space, cleaned_info = clean_orphaned_versions(
		cache_dir,
		installed_plugins,
		dry_run=dry_run
	)

	display_cleanup_tree(cleaned_info, dry_run)

	console.print()
	console.print(Rule(title="[bold blue]Cleanup Summary[/bold blue]", style="blue"))

	summary_table = Table(
		show_header=False,
		box=box.ROUNDED,
		padding=(0, 2),
	)
	summary_table.add_column("Metric", style="bold")
	summary_table.add_column("Value", justify="right")

	summary_table.add_row(
		"📦 Versions processed",
		str(len(cleaned_info)),
	)
	summary_table.add_row(
		"🗑️  Orphaned versions cleaned",
		f"[red]{deleted_count}[/red]",
	)
	summary_table.add_row(
		"💾 Space freed",
		f"[bold green]{format_size(freed_space)}[/bold green]",
	)

	console.print(summary_table)

	if dry_run:
		console.print("\n[yellow]To actually delete these versions, run:[/yellow] [cyan]clean[/cyan]")

	return 0


if __name__ == '__main__':
	exit(main())
