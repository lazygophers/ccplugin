#!/usr/bin/env python3
import json
import os
import shutil
import toml
from pathlib import Path
from typing import List


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


def update_plugin_versions(plugins_dir: Path, new_version: str) -> list:
    """Recursively scan and update all plugin.json files under plugins directory."""
    updated_plugins = []

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
            print(f"  Error processing {plugin_json_path}: {e}")

    return updated_plugins


def find_pyproject_paths(base_dir: Path) -> List[Path]:
    """Find all pyproject.toml files in base_dir and plugin subdirectories."""
    pyproject_paths = []

    # Add root pyproject.toml
    root_pyproject = base_dir / 'pyproject.toml'
    if root_pyproject.exists():
        pyproject_paths.append(root_pyproject)

    # Find all plugin pyproject.toml files
    plugins_dir = base_dir / 'plugins'
    if plugins_dir.exists():
        # Find in code, style, and utility plugin directories
        for plugin_pyproject in sorted(plugins_dir.glob('*/pyproject.toml')):
            pyproject_paths.append(plugin_pyproject)
        for plugin_pyproject in sorted(plugins_dir.glob('*/*/pyproject.toml')):
            pyproject_paths.append(plugin_pyproject)

    return pyproject_paths


def update_pyproject_versions(base_dir: Path, pyproject_paths: List[Path], new_version: str) -> list:
    """Update version in all pyproject.toml files."""
    updated_files = []

    for pyproject_path in pyproject_paths:
        try:
            if not pyproject_path.exists():
                print(f"  Warning: {pyproject_path} not found")
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
                print(f"  Warning: [project] section not found in {pyproject_path}")
        except Exception as e:
            print(f"  Error processing {pyproject_path}: {e}")

    return updated_files


def sync_lib_to_plugins(base_dir: Path) -> List[str]:
    """Auto-sync lib directory to all plugins that have pyproject.toml.

    Copies entire lib/ directory to each plugin's scripts/lib/, excluding:
    - .venv
    - build
    - pyproject.toml
    - uv.lock
    - __pycache__
    - .ruff_cache

    Args:
        base_dir: Project root directory

    Returns:
        List of plugins where lib was synced
    """
    synced_plugins = []
    lib_dir = base_dir / 'lib'
    plugins_dir = base_dir / 'plugins'

    if not lib_dir.exists():
        print(f"  Warning: lib directory not found at {lib_dir}")
        return synced_plugins

    # Find all plugins (directories with pyproject.toml)
    plugins_with_pyproject = list(plugins_dir.glob('**/pyproject.toml'))

    for pyproject_path in sorted(plugins_with_pyproject):
        plugin_root = pyproject_path.parent

        # Skip if it's the lib directory itself
        if plugin_root == lib_dir:
            continue

        # Create scripts/lib directory in plugin
        plugin_lib_dir = plugin_root / 'scripts' / 'lib'

        # Remove existing lib directory
        if plugin_lib_dir.exists():
            shutil.rmtree(plugin_lib_dir)

        plugin_lib_dir.mkdir(parents=True, exist_ok=True)

        # Copy lib directory with exclusions
        for item in lib_dir.iterdir():
            # Skip excluded items
            if item.name in ['.venv', 'build', 'pyproject.toml', 'uv.lock', '__pycache__', '.ruff_cache']:
                continue

            src = lib_dir / item.name
            dst = plugin_lib_dir / item.name

            if item.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)

        # Create __init__.py
        (plugin_lib_dir / '__init__.py').touch()

        # Record plugin path for display
        relative_path = plugin_root.relative_to(plugins_dir)
        synced_plugins.append(str(relative_path))

    return synced_plugins


def main():
    base_dir = Path(__file__).parent.parent
    marketplace_path = base_dir / '.claude-plugin' / 'marketplace.json'
    version_path = base_dir / '.version'
    plugins_dir = base_dir / 'plugins'

    if not marketplace_path.exists():
        print(f"Error: marketplace.json not found at {marketplace_path}")
        return 1
    
    if not version_path.exists():
        print(f"Error: .version file not found at {version_path}")
        return 1

    # Read current version from .version file
    with open(version_path, 'r', encoding='utf-8') as f:
        old_version_full = f.read().strip()
    
    # Increment version (get 3-part format for marketplace/plugins, 4-part for .version)
    new_version = increment_version(old_version_full, include_build=False)
    new_version_full = increment_version(old_version_full, include_build=True)

    print("Updating versions...")

    # Update marketplace.json with 3-part version
    with open(marketplace_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    data['metadata']['version'] = new_version
    
    for plugin in data['plugins']:
        plugin['version'] = new_version
    
    with open(marketplace_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')
    
    print(f"  marketplace.json: {old_version_full} -> {new_version}")

    # Update plugin.json files with 3-part version
    updated_plugins = update_plugin_versions(plugins_dir, new_version)
    print(f"  Updated {len(updated_plugins)} plugin.json(s):")
    for plugin_name in updated_plugins:
        print(f"    - {plugin_name}: {old_version_full} -> {new_version}")

    # Update pyproject.toml files with 3-part version
    pyproject_paths = find_pyproject_paths(base_dir)
    updated_pyprojects = update_pyproject_versions(base_dir, pyproject_paths, new_version)
    print(f"  Updated {len(updated_pyprojects)} pyproject.toml file(s):")
    for file_path in updated_pyprojects:
        print(f"    - {file_path}: {old_version_full} -> {new_version}")

    # Update .version file with 4-part version
    with open(version_path, 'w', encoding='utf-8') as f:
        f.write(new_version_full)

    print(f"  .version: {old_version_full} -> {new_version_full}")

    # Sync lib directory to all plugins with pyproject.toml
    print("\nSyncing lib directory to all plugins...")
    synced_plugins = sync_lib_to_plugins(base_dir)
    if synced_plugins:
        print(f"  Synced lib to {len(synced_plugins)} plugin(s):")
        for plugin_path in synced_plugins:
            print(f"    - {plugin_path}")
    else:
        print("  No plugins to sync lib to")

    print(f"\nVersion update completed: {old_version_full} -> {new_version_full}")
    return 0


if __name__ == '__main__':
    exit(main())
