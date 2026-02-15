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
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from lib.utils import print_help

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


def get_plugin_source(market: str, plugin_name: str) -> str | None:
    """Get plugin source path from marketplace.json.

    Args:
        market: Marketplace name
        plugin_name: Plugin name

    Returns:
        Plugin source path or None if not found
    """
    marketplace_data = read_marketplace_json(market)
    if not marketplace_data:
        return None

    plugins = marketplace_data.get("plugins", [])
    for plugin in plugins:
        if plugin.get("name") == plugin_name:
            return plugin.get("source")

    return None


def get_plugin_dir(market: str, plugin_name: str) -> Path:
    """Get the plugin directory path.

    Args:
        market: Marketplace name (e.g., 'ccplugin-market')
        plugin_name: Plugin name

    Returns:
        Path to the plugin directory
    """
    market_dir = get_marketplace_dir(market)

    # Try to get source from marketplace.json first
    source = get_plugin_source(market, plugin_name)
    if source:
        # Remove leading './' from source
        source = source.lstrip("./")
        return market_dir / source

    # Fallback to simple path
    return market_dir / plugin_name


def read_plugin_json(market: str, plugin_name: str) -> dict[str, Any] | None:
    """Read plugin.json from plugin directory.

    Args:
        market: Marketplace name
        plugin_name: Plugin name

    Returns:
        Plugin data or None if not found
    """
    plugin_dir = get_plugin_dir(market, plugin_name)
    plugin_json = plugin_dir / ".claude-plugin" / "plugin.json"

    if not plugin_json.exists():
        return None

    with open(plugin_json, "r", encoding="utf-8") as f:
        return json.load(f)


def read_hooks_json(market: str, plugin_name: str) -> dict[str, Any] | None:
    """Read hooks.json from plugin directory.

    Args:
        market: Marketplace name
        plugin_name: Plugin name

    Returns:
        Hooks data or None if not found
    """
    plugin_dir = get_plugin_dir(market, plugin_name)
    hooks_json = plugin_dir / "hooks" / "hooks.json"

    if not hooks_json.exists():
        return None

    with open(hooks_json, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_name_from_path(path: str) -> str:
    """Extract component name from file path.

    Args:
        path: File path (e.g., './commands/hello.md')

    Returns:
        Extracted name without extension (e.g., 'hello')
    """
    # Remove leading './' or trailing slashes
    path = path.lstrip("./").strip("/")

    # Get the filename without extension
    filename = Path(path).stem

    return filename


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

            plugin_node = plugins_branch.add(plugin_text)

            # Show components for enabled plugins
            if enabled_plugins.get(plugin_id, False):
                plugin_data = read_plugin_json(market_name, plugin_name)
                hooks_data = read_hooks_json(market_name, plugin_name)

                # Collect all components to display
                components_to_show = []

                if plugin_data:
                    # Commands
                    commands = plugin_data.get("commands", [])
                    if commands:
                        command_names = [extract_name_from_path(cmd) for cmd in commands]
                        components_to_show.append(("Commands", ", ".join(command_names)))

                    # Agents
                    agents = plugin_data.get("agents", [])
                    if agents:
                        agent_names = [extract_name_from_path(agent) for agent in agents]
                        components_to_show.append(("Agents", ", ".join(agent_names)))

                    # Skills
                    skills = plugin_data.get("skills", [])
                    if skills:
                        # For skills directory, list subdirectories
                        plugin_dir = get_plugin_dir(market_name, plugin_name)
                        skills_dir = plugin_dir / skills.strip("./")
                        skill_names = []
                        if skills_dir.exists():
                            for item in skills_dir.iterdir():
                                if item.is_dir() and (item / "SKILL.md").exists():
                                    skill_names.append(item.name)
                        if skill_names:
                            components_to_show.append(("Skills", ", ".join(skill_names)))

                    # Inline hooks from plugin.json
                    inline_hooks = plugin_data.get("hooks", {})
                    if inline_hooks and isinstance(inline_hooks, dict):
                        hook_events = list(inline_hooks.keys())
                        components_to_show.append(("Hooks", ", ".join(hook_events)))
                    elif inline_hooks and isinstance(inline_hooks, list):
                        # Array format: ["./hooks/pre-tool-use.md", ...]
                        hook_names = [extract_name_from_path(hook) for hook in inline_hooks]
                        components_to_show.append(("Hooks", ", ".join(hook_names)))

                # Show hooks from hooks.json
                if hooks_data:
                    hooks_dict = hooks_data.get("hooks", {})
                    if hooks_dict:
                        hook_events = list(hooks_dict.keys())
                        components_to_show.append(("Hook Events", ", ".join(hook_events)))

                # Display all components
                for component_type, component_names in components_to_show:
                    plugin_node.add(f"[dim]{component_type}: {component_names}[/dim]")

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

    # Detailed components for enabled plugins
    tree = Tree("[bold green]✓ Enabled Plugins Details[/bold green]")

    for plugin_id, enabled in sorted(enabled_plugins.items()):
        if not enabled:
            continue

        if "@" in plugin_id:
            plugin_name, market = plugin_id.split("@", 1)
        else:
            plugin_name = plugin_id
            market = "unknown"

        # Plugin node
        plugin_node = tree.add(f"[bold cyan]{plugin_name}[/bold cyan] [dim]@ {market}[/dim]")

        # Read plugin data
        plugin_data = read_plugin_json(market, plugin_name)
        hooks_data = read_hooks_json(market, plugin_name)

        # Collect all components to display
        components_to_show = []

        if plugin_data:
            # Commands
            commands = plugin_data.get("commands", [])
            if commands:
                command_names = [extract_name_from_path(cmd) for cmd in commands]
                components_to_show.append(("Commands", ", ".join(command_names)))

            # Agents
            agents = plugin_data.get("agents", [])
            if agents:
                agent_names = [extract_name_from_path(agent) for agent in agents]
                components_to_show.append(("Agents", ", ".join(agent_names)))

            # Skills
            skills = plugin_data.get("skills", [])
            if skills:
                # For skills directory, list subdirectories
                plugin_dir = get_plugin_dir(market, plugin_name)
                skills_dir = plugin_dir / skills.strip("./")
                skill_names = []
                if skills_dir.exists():
                    for item in skills_dir.iterdir():
                        if item.is_dir() and (item / "SKILL.md").exists():
                            skill_names.append(item.name)
                if skill_names:
                    components_to_show.append(("Skills", ", ".join(skill_names)))

            # Inline hooks from plugin.json
            inline_hooks = plugin_data.get("hooks", {})
            if inline_hooks and isinstance(inline_hooks, dict):
                hook_events = list(inline_hooks.keys())
                components_to_show.append(("Hooks", ", ".join(hook_events)))
            elif inline_hooks and isinstance(inline_hooks, list):
                # Array format: ["./hooks/pre-tool-use.md", ...]
                hook_names = [extract_name_from_path(hook) for hook in inline_hooks]
                components_to_show.append(("Hooks", ", ".join(hook_names)))

        # Show hooks from hooks.json
        if hooks_data:
            hooks_dict = hooks_data.get("hooks", {})
            if hooks_dict:
                hook_events = list(hooks_dict.keys())
                components_to_show.append(("Hook Events", ", ".join(hook_events)))

        # Display all components
        for component_type, component_names in components_to_show:
            plugin_node.add(f"[dim]{component_type}: {component_names}[/dim]")

        # Add empty line if there were components
        if components_to_show:
            plugin_node.add("")

    console.print(Panel(tree, title="[bold]Plugin Components[/bold]", title_align="left"))
    console.print()


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="info.py",
        description="📊 CCPlugin 信息工具 - 显示已注册的市场和插件信息",
        add_help=False,
    )
    parser.add_argument(
        "--enabled",
        action="store_true",
        help="仅显示当前项目已启用的插件",
    )
    parser.add_argument(
        "--project-dir",
        type=str,
        default=".",
        help="项目目录 (默认: 当前目录)",
        metavar="PATH",
    )
    parser.add_argument(
        "-h", "--help",
        action="store_true",
        help="显示帮助信息",
    )

    args = parser.parse_args()

    if args.help:
        print_help(parser, console)
        return

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
