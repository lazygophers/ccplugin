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


def clean_old_versions(cache_dir: Path, dry_run: bool = False) -> Tuple[int, int, List[str]]:
    """Clean old plugin versions, keeping only the latest.

    For each plugin in each market, deletes all versions except the newest.

    Args:
        cache_dir: Path to the cache directory
        dry_run: If True, only show what would be deleted without actually deleting

    Returns:
        - Number of deleted directories
        - Total freed space in bytes
        - List of cleaned plugin names with version info
    """
    plugins = get_plugin_versions(cache_dir)
    deleted_count = 0
    freed_space = 0
    cleaned_info = []

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

                if dry_run:
                    # In dry-run mode, just count and report
                    deleted_count += 1
                    freed_space += size
                    cleaned_info.append(
                        f"  [DRY-RUN] Would delete {plugin_key}/{version} ({format_size(size)})"
                    )
                else:
                    # Actually delete the directory
                    shutil.rmtree(version_dir)
                    deleted_count += 1
                    freed_space += size
                    cleaned_info.append(
                        f"  Deleted {plugin_key}/{version} ({format_size(size)})"
                    )
            except Exception as e:
                cleaned_info.append(
                    f"  Failed to delete {plugin_key}/{version_dir.name}: {e}"
                )

    return deleted_count, freed_space, cleaned_info


def main():
    # Parse command line arguments
    dry_run = '--dry-run' in sys.argv or '-d' in sys.argv
    show_help = '--help' in sys.argv or '-h' in sys.argv

    if show_help:
        print("Usage: clean [OPTIONS]")
        print("\nOptions:")
        print("  --dry-run, -d  Show what would be deleted without actually deleting")
        print("  --help, -h     Show this help message")
        return 0

    cache_dir = get_cache_dir()

    mode = "DRY-RUN" if dry_run else "CLEAN"
    print(f"[{mode}] Cleaning plugin cache...")
    print(f"Cache directory: {cache_dir}\n")

    if not cache_dir.exists():
        print("Cache directory not found. Nothing to clean.")
        return 0

    deleted_count, freed_space, cleaned_info = clean_old_versions(cache_dir, dry_run=dry_run)

    if deleted_count == 0:
        print("No old plugin versions found. Cache is clean.")
        return 0

    action_label = "Would delete" if dry_run else "Deleted"
    print(f"{action_label} old plugin versions:")
    for info in cleaned_info:
        print(info)

    print(f"\nCleanup summary:")
    print(f"  Directories: {deleted_count}")
    print(f"  Freed space: {format_size(freed_space)}")

    if dry_run:
        print("\nTo actually delete these versions, run: clean")

    return 0


if __name__ == '__main__':
    exit(main())
