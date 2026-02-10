#!/usr/bin/env python3
"""Version update script for CCPlugin monorepo.

Updates version numbers across:
- .version file (4-part: major.minor.patch.build)
- marketplace.json
- All plugin.json files
- All pyproject.toml files
- uv.lock files (via uv lock -U)
"""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple

import toml
from rich.console import Console

# Console instance for rich output
console = Console()

# Project paths
MARKETPLACE_JSON = ".claude-plugin/marketplace.json"
VERSION_FILE = ".version"
PLUGINS_DIR = "plugins"

# Version parts
VERSION_PARTS_STANDARD = 3
VERSION_PARTS_WITH_BUILD = 4


class VersionUpdateResult(NamedTuple):
    """Result of a version update operation."""
    updated: list[str]
    failed: list[dict[str, str]]


@dataclass
class VersionConfig:
    """Configuration for version update."""
    base_dir: Path
    old_version: str
    new_version: str  # 3-part format (major.minor.patch)
    new_version_full: str  # 4-part format (major.minor.patch.build)


def parse_version(version_str: str) -> tuple[int, int, int, int | None]:
    """Parse version string into components.

    Args:
        version_str: Version string (3 or 4 parts)

    Returns:
        Tuple of (major, minor, patch, build) where build may be None

    Raises:
        ValueError: If version format is invalid
    """
    parts = version_str.split('.')
    if len(parts) not in (VERSION_PARTS_STANDARD, VERSION_PARTS_WITH_BUILD):
        raise ValueError(f"Invalid version format: {version_str}")

    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    build = int(parts[3]) if len(parts) == VERSION_PARTS_WITH_BUILD else None

    return major, minor, patch, build


def format_version(major: int, minor: int, patch: int, build: int | None = None) -> str:
    """Format version components into string.

    Args:
        major: Major version number
        minor: Minor version number
        patch: Patch version number
        build: Optional build number

    Returns:
        Formatted version string
    """
    if build is not None:
        return f"{major}.{minor}.{patch}.{build}"
    return f"{major}.{minor}.{patch}"


def increment_version(version_str: str, include_build: bool = False) -> str:
    """Increment patch version number.

    Args:
        version_str: Version string (3 or 4 parts: major.minor.patch[.build])
        include_build: If True, return 4-part format with build=0.
                      If False, return 3-part format.

    Returns:
        Incremented version string

    Raises:
        ValueError: If version format is invalid
    """
    major, minor, patch, _build = parse_version(version_str)
    new_patch = patch + 1
    build = 0 if include_build else None
    return format_version(major, minor, new_patch, build)


def update_plugin_versions(plugins_dir: Path, new_version: str) -> VersionUpdateResult:
    """Update all plugin.json files under plugins directory.

    Args:
        plugins_dir: Path to plugins directory
        new_version: New version string to set

    Returns:
        VersionUpdateResult with updated paths and failed items
    """
    updated = []
    failed = []

    plugin_jsons = list(plugins_dir.glob('**/.claude-plugin/plugin.json'))

    for plugin_json_path in sorted(plugin_jsons):
        try:
            with open(plugin_json_path, 'r', encoding='utf-8') as f:
                plugin_data = json.load(f)

            plugin_data['version'] = new_version

            with open(plugin_json_path, 'w', encoding='utf-8') as f:
                json.dump(plugin_data, f, ensure_ascii=False, indent=2)
                f.write('\n')

            relative_path = plugin_json_path.relative_to(plugins_dir).parent.parent
            updated.append(str(relative_path))
        except Exception as e:
            relative_path = plugin_json_path.relative_to(plugins_dir).parent.parent
            failed.append({'path': str(relative_path), 'error': str(e)})

    return VersionUpdateResult(updated, failed)


def find_pyproject_paths(base_dir: Path) -> list[Path]:
    """Find all pyproject.toml files in the project.

    Searches in:
    - Root directory
    - lib directory
    - All plugin directories (single and nested level)

    Args:
        base_dir: Project base directory

    Returns:
        List of pyproject.toml file paths
    """
    pyproject_paths = []

    # Root pyproject.toml
    root_pyproject = base_dir / 'pyproject.toml'
    if root_pyproject.exists():
        pyproject_paths.append(root_pyproject)

    # lib/pyproject.toml
    lib_pyproject = base_dir / 'lib' / 'pyproject.toml'
    if lib_pyproject.exists():
        pyproject_paths.append(lib_pyproject)

    # Plugin pyproject.toml files
    plugins_dir = base_dir / PLUGINS_DIR
    if plugins_dir.exists():
        # Single-level plugins (plugins/*/pyproject.toml)
        for path in sorted(plugins_dir.glob('*/pyproject.toml')):
            pyproject_paths.append(path)
        # Nested plugins (plugins/*/*/pyproject.toml)
        for path in sorted(plugins_dir.glob('*/*/pyproject.toml')):
            pyproject_paths.append(path)

    return pyproject_paths


def update_pyproject_versions(
    base_dir: Path,
    pyproject_paths: list[Path],
    new_version: str
) -> VersionUpdateResult:
    """Update version in all pyproject.toml files.

    Args:
        base_dir: Project base directory for relative paths
        pyproject_paths: List of pyproject.toml file paths
        new_version: New version string to set

    Returns:
        VersionUpdateResult with updated paths and failed items
    """
    updated = []
    failed = []

    for pyproject_path in pyproject_paths:
        try:
            if not pyproject_path.exists():
                failed.append({
                    'path': str(pyproject_path.relative_to(base_dir)),
                    'error': 'File not found'
                })
                continue

            with open(pyproject_path, 'r', encoding='utf-8') as f:
                data = toml.load(f)

            if 'project' not in data:
                failed.append({
                    'path': str(pyproject_path.relative_to(base_dir)),
                    'error': '[project] section not found'
                })
                continue

            data['project']['version'] = new_version

            with open(pyproject_path, 'w', encoding='utf-8') as f:
                toml.dump(data, f)

            relative_path = pyproject_path.relative_to(base_dir)
            updated.append(str(relative_path))

        except Exception as e:
            failed.append({
                'path': str(pyproject_path.relative_to(base_dir)),
                'error': str(e)
            })

    return VersionUpdateResult(updated, failed)


def run_uv_update(project_dir: Path, console: Console) -> bool:
    """Run 'uv lock -U' and 'uv sync' in a project directory.

    Args:
        project_dir: Directory containing pyproject.toml
        console: Console instance for output

    Returns:
        True if successful, False otherwise
    """
    console.print(f"  Running 'uv lock -U && uv sync' in {project_dir}...")

    try:
        # Run uv lock -U
        lock_result = subprocess.run(
            ['uv', 'lock', '-U'],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if lock_result.returncode != 0:
            return False

        # Run uv sync
        sync_result = subprocess.run(
            ['uv', 'sync'],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=120,
        )

        return sync_result.returncode == 0

    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False


def update_uv_locks(pyproject_paths: list[Path]) -> VersionUpdateResult:
    """Run 'uv lock -U' in each directory containing pyproject.toml.

    Args:
        pyproject_paths: List of pyproject.toml file paths

    Returns:
        VersionUpdateResult with updated directories and failed items
    """
    updated = []
    failed = []
    processed_dirs = set()

    for pyproject_path in pyproject_paths:
        if not pyproject_path.exists():
            continue

        project_dir = pyproject_path.parent

        # Skip already processed directories
        if project_dir in processed_dirs:
            continue

        processed_dirs.add(project_dir)

        if run_uv_update(project_dir, console):
            updated.append(str(project_dir))
        else:
            failed.append({
                'path': str(project_dir),
                'error': 'uv lock -U or uv sync failed'
            })

    return VersionUpdateResult(updated, failed)


def update_marketplace(marketplace_path: Path, new_version: str) -> None:
    """Update version in marketplace.json.

    Args:
        marketplace_path: Path to marketplace.json
        new_version: New version string to set
    """
    with open(marketplace_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    data['metadata']['version'] = new_version

    for plugin in data['plugins']:
        plugin['version'] = new_version

    with open(marketplace_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')


def update_version_file(version_path: Path, new_version: str) -> None:
    """Update .version file with new version.

    Args:
        version_path: Path to .version file
        new_version: New version string to write
    """
    with open(version_path, 'w', encoding='utf-8') as f:
        f.write(new_version)


def print_version_updates(
    updated: list[str],
    label: str,
    old_version: str,
    new_version: str,
    console: Console
) -> None:
    """Print version update results.

    Args:
        updated: List of updated item names
        label: Label for the update category
        old_version: Old version string
        new_version: New version string
        console: Console instance for output
    """
    console.print(f"  [green]✓[/green] Updated {len(updated)} {label}")
    for name in updated:
        console.print(f"    - {name}: {old_version} → {new_version}")


def print_failures(failures_by_category: list[tuple[str, list[dict[str, str]]]]) -> None:
    """Print all failures in a structured format.

    Args:
        failures_by_category: List of (category_name, failures_list) tuples
    """
    console.print("\n[bold red]Failures Summary:[/bold red]")
    for category, failures in failures_by_category:
        console.print(f"\n[red]{category}:[/red]")
        for item in failures:
            console.print(f"  [red]✗[/red] {item['path']}")
            console.print(f"      Error: {item['error']}")


def load_version(version_path: Path) -> str:
    """Load current version from .version file.

    Args:
        version_path: Path to .version file

    Returns:
        Version string

    Raises:
        FileNotFoundError: If version file does not exist
    """
    with open(version_path, 'r', encoding='utf-8') as f:
        return f.read().strip()


def main() -> int:
    """Main entry point for version update script.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    base_dir = Path(__file__).parent.parent
    marketplace_path = base_dir / MARKETPLACE_JSON
    version_path = base_dir / VERSION_FILE
    plugins_dir = base_dir / PLUGINS_DIR

    # Validate required files exist
    if not marketplace_path.exists():
        console.print(f"[red]Error: marketplace.json not found at {marketplace_path}[/red]")
        return 1

    if not version_path.exists():
        console.print(f"[red]Error: .version file not found at {version_path}[/red]")
        return 1

    # Load and increment version
    old_version = load_version(version_path)
    new_version = increment_version(old_version, include_build=False)
    new_version_full = increment_version(old_version, include_build=True)

    console.print("\n[bold cyan]Updating versions...[/bold cyan]")

    # Update marketplace.json
    update_marketplace(marketplace_path, new_version)
    console.print(f"  [green]✓[/green] marketplace.json: {old_version} → {new_version}")

    # Update plugin.json files
    plugin_result = update_plugin_versions(plugins_dir, new_version)
    print_version_updates(plugin_result.updated, 'plugin.json(s)', old_version, new_version, console)

    # Update pyproject.toml files
    pyproject_paths = find_pyproject_paths(base_dir)
    pyproject_result = update_pyproject_versions(base_dir, pyproject_paths, new_version)
    print_version_updates(pyproject_result.updated, 'pyproject.toml file(s)', old_version, new_version, console)

    # Update uv.lock files
    console.print("\n[bold cyan]Updating uv.lock files...[/bold cyan]")
    lock_result = update_uv_locks(pyproject_paths)
    console.print(f"  [green]✓[/green] Updated {len(lock_result.updated)} uv.lock file(s)")
    for lock_dir in lock_result.updated:
        console.print(f"    - {lock_dir}")

    # Update .version file
    update_version_file(version_path, new_version_full)
    console.print(f"  [green]✓[/green] .version: {old_version} → {new_version_full}")

    # Print success summary
    console.print(f"\n[bold green]Version update completed: {old_version} → {new_version_full}[/bold green]")

    # Collect and print failures
    all_failures = []
    if plugin_result.failed:
        all_failures.append(('Plugin Files', plugin_result.failed))
    if pyproject_result.failed:
        all_failures.append(('Pyproject Files', pyproject_result.failed))
    if lock_result.failed:
        all_failures.append(('UV Lock Updates', lock_result.failed))

    if all_failures:
        print_failures(all_failures)
        return 1

    return 0


if __name__ == '__main__':
    exit(main())