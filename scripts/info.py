#!/usr/bin/env python3
"""
Display information about registered marketplaces and their plugins.

This script uses Claude Code CLI commands to get plugin information:
- `claude plugin marketplace list --json` for marketplaces
- `claude plugin list --json --available` for installed and available plugins
"""

import argparse
import json
import os
import random
import subprocess
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.tree import Tree
from lib.utils import print_help

console = Console()

LOADING_MESSAGES = [
    "🔍 正在搜索插件市场...",
    "📦 正在加载插件列表...",
    "🚀 正在获取最新数据...",
    "✨ 正在整理插件信息...",
    "🎯 正在匹配已安装插件...",
    "🌐 正在连接市场源...",
    "⚡ 正在加速数据传输...",
    "🔮 正在预测你的需求...",
    "🦄 正在召唤插件精灵...",
    "🌟 正在收集星光数据...",
    "🎭 正在准备精彩展示...",
    "🎪 正在搭建插件舞台...",
]


def run_claude_command(args: list[str], description: str = "正在执行命令") -> dict[str, Any] | list[Any] | None:
    """Run a claude CLI command and return JSON output.

    Uses temp file to handle large JSON outputs that exceed pipe buffer.
    Shows a progress bar with animated messages while waiting.

    Args:
        args: Command arguments (e.g., ['plugin', 'list', '--json'])
        description: Description for the progress bar

    Returns:
        Parsed JSON data or None if command fails
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name

    result_container = {"done": False, "data": None}

    def run_command():
        try:
            proc = subprocess.run(
                ["claude"] + args,
                stdout=open(temp_path, 'w'),
                stderr=subprocess.PIPE,
                text=True,
            )
            if proc.returncode == 0:
                with open(temp_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        result_container["data"] = json.loads(content)
        except (subprocess.CalledProcessError, json.JSONDecodeError, OSError):
            pass
        finally:
            result_container["done"] = True

    thread = threading.Thread(target=run_command)
    thread.start()

    with Progress(
        SpinnerColumn("dots", style="cyan"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style="cyan", finished_style="green"),
        TextColumn("[dim]{task.fields[emoji]}[/dim]"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task(description, total=100, emoji="🎯")
        message_idx = 0

        while not result_container["done"]:
            if random.random() < 0.1:
                message_idx = (message_idx + 1) % len(LOADING_MESSAGES)
                progress.update(task, description=LOADING_MESSAGES[message_idx])

            current = progress.tasks[0].completed
            if current < 95:
                advance = random.uniform(0.5, 2.0)
                progress.advance(task, advance=advance)

            emojis = ["✨", "🌟", "💫", "⭐", "🔥", "💎", "🎯", "🚀"]
            progress.update(task, emoji=random.choice(emojis))

            time.sleep(0.1)

        progress.update(task, completed=100, description="✅ 完成!", emoji="🎉")

    thread.join()

    try:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    except OSError:
        pass

    return result_container["data"]


def get_marketplaces() -> list[dict[str, Any]]:
    """Get list of registered marketplaces via CLI.

    Returns:
        List of marketplace dictionaries
    """
    data = run_claude_command(
        ["plugin", "marketplace", "list", "--json"],
        description="🔍 正在获取市场列表..."
    )
    if isinstance(data, list):
        return data
    return []


def get_plugins() -> dict[str, Any]:
    """Get installed and available plugins via CLI.

    Returns:
        Dictionary with 'installed' and 'available' lists
    """
    data = run_claude_command(
        ["plugin", "list", "--json", "--available"],
        description="📦 正在获取插件信息..."
    )
    if isinstance(data, dict):
        return data
    return {"installed": [], "available": []}


def read_project_settings(project_dir: Path) -> dict[str, bool]:
    """Read enabled plugins from project settings.

    Args:
        project_dir: Path to the project directory

    Returns:
        Dictionary with enabled plugins from both settings files
    """
    enabled_plugins: dict[str, bool] = {}

    settings_path = project_dir / ".claude" / "settings.json"
    if settings_path.exists():
        with open(settings_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            enabled_plugins.update(data.get("enabledPlugins", {}))

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
        local_dt = dt.astimezone()
        return local_dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "[dim]Invalid[/dim]"


def format_relative_time(iso_string: str | None) -> str:
    """Format ISO timestamp to relative time string.

    Args:
        iso_string: ISO 8601 timestamp string

    Returns:
        Relative time string (e.g., '2 hours ago')
    """
    if not iso_string:
        return "[dim]Unknown[/dim]"

    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        local_dt = dt.astimezone()
        now = datetime.now(local_dt.tzinfo)
        diff = now - local_dt

        if diff.days > 365:
            years = diff.days // 365
            return f"{years} year{'s' if years > 1 else ''} ago"
        elif diff.days > 30:
            months = diff.days // 30
            return f"{months} month{'s' if months > 1 else ''} ago"
        elif diff.days > 0:
            return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "just now"
    except Exception:
        return "[dim]Invalid[/dim]"


def get_status_icon(enabled: bool) -> str:
    """Get status icon for a plugin.

    Args:
        enabled: Whether the plugin is enabled

    Returns:
        Status icon string
    """
    return "[green]✓[/green]" if enabled else "[dim]○[/dim]"


def get_scope_badge(scope: str) -> str:
    """Get scope badge for display.

    Args:
        scope: Plugin scope ('user' or 'project')

    Returns:
        Formatted scope badge
    """
    if scope == "project":
        return "[blue]📁 project[/blue]"
    return "[magenta]👤 user[/magenta]"


def display_marketplaces_summary(marketplaces: list[dict[str, Any]], plugins_data: dict[str, Any]) -> None:
    """Display marketplaces summary table.

    Args:
        marketplaces: List of marketplace data
        plugins_data: Dictionary with installed and available plugins
    """
    if not marketplaces:
        console.print("[yellow]No marketplaces found.[/yellow]")
        console.print("Add a marketplace with: [cyan]claude plugin marketplace add <url>[/cyan]")
        return

    available_plugins = plugins_data.get("available", [])

    marketplace_plugin_counts: dict[str, int] = {}
    for plugin in available_plugins:
        market_name = plugin.get("marketplaceName", "unknown")
        marketplace_plugin_counts[market_name] = marketplace_plugin_counts.get(market_name, 0) + 1

    table = Table(
        title="[bold blue]📦 Registered Marketplaces[/bold blue]",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Name", style="cyan", width=25)
    table.add_column("Source", style="white")
    table.add_column("Plugins", justify="right", style="green", width=8)

    total_plugins = 0

    for market in marketplaces:
        name = market.get("name", "unknown")
        url = market.get("url", "N/A")
        plugin_count = marketplace_plugin_counts.get(name, 0)
        total_plugins += plugin_count

        source_display = url
        if url.startswith("https://github.com/"):
            parts = url.replace("https://github.com/", "").replace(".git", "")
            source_display = f"[link={url}]{parts}[/link]"

        table.add_row(
            name,
            f"[dim]{source_display}[/dim]",
            str(plugin_count),
        )

    console.print(table)
    console.print(f"\n[bold]Total Available Plugins:[/bold] {total_plugins}\n")


def display_installed_plugins(plugins_data: dict[str, Any], project_enabled: dict[str, bool]) -> None:
    """Display installed plugins grouped by marketplace.

    Args:
        plugins_data: Dictionary with installed plugins
        project_enabled: Project-level enabled plugins settings
    """
    installed = plugins_data.get("installed", [])

    if not installed:
        console.print("[dim]No plugins installed.[/dim]\n")
        return

    grouped: dict[str, list[dict[str, Any]]] = {}
    for plugin in installed:
        market = plugin.get("id", "@").split("@")[-1] if "@" in plugin.get("id", "") else "unknown"
        if market not in grouped:
            grouped[market] = []
        grouped[market].append(plugin)

    table = Table(
        title="[bold green]✓ Installed Plugins[/bold green]",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Plugin", style="cyan", width=18)
    table.add_column("Version", style="yellow", width=10)
    table.add_column("Scope", width=12)
    table.add_column("Status", justify="center", width=6)
    table.add_column("Updated", style="dim", width=12)
    table.add_column("Command", style="cyan", width=38)

    for market, plugins in sorted(grouped.items()):
        for plugin in sorted(plugins, key=lambda p: p.get("id", "")):
            plugin_id = plugin.get("id", "unknown")
            name = plugin_id.split("@")[0] if "@" in plugin_id else plugin_id
            version = plugin.get("version", "N/A")
            scope = plugin.get("scope", "user")
            enabled = plugin.get("enabled", False)
            last_updated = plugin.get("lastUpdated")

            status = get_status_icon(enabled)
            scope_badge = get_scope_badge(scope)
            updated = format_relative_time(last_updated)
            update_cmd = f"[cyan]↻ claude plugin update {plugin_id}[/cyan]"

            table.add_row(name, f"v{version}", scope_badge, status, updated, update_cmd)

        if market != list(grouped.keys())[-1]:
            table.add_section()

    console.print(table)
    console.print()


def display_available_plugins(plugins_data: dict[str, Any], installed_ids: set[str]) -> None:
    """Display available plugins from marketplaces.

    Args:
        plugins_data: Dictionary with available plugins
        installed_ids: Set of installed plugin IDs
    """
    available = plugins_data.get("available", [])

    if not available:
        return

    grouped: dict[str, list[dict[str, Any]]] = {}
    for plugin in available:
        market = plugin.get("marketplaceName", "unknown")
        if market not in grouped:
            grouped[market] = []
        grouped[market].append(plugin)

    for market, plugins in sorted(grouped.items()):
        tree = Tree(f"[bold cyan]📦 {market}[/bold cyan]")

        for plugin in sorted(plugins, key=lambda p: p.get("name", "")):
            name = plugin.get("name", "unknown")
            plugin_id = plugin.get("pluginId", f"{name}@{market}")
            version = plugin.get("version", "N/A")
            description = plugin.get("description", "")
            install_count = plugin.get("installCount", 0)

            is_installed = plugin_id in installed_ids
            status = "[green]✓[/green]" if is_installed else "[dim]○[/dim]"

            plugin_text = f"{status} [bold white]{name}[/bold white] [dim]v{version}[/dim]"

            if description:
                desc_display = description[:70] + "..." if len(description) > 70 else description
                plugin_text += f"\n    [dim]{desc_display}[/dim]"

            if install_count > 0:
                plugin_text += f"\n    [dim]📥 {install_count:,} installs[/dim]"

            if is_installed:
                plugin_text += f"\n    [cyan]↻ claude plugin update {name}@{market}[/cyan]"
            else:
                plugin_text += f"\n    [green]+ claude plugin install {name}@{market}[/green]"

            tree.add(plugin_text)

        console.print(Panel(tree, title=f"[bold]{market}[/bold]", title_align="left"))
        console.print()


def display_enabled_plugins_details(plugins_data: dict[str, Any], project_enabled: dict[str, bool]) -> None:
    """Display detailed information about enabled plugins.

    Args:
        plugins_data: Dictionary with installed plugins
        project_enabled: Project-level enabled plugins settings
    """
    installed = plugins_data.get("installed", [])
    enabled_plugins = [p for p in installed if p.get("enabled", False)]

    if not enabled_plugins:
        return

    tree = Tree("[bold green]✓ Enabled Plugins Details[/bold green]")

    for plugin in sorted(enabled_plugins, key=lambda p: p.get("id", "")):
        plugin_id = plugin.get("id", "unknown")
        name = plugin_id.split("@")[0] if "@" in plugin_id else plugin_id
        market = plugin_id.split("@")[-1] if "@" in plugin_id else "unknown"
        version = plugin.get("version", "N/A")
        scope = plugin.get("scope", "user")
        install_path = plugin.get("installPath", "")

        scope_badge = get_scope_badge(scope)
        plugin_node = tree.add(f"[bold cyan]{name}[/bold cyan] [dim]v{version}[/dim] {scope_badge}")

        if install_path:
            short_path = install_path.replace(str(Path.home()), "~")
            plugin_node.add(f"[dim]📍 {short_path}[/dim]")

        plugin_json_path = Path(install_path) / ".claude-plugin" / "plugin.json"
        if plugin_json_path.exists():
            try:
                with open(plugin_json_path, "r", encoding="utf-8") as f:
                    plugin_json = json.load(f)

                components_to_show = []

                commands = plugin_json.get("commands", [])
                if commands:
                    command_names = [Path(cmd).stem for cmd in commands]
                    components_to_show.append(("Commands", command_names))

                agents = plugin_json.get("agents", [])
                if agents:
                    agent_names = [Path(agent).stem for agent in agents]
                    components_to_show.append(("Agents", agent_names))

                skills = plugin_json.get("skills", [])
                if skills:
                    if isinstance(skills, list):
                        skills_path = skills[0] if skills else ""
                    else:
                        skills_path = skills
                    skills_dir = Path(install_path) / skills_path.strip("./")
                    skill_names = []
                    if skills_dir.exists():
                        for item in skills_dir.iterdir():
                            if item.is_dir() and (item / "SKILL.md").exists():
                                skill_names.append(item.name)
                    if skill_names:
                        components_to_show.append(("Skills", skill_names))

                hooks = plugin_json.get("hooks", {})
                if hooks:
                    if isinstance(hooks, dict):
                        hook_events = list(hooks.keys())
                        components_to_show.append(("Hooks", hook_events))
                    elif isinstance(hooks, list):
                        hook_names = [Path(hook).stem for hook in hooks]
                        components_to_show.append(("Hooks", hook_names))

                for component_type, component_names in components_to_show:
                    names_str = ", ".join(component_names[:5])
                    if len(component_names) > 5:
                        names_str += f" ... (+{len(component_names) - 5} more)"
                    plugin_node.add(f"[dim]{component_type}: {names_str}[/dim]")

            except (json.JSONDecodeError, OSError):
                pass

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
        "--installed",
        action="store_true",
        help="仅显示已安装的插件",
    )
    parser.add_argument(
        "--available",
        action="store_true",
        help="仅显示可用的插件（未安装）",
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

    project_dir = Path(args.project_dir).resolve()
    project_enabled = read_project_settings(project_dir)

    header = (
        "[bold blue]╔══════════════════════════════════════════╗[/bold blue]\n"
        "[bold blue]║     Claude Code Plugin Market Info       ║[/bold blue]\n"
        "[bold blue]╚══════════════════════════════════════════╝[/bold blue]"
    )
    console.print(header)
    console.print()

    marketplaces = get_marketplaces()
    plugins_data = get_plugins()

    installed = plugins_data.get("installed", [])
    installed_ids = {p.get("id", "") for p in installed}

    if args.enabled:
        display_enabled_plugins_details(plugins_data, project_enabled)
    elif args.installed:
        display_installed_plugins(plugins_data, project_enabled)
    elif args.available:
        available_plugins = {"available": [p for p in plugins_data.get("available", []) if p.get("pluginId") not in installed_ids]}
        display_available_plugins(available_plugins, installed_ids)
    else:
        display_marketplaces_summary(marketplaces, plugins_data)
        console.print()

        display_installed_plugins(plugins_data, project_enabled)

        available_not_installed = {
            "available": [p for p in plugins_data.get("available", []) if p.get("pluginId") not in installed_ids]
        }
        if available_not_installed["available"]:
            console.print("[bold blue]📋 Available Plugins[/bold blue]\n")
            display_available_plugins(available_not_installed, installed_ids)


if __name__ == "__main__":
    main()
