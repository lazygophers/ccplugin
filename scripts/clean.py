#!/usr/bin/env python3
"""Clean old plugin versions from ~/.claude/plugins/cache/

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
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.tree import Tree

console = Console()


def get_cache_dir() -> Path:
    """Get the plugin cache directory."""
    return Path.home() / '.claude' / 'plugins' / 'cache'


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
    dry_run: bool = False
) -> Tuple[int, int, List[Tuple[str, str, str]]]:
    """Clean old plugin versions, keeping only the latest.

    For each plugin in each market, deletes all versions except the newest.

    Args:
        cache_dir: Path to the cache directory
        dry_run: If True, only show what would be deleted without actually deleting

    Returns:
        - Number of deleted directories
        - Total freed space in bytes
        - List of (plugin_key, version, size) tuples
    """
    plugins = get_plugin_versions(cache_dir)
    deleted_count = 0
    freed_space = 0
    cleaned_info: List[Tuple[str, str, str]] = []

    for plugin_key, versions in plugins.items():
        if len(versions) <= 1:
            continue

        # Sort by version (descending) to find the latest
        sorted_versions = sorted(
            versions,
            key=lambda p: parse_version(p.name),
            reverse=True
        )

        # Keep the first (latest), delete the rest
        to_delete = sorted_versions[1:]

        for version_dir in to_delete:
            try:
                size = calculate_dir_size(version_dir)
                version = version_dir.name
                size_str = format_size(size)

                if dry_run:
                    # In dry-run mode, just count and report
                    deleted_count += 1
                    freed_space += size
                    cleaned_info.append((plugin_key, version, size_str))
                else:
                    # Actually delete the directory
                    shutil.rmtree(version_dir)
                    deleted_count += 1
                    freed_space += size
                    cleaned_info.append((plugin_key, version, size_str))
            except Exception as e:
                console.print(f"  [red]Failed to delete[/red] {plugin_key}/{version_dir.name}: {e}")

    return deleted_count, freed_space, cleaned_info


def display_cleanup_tree(cleaned_info: List[Tuple[str, str, str]], dry_run: bool) -> None:
    """Display cleanup information in a tree structure."""
    if not cleaned_info:
        return

    action_label = "[yellow]Would delete[/yellow]" if dry_run else "[red]Deleted[/red]"
    root = Tree(f"{action_label} old plugin versions:")

    # Group by plugin key
    grouped: Dict[str, List[Tuple[str, str]]] = {}
    for plugin_key, version, size in cleaned_info:
        if plugin_key not in grouped:
            grouped[plugin_key] = []
        grouped[plugin_key].append((version, size))

    for plugin_key, versions in sorted(grouped.items()):
        branch = root.add(f"[cyan]{plugin_key}[/cyan]")
        for version, size in sorted(versions):
            branch.add(f"  [dim]{version}[/dim] [yellow]({size})[/yellow]")

    console.print(root)


def main():
    # Parse command line arguments
    dry_run = '--dry-run' in sys.argv or '-d' in sys.argv
    show_help = '--help' in sys.argv or '-h' in sys.argv

    if show_help:
        console.print(Panel.fit(
            "[bold cyan]Plugin Cache Cleaner[/bold cyan]\n\n"
            "[dim]Usage:[/dim] clean [OPTIONS]\n\n"
            "[bold cyan]Options:[/bold cyan]\n"
            "  [cyan]--dry-run, -d[/cyan]  Show what would be deleted without actually deleting\n"
            "  [cyan]--help, -h[/cyan]     Show this help message\n"
        ))
        return 0

    cache_dir = get_cache_dir()

    # Print header
    mode = "[yellow]DRY-RUN[/yellow]" if dry_run else "[bold red]CLEAN[/bold red]"
    console.print(Panel.fit(
        f"[bold cyan]Plugin Cache Cleaner[/bold cyan]\n"
        f"[dim]Mode:[/dim] {mode}\n"
        f"[dim]Cache:[/dim] {cache_dir}",
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

    # Display current cache status
    status_table = Table(title="[bold]Current Cache Status[/bold]", show_header=True)
    status_table.add_column("Market/Plugin", style="cyan")
    status_table.add_column("Versions", justify="right", style="green")
    status_table.add_column("Latest", style="yellow")

    total_plugins = 0
    total_versions = 0
    outdated_plugins = 0

    for plugin_key, versions in sorted(plugins.items()):
        sorted_versions = sorted(versions, key=lambda p: parse_version(p.name), reverse=True)
        latest = sorted_versions[0].name
        version_count = len(versions)
        total_plugins += 1
        total_versions += version_count
        if version_count > 1:
            outdated_plugins += 1
            # Mark outdated plugins with a warning
            status_table.add_row(f"[yellow]⚠[/yellow] {plugin_key}", str(version_count), f"[green]{latest}[/green]")
        else:
            status_table.add_row(f"[dim]✓[/dim] {plugin_key}", str(version_count), f"[dim]{latest}[/dim]")

    console.print(status_table)
    console.print(f"[dim]Total: {total_plugins} plugins, {total_versions} versions, {outdated_plugins} with old versions[/dim]\n")

    if outdated_plugins == 0:
        console.print("[green]✓ No old plugin versions found. Cache is clean.[/green]")
        return 0

    # Perform cleanup
    deleted_count, freed_space, cleaned_info = clean_old_versions(cache_dir, dry_run=dry_run)

    # Display cleanup tree
    display_cleanup_tree(cleaned_info, dry_run)

    # Display summary table
    summary_table = Table(title="[bold blue]Cleanup Summary[/bold blue]", show_header=True)
    summary_table.add_column("Metric", style="cyan", width=25)
    summary_table.add_column("Value", justify="right", style="green")

    summary_table.add_row("Directories cleaned", str(deleted_count))
    summary_table.add_row("Space freed", f"[bold green]{format_size(freed_space)}[/bold green]")

    console.print(summary_table)

    if dry_run:
        console.print("\n[yellow]To actually delete these versions, run:[/yellow] [cyan]clean[/cyan]")

    return 0


if __name__ == '__main__':
    exit(main())
