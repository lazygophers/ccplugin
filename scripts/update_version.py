#!/usr/bin/env python3
import json
import subprocess
import toml
from pathlib import Path
from typing import List
from rich.console import Console

console = Console()


def increment_version(version_str: str, include_build: bool = False) -> str:
    """Increment version number.

    Args:
        version_str: Version string (3 or 4 parts: major.minor.patch[.build])
        include_build: If True, keep 4-part format with build=0. If False, return 3-part format.

    Returns:
        Incremented version string (3 or 4 parts based on include_build)
    """
    parts = version_str.split('.')
    if len(parts) not in (3, 4):
        raise ValueError(f"Invalid version format: {version_str}")

    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    patch += 1

    if include_build:
        # Return 4-part format with build=0
        return f"{major}.{minor}.{patch}.0"
    else:
        # Return 3-part format
        return f"{major}.{minor}.{patch}"


def update_plugin_versions(plugins_dir: Path, new_version: str) -> tuple:
    """Recursively scan and update all plugin.json files under plugins directory.

    Returns:
        Tuple of (updated_plugins list, failed_items list)
    """
    updated_plugins = []
    failed_items = []

    # Recursively find all plugin.json files
    plugin_jsons = list(plugins_dir.glob('**/.claude-plugin/plugin.json'))

    for plugin_json_path in sorted(plugin_jsons):
        try:
            with open(plugin_json_path, 'r', encoding='utf-8') as f:
                plugin_data = json.load(f)

            plugin_data['version'] = new_version

            with open(plugin_json_path, 'w', encoding='utf-8') as f:
                json.dump(plugin_data, f, ensure_ascii=False, indent=2)
                f.write('\n')

            # Extract plugin path relative to plugins/ for display
            relative_path = plugin_json_path.relative_to(plugins_dir).parent.parent
            updated_plugins.append(str(relative_path))
        except Exception as e:
            relative_path = plugin_json_path.relative_to(plugins_dir).parent.parent
            failed_items.append({
                'path': str(relative_path),
                'error': str(e)
            })

    return updated_plugins, failed_items


def find_pyproject_paths(base_dir: Path) -> List[Path]:
    """Find all pyproject.toml files in base_dir, lib, and plugin subdirectories."""
    pyproject_paths = []

    # Add root pyproject.toml
    root_pyproject = base_dir / 'pyproject.toml'
    if root_pyproject.exists():
        pyproject_paths.append(root_pyproject)

    # Add lib/pyproject.toml
    lib_pyproject = base_dir / 'lib' / 'pyproject.toml'
    if lib_pyproject.exists():
        pyproject_paths.append(lib_pyproject)

    # Find all plugin pyproject.toml files
    plugins_dir = base_dir / 'plugins'
    if plugins_dir.exists():
        # Find in code, style, and utility plugin directories
        for plugin_pyproject in sorted(plugins_dir.glob('*/pyproject.toml')):
            pyproject_paths.append(plugin_pyproject)
        for plugin_pyproject in sorted(plugins_dir.glob('*/*/pyproject.toml')):
            pyproject_paths.append(plugin_pyproject)

    return pyproject_paths


def update_pyproject_versions(base_dir: Path, pyproject_paths: List[Path], new_version: str) -> tuple:
    """Update version in all pyproject.toml files.

    Returns:
        Tuple of (updated_files list, failed_items list)
    """
    updated_files = []
    failed_items = []

    for pyproject_path in pyproject_paths:
        try:
            if not pyproject_path.exists():
                failed_items.append({
                    'path': str(pyproject_path.relative_to(base_dir)),
                    'error': 'File not found'
                })
                continue

            with open(pyproject_path, 'r', encoding='utf-8') as f:
                data = toml.load(f)

            # Update version in [project] section
            if 'project' in data:
                data['project']['version'] = new_version

                with open(pyproject_path, 'w', encoding='utf-8') as f:
                    toml.dump(data, f)

                relative_path = pyproject_path.relative_to(base_dir)
                updated_files.append(str(relative_path))
            else:
                failed_items.append({
                    'path': str(pyproject_path.relative_to(base_dir)),
                    'error': '[project] section not found'
                })
        except Exception as e:
            failed_items.append({
                'path': str(pyproject_path.relative_to(base_dir)),
                'error': str(e)
            })

    return updated_files, failed_items


def run_uv_lock_update(pyproject_paths: List[Path]) -> tuple:
    """Run 'uv lock -U' in each directory containing pyproject.toml.

    Returns:
        Tuple of (updated_locks list, failed_items list)
    """
    updated_locks = []
    failed_items = []
    processed_dirs = set()

    for pyproject_path in pyproject_paths:
        if not pyproject_path.exists():
            continue

        # Get the directory containing pyproject.toml
        project_dir = pyproject_path.parent

        # Skip if we already processed this directory
        if project_dir in processed_dirs:
            continue

        processed_dirs.add(project_dir)

        try:
            console.print(f"  Running 'uv update' in {project_dir}...")
            result = subprocess.run(
                ['uv', 'lock', '-U', "&&", "uv", "sync"],
                cwd=project_dir,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0:
                updated_locks.append(str(project_dir))
            else:
                failed_items.append({
                    'path': str(project_dir),
                    'error': result.stderr or 'Unknown error'
                })
        except subprocess.TimeoutExpired:
            failed_items.append({
                'path': str(project_dir),
                'error': 'Command timed out'
            })
        except Exception as e:
            failed_items.append({
                'path': str(project_dir),
                'error': str(e)
            })

    return updated_locks, failed_items


def main():
    base_dir = Path(__file__).parent.parent
    marketplace_path = base_dir / '.claude-plugin' / 'marketplace.json'
    version_path = base_dir / '.version'
    plugins_dir = base_dir / 'plugins'

    if not marketplace_path.exists():
        console.print(f"[red]Error: marketplace.json not found at {marketplace_path}[/red]")
        return 1

    if not version_path.exists():
        console.print(f"[red]Error: .version file not found at {version_path}[/red]")
        return 1

    # Read current version from .version file
    with open(version_path, 'r', encoding='utf-8') as f:
        old_version_full = f.read().strip()

    # Increment version (get 3-part format for marketplace/plugins, 4-part for .version)
    new_version = increment_version(old_version_full, include_build=False)
    new_version_full = increment_version(old_version_full, include_build=True)

    console.print("\n[bold cyan]Updating versions...[/bold cyan]")

    # Update marketplace.json with 3-part version
    with open(marketplace_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    data['metadata']['version'] = new_version

    for plugin in data['plugins']:
        plugin['version'] = new_version

    with open(marketplace_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')

    console.print(f"  [green]✓[/green] marketplace.json: {old_version_full} → {new_version}")

    # Update plugin.json files with 3-part version
    updated_plugins, failed_plugins = update_plugin_versions(plugins_dir, new_version)
    console.print(f"  [green]✓[/green] Updated {len(updated_plugins)} plugin.json(s)")
    for plugin_name in updated_plugins:
        console.print(f"    - {plugin_name}: {old_version_full} → {new_version}")

    # Update pyproject.toml files with 3-part version
    pyproject_paths = find_pyproject_paths(base_dir)
    updated_pyprojects, failed_pyprojects = update_pyproject_versions(base_dir, pyproject_paths, new_version)
    console.print(f"  [green]✓[/green] Updated {len(updated_pyprojects)} pyproject.toml file(s)")
    for file_path in updated_pyprojects:
        console.print(f"    - {file_path}: {old_version_full} → {new_version}")

    # Run 'uv lock -U' in each directory with pyproject.toml
    console.print("\n[bold cyan]Updating uv.lock files...[/bold cyan]")
    updated_locks, failed_locks = run_uv_lock_update(pyproject_paths)
    console.print(f"  [green]✓[/green] Updated {len(updated_locks)} uv.lock file(s)")
    for lock_dir in updated_locks:
        console.print(f"    - {lock_dir}")

    # Update .version file with 4-part version
    with open(version_path, 'w', encoding='utf-8') as f:
        f.write(new_version_full)

    console.print(f"  [green]✓[/green] .version: {old_version_full} → {new_version_full}")

    # Print summary
    console.print(f"\n[bold green]Version update completed: {old_version_full} → {new_version_full}[/bold green]")

    # Print all failures if any
    all_failures = []
    if failed_plugins:
        all_failures.append(('Plugin Files', failed_plugins))
    if failed_pyprojects:
        all_failures.append(('Pyproject Files', failed_pyprojects))
    if failed_locks:
        all_failures.append(('UV Lock Updates', failed_locks))

    if all_failures:
        console.print("\n[bold red]Failures Summary:[/bold red]")
        for category, failures in all_failures:
            console.print(f"\n[red]{category}:[/red]")
            for item in failures:
                console.print(f"  [red]✗[/red] {item['path']}")
                console.print(f"      Error: {item['error']}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())