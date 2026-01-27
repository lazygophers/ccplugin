#!/usr/bin/env python3
"""
Register enabled plugins to installed_plugins.json.

This script reads enabledPlugins from .claude/settings.json and registers
them to ~/.claude/plugins/installed_plugins.json with versions from cache.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _version_key(version: str) -> tuple:
    """Convert version string to a sortable tuple.

    Handles semantic versions (e.g., '0.0.91') and git SHAs (e.g., '96276205880a').

    Args:
        version: Version string to parse

    Returns:
        Tuple that can be used for sorting: (is_semantic, semantic_parts, version_string)
        - is_semantic: False (semantic versions sort first)
        - semantic_parts: List of integers for semantic versions, empty list for git SHAs
        - version_string: Original version string as fallback
    """
    try:
        # Try to parse as semantic version (e.g., '0.0.91')
        parts = [int(x) for x in version.split(".")]
        return (False, parts, version)
    except ValueError:
        # Not a semantic version (e.g., git SHA), sort as string
        return (True, [], version)


def get_latest_version_from_cache(market: str, plugin: str) -> str | None:
    """Get the latest version from plugin cache directory.

    Args:
        market: Marketplace name (e.g., 'ccplugin-market')
        plugin: Plugin name (e.g., 'git')

    Returns:
        Latest version string or None if not found
    """
    cache_dir = Path.home() / ".claude" / "plugins" / "cache" / market / plugin

    if not cache_dir.exists():
        return None

    # Find all version directories
    version_dirs = [d for d in cache_dir.iterdir() if d.is_dir()]

    if not version_dirs:
        return None

    # Sort by version string (semantic versions first, then alphabetically)
    versions = [d.name for d in version_dirs]
    versions.sort(key=_version_key)

    return versions[-1] if versions else None


def get_git_commit_sha(install_path: Path) -> str | None:
    """Get git commit SHA from plugin installation directory.

    Args:
        install_path: Path to the installed plugin directory

    Returns:
        Git commit SHA or None
    """
    # Try to find .git/HEAD or similar
    head_file = install_path / ".git" / "HEAD"
    if head_file.exists():
        try:
            content = head_file.read_text().strip()
            if content.startswith("ref:"):
                ref_path = install_path / ".git" / content[5:]
                if ref_path.exists():
                    return ref_path.read_text().strip()
            else:
                return content
        except Exception:
            pass

    # Check for .git-commit-sha file (some plugins use this)
    commit_file = install_path / ".git-commit-sha"
    if commit_file.exists():
        try:
            return commit_file.read_text().strip()
        except Exception:
            pass

    return None


def read_settings_json(project_dir: Path) -> dict[str, bool]:
    """Read enabledPlugins from .claude/settings.json.

    Args:
        project_dir: Path to the project directory

    Returns:
        Dictionary of enabled plugins (plugin@market -> bool)
    """
    settings_path = project_dir / ".claude" / "settings.json"

    if not settings_path.exists():
        print(f"Error: settings.json not found at {settings_path}")
        sys.exit(1)

    with open(settings_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("enabledPlugins", {})


def read_installed_plugins() -> dict[str, Any]:
    """Read the installed_plugins.json file.

    Returns:
        Dictionary containing installed plugins data
    """
    installed_path = Path.home() / ".claude" / "plugins" / "installed_plugins.json"

    if not installed_path.exists():
        # Create default structure
        return {"version": 2, "plugins": {}}

    with open(installed_path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_installed_plugins(data: dict[str, Any]) -> None:
    """Write data to installed_plugins.json.

    Args:
        data: Dictionary to write
    """
    installed_path = Path.home() / ".claude" / "plugins" / "installed_plugins.json"

    # Ensure parent directory exists
    installed_path.parent.mkdir(parents=True, exist_ok=True)

    with open(installed_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


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


def update_or_add_plugin(
    data: dict[str, Any],
    plugin_key: str,
    project_path: Path,
    install_path: Path,
    version: str,
) -> None:
    """Update or add a plugin to installed_plugins.json.

    Args:
        data: The installed_plugins data structure
        plugin_key: Plugin key in format 'plugin@market'
        project_path: Path to the project
        install_path: Path to the installed plugin
        version: Plugin version
    """
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    commit_sha = get_git_commit_sha(install_path)

    entry = {
        "scope": "project",
        "projectPath": str(project_path),
        "installPath": str(install_path),
        "version": version,
        "installedAt": now,
        "lastUpdated": now,
    }

    if commit_sha:
        entry["gitCommitSha"] = commit_sha

    # Check if plugin already exists for this project
    if plugin_key in data["plugins"]:
        plugins_list = data["plugins"][plugin_key]
        # Find existing entry for this project
        updated = False
        for i, p in enumerate(plugins_list):
            if p.get("projectPath") == str(project_path):
                # Update existing entry
                plugins_list[i] = entry
                updated = True
                break
        if not updated:
            plugins_list.append(entry)
    else:
        # Add new plugin
        data["plugins"][plugin_key] = [entry]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Register enabled plugins to installed_plugins.json"
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

    args = parser.parse_args()
    project_path = args.project_path.resolve()

    print(f"Project path: {project_path}")

    # Read enabled plugins from settings.json
    enabled_plugins = read_settings_json(project_path)

    if not enabled_plugins:
        print("No enabled plugins found in settings.json")
        return 0

    print(f"Found {len(enabled_plugins)} enabled plugin(s)")

    # Read existing installed_plugins.json
    installed_data = read_installed_plugins()

    # Process each enabled plugin
    registered_count = 0
    skipped_count = 0

    for plugin_key, enabled in enabled_plugins.items():
        if not enabled:
            print(f"  Skipping {plugin_key} (disabled)")
            continue

        parsed = parse_plugin_key(plugin_key)
        if not parsed:
            print(f"  Warning: Invalid plugin key format: {plugin_key}")
            skipped_count += 1
            continue

        plugin, market = parsed

        # Get latest version from cache
        version = get_latest_version_from_cache(market, plugin)

        if not version:
            print(f"  Warning: No cache found for {plugin_key}, skipping")
            skipped_count += 1
            continue

        install_path = (
            Path.home() / ".claude" / "plugins" / "cache" / market / plugin / version
        )

        if not install_path.exists():
            print(f"  Warning: Install path not found: {install_path}, skipping")
            skipped_count += 1
            continue

        print(f"  Registering {plugin_key} @ {version}")

        if not args.dry_run:
            update_or_add_plugin(
                installed_data, plugin_key, project_path, install_path, version
            )

        registered_count += 1

    # Write back to installed_plugins.json
    if not args.dry_run and registered_count > 0:
        write_installed_plugins(installed_data)
        print("\nUpdated: ~/.claude/plugins/installed_plugins.json")
    elif args.dry_run:
        print("\nDry run mode - no changes made")

    print("\nSummary:")
    print(f"  Registered: {registered_count}")
    print(f"  Skipped: {skipped_count}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
