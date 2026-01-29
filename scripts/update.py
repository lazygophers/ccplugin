#!/usr/bin/env python3
"""
Update enabled plugins from marketplaces.

This script:
1. Reads enabledPlugins from .claude/settings.json and .claude/settings.local.json
2. Updates marketplaces via git pull
3. Gets latest versions from marketplace.json
4. Copies new plugin versions to cache directory
5. Updates installed_plugins.json with latest versions
"""

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
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

console = Console()


class UpdateStats:
    """Statistics for the update process."""

    def __init__(self) -> None:
        self.updated_count = 0
        self.skipped_count = 0
        self.error_count = 0
        self.market_updated = 0
        self.market_failed = 0
        self.copied_count = 0
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
        if self.copied_count > 0:
            table.add_row("New Versions Copied", str(self.copied_count))
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


def is_valid_semver(version: str) -> bool:
    """Check if version string is a valid 3-part semantic version.

    Args:
        version: Version string to validate

    Returns:
        True if version is in X.Y.Z format, False otherwise
    """
    parts = version.split(".")
    if len(parts) != 3:
        return False
    try:
        int(parts[0])
        int(parts[1])
        int(parts[2])
        return True
    except ValueError:
        return False


def get_plugin_latest_version(market: str, plugin: str) -> str | None:
    """Get latest version of a plugin from marketplace.json.

    Args:
        market: Marketplace name
        plugin: Plugin name

    Returns:
        Latest version string, "1.0.0" if not found or invalid, or existing cache version
    """
    marketplace_data = read_marketplace_json(market)

    if not marketplace_data:
        return None

    for p in marketplace_data.get("plugins", []):
        if p.get("name") == plugin:
            # Return version if present and valid semver
            if "version" in p:
                version = p["version"]
                if is_valid_semver(version):
                    return version
            # No valid version in marketplace.json, check cache for existing version
            cache_base = Path.home() / ".claude" / "plugins" / "cache" / market / plugin
            if cache_base.exists():
                existing_versions = [d.name for d in cache_base.iterdir() if d.is_dir()]
                # Prefer valid semver versions from cache
                for v in existing_versions:
                    if is_valid_semver(v):
                        return v
                # If no valid semver in cache, use first available
                if existing_versions:
                    return existing_versions[0]
            # Default to 1.0.0 if no valid version info available
            return "1.0.0"

    return None


def get_plugin_source_path(market: str, plugin: str) -> Path | None:
    """Get source path of a plugin from marketplace directory.

    Args:
        market: Marketplace name
        plugin: Plugin name

    Returns:
        Path to plugin source directory or None if not found
    """
    marketplace_data = read_marketplace_json(market)

    if not marketplace_data:
        return None

    for p in marketplace_data.get("plugins", []):
        if p.get("name") == plugin:
            source = p.get("source")
            if source:
                market_dir = get_marketplace_dir(market)
                return market_dir / source.lstrip("./")

    return None


def get_cache_dir(market: str, plugin: str, version: str) -> Path:
    """Get cache directory path for a plugin version.

    Args:
        market: Marketplace name
        plugin: Plugin name
        version: Plugin version

    Returns:
        Path to cache directory
    """
    return Path.home() / ".claude" / "plugins" / "cache" / market / plugin / version


def copy_plugin_to_cache(
    market: str,
    plugin: str,
    version: str,
    source_path: Path,
    stats: UpdateStats,
) -> bool:
    """Copy plugin from marketplace to cache directory.

    Args:
        market: Marketplace name
        plugin: Plugin name
        version: Plugin version
        source_path: Path to plugin source directory
        stats: Statistics object to track results

    Returns:
        True if successful, False otherwise
    """
    cache_dir = get_cache_dir(market, plugin, version)

    # Skip if already exists
    if cache_dir.exists():
        return True

    # Create parent directory
    cache_dir.parent.mkdir(parents=True, exist_ok=True)

    try:
        shutil.copytree(source_path, cache_dir)
        stats.copied_count += 1
        stats.add_message(
            "success",
            f"Copied [cyan]{plugin}@{market}[/cyan] [dim]@[/dim] [bold]{version}[/bold] to cache",
        )

        # Initialize virtual environment if plugin has pyproject.toml
        pyproject_path = cache_dir / "pyproject.toml"
        if pyproject_path.exists():
            try:
                # Run uv sync to create virtual environment and install dependencies
                result = subprocess.run(
                    ["uv", "sync"],
                    cwd=cache_dir,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                if result.returncode == 0:
                    stats.add_message(
                        "info", f"  [dim]Initialized venv for {plugin}[/dim]"
                    )
                else:
                    stats.add_message(
                        "warning",
                        f"  [yellow]uv sync failed for {plugin}: {result.stderr.strip()}[/yellow]",
                    )
            except subprocess.TimeoutExpired:
                stats.add_message(
                    "warning", f"  [yellow]uv sync timeout for {plugin}[/yellow]"
                )
            except Exception as e:
                stats.add_message(
                    "warning", f"  [yellow]uv sync error for {plugin}: {e}[/yellow]"
                )

        return True
    except Exception as e:
        stats.add_message("error", f"Failed to copy {plugin}@{market}: {e}")
        return False


def read_installed_plugins() -> dict[str, Any]:
    """Read the installed_plugins.json file.

    Returns:
        Dictionary containing installed plugins data
    """
    installed_path = Path.home() / ".claude" / "plugins" / "installed_plugins.json"

    if not installed_path.exists():
        return {"version": 2, "plugins": {}}

    with open(installed_path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_installed_plugins(data: dict[str, Any]) -> None:
    """Write data to installed_plugins.json.

    Args:
        data: Dictionary to write
    """
    installed_path = Path.home() / ".claude" / "plugins" / "installed_plugins.json"
    installed_path.parent.mkdir(parents=True, exist_ok=True)

    with open(installed_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_git_commit_sha(install_path: Path) -> str | None:
    """Get git commit SHA from plugin installation directory.

    Args:
        install_path: Path to the installed plugin directory

    Returns:
        Git commit SHA or None
    """
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

    commit_file = install_path / ".git-commit-sha"
    if commit_file.exists():
        try:
            return commit_file.read_text().strip()
        except Exception:
            pass

    return None


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

    if plugin_key in data["plugins"]:
        plugins_list = data["plugins"][plugin_key]
        updated = False
        for i, p in enumerate(plugins_list):
            if p.get("projectPath") == str(project_path):
                plugins_list[i] = entry
                updated = True
                break
        if not updated:
            plugins_list.append(entry)
    else:
        data["plugins"][plugin_key] = [entry]


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
        description="Update enabled plugins from marketplaces"
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

    # Print header
    console.print(
        Panel.fit(
            f"[bold cyan]Plugin Update Tool[/bold cyan]\n"
            f"[dim]Project:[/dim] {project_path}",
            border_style="blue",
        )
    )

    stats = UpdateStats()

    # Read enabled plugins from settings files
    enabled_plugins = get_enabled_plugins(project_path)

    if not enabled_plugins:
        console.print(
            "[yellow]No enabled plugins found in settings.json or settings.local.json[/yellow]"
        )
        return 0

    # Display enabled plugins
    enabled_table = Table(
        title="[bold]Enabled Plugins[/bold]", show_header=True, header_style="bold cyan"
    )
    enabled_table.add_column("Plugin", style="green")
    enabled_table.add_column("Market", style="blue")
    enabled_table.add_column("Status", style="yellow")

    enabled_list = []
    for plugin_key, enabled in enabled_plugins.items():
        parsed = parse_plugin_key(plugin_key)
        if parsed:
            plugin, market = parsed
            status = "[green]Enabled[/green]" if enabled else "[dim]Disabled[/dim]"
            enabled_table.add_row(plugin, market, status)
            if enabled:
                enabled_list.append(plugin_key)

    console.print(enabled_table)
    console.print(f"[dim]Found {len(enabled_list)} enabled plugin(s)[/dim]\n")

    # Read existing installed_plugins.json
    installed_data = read_installed_plugins()

    # Collect unique markets
    markets = set()
    for plugin_key in enabled_plugins:
        parsed = parse_plugin_key(plugin_key)
        if parsed:
            _, market = parsed
            markets.add(market)

    # Update marketplaces
    if markets:
        console.print("[bold cyan]Updating Marketplaces[/bold cyan]")
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                "[cyan]Updating markets...[/cyan]", total=len(markets)
            )
            for market in sorted(markets):
                progress.update(task, description=f"[cyan]Updating {market}...[/cyan]")
                update_marketplace(market, stats)
                progress.advance(task)
        console.print()

    # Process plugins
    console.print("[bold cyan]Processing Plugins[/bold cyan]")
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(
            "[cyan]Processing plugins...[/cyan]", total=len(enabled_list)
        )

        for plugin_key in enabled_plugins:
            if not enabled_plugins[plugin_key]:
                stats.skipped_count += 1
                stats.add_message("info", f"Skipped [dim]{plugin_key}[/dim] (disabled)")
                progress.advance(task)
                continue

            parsed = parse_plugin_key(plugin_key)
            if not parsed:
                stats.error_count += 1
                stats.add_message("error", f"Invalid plugin key format: {plugin_key}")
                progress.advance(task)
                continue

            plugin, market = parsed
            progress.update(task, description=f"[cyan]Processing {plugin}...[/cyan]")

            # Get latest version from marketplace
            version = get_plugin_latest_version(market, plugin)

            if not version:
                stats.error_count += 1
                stats.add_message(
                    "warning", f"Plugin {plugin_key} not found in marketplace.json"
                )
                progress.advance(task)
                continue

            # Get source path
            source_path = get_plugin_source_path(market, plugin)

            if not source_path or not source_path.exists():
                stats.error_count += 1
                stats.add_message(
                    "error", f"Source path not found for {plugin_key}: {source_path}"
                )
                progress.advance(task)
                continue

            # Copy to cache if not exists
            cache_dir = get_cache_dir(market, plugin, version)
            if not cache_dir.exists():
                if not args.dry_run:
                    if not copy_plugin_to_cache(
                        market, plugin, version, source_path, stats
                    ):
                        progress.advance(task)
                        continue
                else:
                    stats.add_message(
                        "info",
                        f"[DRY RUN] Would copy {plugin_key} @ {version} to cache",
                    )

            stats.updated_count += 1
            stats.add_message(
                "success",
                f"Updated [cyan]{plugin_key}[/cyan] [dim]@[/dim] [bold]{version}[/bold]",
            )

            if not args.dry_run:
                update_or_add_plugin(
                    installed_data, plugin_key, project_path, cache_dir, version
                )

            progress.advance(task)

    # Write back to installed_plugins.json
    if not args.dry_run:
        write_installed_plugins(installed_data)
        console.print(
            Panel(
                "[green]✓[/green] [bold]Updated:[/bold] [dim]~/.claude/plugins/installed_plugins.json[/dim]",
                border_style="green",
            )
        )
    else:
        console.print(
            Panel(
                "[yellow]⚠[/yellow] [bold]DRY RUN MODE[/bold] - [dim]No changes made[/dim]",
                border_style="yellow",
            )
        )

    # Print summary
    console.print()
    stats.print_summary()

    return 0


if __name__ == "__main__":
    sys.exit(main())
