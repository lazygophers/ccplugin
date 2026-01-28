#!/usr/bin/env python3
"""
Display information about registered marketplaces and their plugins.

This script shows:
1. All registered marketplaces from known_marketplaces.json
2. Plugins available in each marketplace from marketplace.json
3. Currently enabled plugins from project settings
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

console = Console()


def get_marketplaces_file() -> Path:
    """Get the known_marketplaces.json file path.

    Returns:
        Path to known_marketplaces.json
    """
    return Path.home() / ".claude" / "plugins" / "known_marketplaces.json"


def get_marketplace_dir(market: str) -> Path:
    """Get the marketplace directory path.

    Args:
        market: Marketplace name (e.g., 'ccplugin-market')

    Returns:
        Path to the marketplace directory
    """
    return Path.home() / ".claude" / "plugins" / "marketplaces" / market


def read_known_marketplaces() -> dict[str, Any] | None:
    """Read known_marketplaces.json.

    Returns:
        Marketplaces data or None if not found
    """
    marketplaces_file = get_marketplaces_file()
    if not marketplaces_file.exists():
        return None

    with open(marketplaces_file, "r", encoding="utf-8") as f:
        return json.load(f)


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


def read_project_settings(project_dir: Path) -> dict[str, Any]:
    """Read enabled plugins from project settings.

    Args:
        project_dir: Path to the project directory

    Returns:
        Dictionary with enabled plugins from both settings files
    """
    enabled_plugins: dict[str, bool] = {}

    # Read settings.json
    settings_path = project_dir / ".claude" / "settings.json"
    if settings_path.exists():
        with open(settings_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            enabled_plugins.update(data.get("enabledPlugins", {}))

    # Read settings.local.json (overrides)
    settings_local_path = project_dir / ".claude" / "settings.local.json"
    if settings_local_path.exists():
        with open(settings_local_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            enabled_plugins.update(data.get("enabledPlugins", {}))

    return enabled_plugins


def format_timestamp(iso_string: str | None) -> str:
    """Format ISO timestamp to human-readable string.

    Args:
        iso_string: ISO 8601 timestamp string

    Returns:
        Formatted date/time string or 'Unknown' if None
    """
    if not iso_string:
        return "[dim]Unknown[/dim]"

    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        # Convert to local timezone
        local_dt = dt.astimezone()
        return local_dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "[dim]Invalid[/dim]"


def get_status_icon(plugin_id: str, enabled_plugins: dict[str, bool]) -> str:
    """Get status icon for a plugin.

    Args:
        plugin_id: Plugin identifier (name@market)
        enabled_plugins: Dictionary of enabled plugins

    Returns:
        Status icon string
    """
    if enabled_plugins.get(plugin_id, False):
        return "[green]✓[/green]"
    return "[dim]○[/dim]"


def display_marketplaces(enabled_plugins: dict[str, bool]) -> None:
    """Display all marketplaces and their plugins.

    Args:
        enabled_plugins: Dictionary of enabled plugins from project settings
    """
    marketplaces = read_known_marketplaces()

    if not marketplaces:
        console.print("[yellow]No marketplaces found.[/yellow]")
        console.print(
            "Marketplaces are registered in: "
            f"[cyan]{get_marketplaces_file()}[/cyan]"
        )
        return

    # Summary table
    summary_table = Table(
        title="[bold blue]Registered Marketplaces[/bold blue]",
        show_header=True,
        header_style="bold magenta",
    )
    summary_table.add_column("Marketplace", style="cyan", width=30)
    summary_table.add_column("Source", style="white")
    summary_table.add_column("Last Updated", style="yellow")
    summary_table.add_column("Plugins", justify="right", style="green")

    total_plugins = 0

    for market_name, market_info in marketplaces.items():
        source = market_info.get("source", {})
        source_url = source.get("url", "N/A")
        last_updated = format_timestamp(market_info.get("lastUpdated"))

        # Read marketplace.json to get plugin count
        marketplace_data = read_marketplace_json(market_name)
        plugin_count = 0
        if marketplace_data:
            plugins = marketplace_data.get("plugins", [])
            plugin_count = len(plugins)
            total_plugins += plugin_count

        summary_table.add_row(
            market_name,
            f"[dim]{source_url}[/dim]",
            last_updated,
            str(plugin_count),
        )

    console.print(summary_table)
    console.print(f"\n[bold]Total Plugins:[/bold] {total_plugins}\n")

    # Detailed plugin list per marketplace
    for market_name, market_info in marketplaces.items():
        marketplace_data = read_marketplace_json(market_name)

        if not marketplace_data:
            console.print(
                f"[yellow]⚠[/yellow] No marketplace.json found for [cyan]{market_name}[/cyan]\n"
            )
            continue

        plugins = marketplace_data.get("plugins", [])

        # Create tree for this marketplace
        tree = Tree(f"[bold cyan]📦 {market_name}[/bold cyan]")

        # Add marketplace info
        source = market_info.get("source", {})
        install_location = market_info.get("installLocation", "")
        tree.add(
            f"[dim]Source: {source.get('url', 'N/A')}[/dim]"
        )
        tree.add(
            f"[dim]Location: {install_location}[/dim]"
        )
        tree.add(
            f"[dim]Last Updated: {format_timestamp(market_info.get('lastUpdated'))}[/dim]"
        )

        # Add plugins branch
        plugins_branch = tree.add("[bold]Plugins[/bold]")

        for plugin in plugins:
            plugin_name = plugin.get("name", "Unknown")
            version = plugin.get("version", "N/A")
            description = plugin.get("description", "")
            plugin_id = f"{plugin_name}@{market_name}"

            # Status icon
            status_icon = get_status_icon(plugin_id, enabled_plugins)

            # Create plugin entry
            plugin_text = f"{status_icon} [bold white]{plugin_name}[/bold white] [dim]v{version}[/dim]"

            if description:
                # Truncate long descriptions
                if len(description) > 60:
                    description = description[:57] + "..."
                plugin_text += f"\n    [dim]{description}[/dim]"

            plugins_branch.add(plugin_text)

        console.print(Panel(tree, title=f"[bold]{market_name}[/bold]", title_align="left"))
        console.print()


def display_enabled_plugins(enabled_plugins: dict[str, bool]) -> None:
    """Display currently enabled plugins.

    Args:
        enabled_plugins: Dictionary of enabled plugins
    """
    if not enabled_plugins:
        console.print("[dim]No plugins enabled in this project.[/dim]\n")
        return

    table = Table(
        title="[bold green]Enabled Plugins[/bold green]",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Plugin", style="cyan", width=25)
    table.add_column("Marketplace", style="white", width=25)
    table.add_column("Status", justify="center", width=10)

    for plugin_id, enabled in enabled_plugins.items():
        if "@" in plugin_id:
            plugin_name, market = plugin_id.split("@", 1)
        else:
            plugin_name = plugin_id
            market = "unknown"

        status = "[green]Enabled[/green]" if enabled else "[dim]Disabled[/dim]"
        table.add_row(plugin_name, market, status)

    console.print(table)
    console.print()


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Display information about registered marketplaces and plugins"
    )
    parser.add_argument(
        "--enabled",
        action="store_true",
        help="Show only enabled plugins for the current project",
    )
    parser.add_argument(
        "--project-dir",
        type=str,
        default=".",
        help="Project directory (default: current directory)",
    )

    args = parser.parse_args()

    # Get project directory
    project_dir = Path(args.project_dir).resolve()

    # Read enabled plugins from project settings
    enabled_plugins = read_project_settings(project_dir)

    # Print header
    header = (
        "[bold blue]╔══════════════════════════════════════════╗[/bold blue]\n"
        "[bold blue]║     Claude Code Plugin Market Info       ║[/bold blue]\n"
        "[bold blue]╚══════════════════════════════════════════╝[/bold blue]"
    )
    console.print(header)
    console.print()

    if args.enabled:
        # Show only enabled plugins
        display_enabled_plugins(enabled_plugins)
    else:
        # Show all marketplaces and plugins
        display_marketplaces(enabled_plugins)

        # Show enabled plugins section if any
        if enabled_plugins:
            console.print()
            display_enabled_plugins(enabled_plugins)


if __name__ == "__main__":
    main()
