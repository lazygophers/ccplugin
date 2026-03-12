#!/usr/bin/env python3
"""
Update enabled plugins using Claude's official plugin update command.

This script:
1. Gets enabled plugins via 'claude plugin list --json'
2. Updates marketplaces via 'claude plugin marketplace update' command
3. Uses 'claude plugin update' command to update all enabled plugins
4. Verifies all plugins are at latest versions after update
"""

import argparse
import json
import os
import random
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
)
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from lib.utils.env import get_project_dir
from lib.utils.constants import (
    LOADING_MESSAGES,
    MESSAGE_CHANGE_PROBABILITY,
    PROGRESS_THRESHOLD,
    MIN_ADVANCE,
    MAX_ADVANCE,
)

# Concurrency settings
MAX_MARKET_WORKERS = 3  # Maximum concurrent marketplace updates
MAX_PLUGIN_WORKERS = 5  # Maximum concurrent plugin updates
MAX_UV_WORKERS = 4  # Maximum concurrent uv sync operations


class NullConsole:
    """A console that doesn't output anything."""

    def __getattr__(self, name: str) -> Any:
        """Return a no-op function for any attribute access."""
        return lambda *args, **kwargs: None


console = Console()


def set_quiet_mode(quiet: bool) -> None:
    """Set quiet mode on or off."""
    global console
    if quiet:
        console = NullConsole()
    else:
        console = Console()


def create_progress_bar(console: Console, quiet: bool, total: int) -> Progress:
    """Create standardized progress bar.

    Args:
            console: Console instance
            quiet: Whether to disable progress display
            total: Total number of items

    Returns:
            Configured Progress instance
    """
    return Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40, complete_style="green", finished_style="bold green"),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
        disable=quiet,
    )


def run_claude_command_with_progress(
    args: list[str],
    description: str = "正在执行命令",
) -> dict[str, Any] | list[Any] | None:
    """Run a claude CLI command with animated progress bar.

    Args:
            args: Command arguments
            description: Initial description for progress bar

    Returns:
            Parsed JSON data or None if command fails
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = f.name

    result_container = {"done": False, "data": None}

    def run_command():
        try:
            proc = subprocess.run(
                ["claude"] + args,
                stdout=open(temp_path, "w"),
                stderr=subprocess.PIPE,
                text=True,
                cwd=get_project_dir(),
            )
            if proc.returncode == 0:
                with open(temp_path, "r", encoding="utf-8") as f:
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
            if random.random() < MESSAGE_CHANGE_PROBABILITY:
                message_idx = (message_idx + 1) % len(LOADING_MESSAGES)
                progress.update(task, description=LOADING_MESSAGES[message_idx])

            current = progress.tasks[0].completed
            if current < PROGRESS_THRESHOLD:
                advance = random.uniform(MIN_ADVANCE, MAX_ADVANCE)
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


class UpdateStats:
    """Statistics for the update process."""

    def __init__(self) -> None:
        self.updated_count = 0
        self.skipped_count = 0
        self.error_count = 0
        self.market_updated = 0
        self.market_failed = 0
        self.uv_sync_count = 0
        self.uv_sync_failed = 0
        self.messages: list[tuple[str, str]] = []
        self.version_mismatches: list[tuple[str, str, str]] = []
        self.version_changes: list[tuple[str, str, str]] = []
        self.market_changes: list[tuple[str, str, str]] = []

    def add_message(self, status: str, message: str) -> None:
        """Add a message to the log."""
        self.messages.append((status, message))

    def add_mismatch(self, plugin_id: str, expected: str, actual: str) -> None:
        """Add a version mismatch."""
        self.version_mismatches.append((plugin_id, expected, actual))

    def add_version_change(
        self, plugin_id: str, old_version: str, new_version: str
    ) -> None:
        """Add a version change record."""
        self.version_changes.append((plugin_id, old_version, new_version))

    def add_market_change(
        self, market_name: str, old_state: str, new_state: str
    ) -> None:
        """Add a market change record."""
        self.market_changes.append((market_name, old_state, new_state))

    def print_summary(self) -> None:
        """Print a summary table of the update process."""
        console.print(Rule(title="[bold blue]Update Summary[/bold blue]", style="blue"))

        summary_table = Table(
            show_header=False,
            box=box.ROUNDED,
            padding=(0, 2),
        )
        summary_table.add_column("Category", style="bold")
        summary_table.add_column("Status", justify="right")

        summary_table.add_row(
            "📦 Marketplaces Updated",
            f"[green]{self.market_updated}[/green]",
        )
        if self.market_failed > 0:
            summary_table.add_row(
                "❌ Marketplaces Failed",
                f"[red]{self.market_failed}[/red]",
            )
        summary_table.add_row(
            "✅ Plugins Updated",
            f"[green]{self.updated_count}[/green]",
        )
        summary_table.add_row(
            "⏭️  Plugins Skipped",
            f"[yellow]{self.skipped_count}[/yellow]",
        )
        if self.error_count > 0:
            summary_table.add_row(
                "❌ Errors",
                f"[red bold]{self.error_count}[/red bold]",
            )
        if self.uv_sync_count > 0:
            summary_table.add_row(
                "🔄 UV Sync Completed",
                f"[green]{self.uv_sync_count}[/green]",
            )
        if self.uv_sync_failed > 0:
            summary_table.add_row(
                "❌ UV Sync Failed",
                f"[red]{self.uv_sync_failed}[/red]",
            )
        if self.version_mismatches:
            summary_table.add_row(
                "⚠️  Version Mismatches",
                f"[yellow bold]{len(self.version_mismatches)}[/yellow bold]",
            )

        console.print(summary_table)

        if self.version_mismatches:
            console.print()
            console.print(
                Rule(
                    title="[bold yellow]Version Mismatches[/bold yellow]",
                    style="yellow",
                )
            )
            mismatch_table = Table(
                show_header=True,
                header_style="bold yellow",
                box=box.ROUNDED,
            )
            mismatch_table.add_column("Plugin", style="cyan")
            mismatch_table.add_column("Expected", style="green")
            mismatch_table.add_column("Actual", style="red")
            for plugin_id, expected, actual in self.version_mismatches:
                mismatch_table.add_row(plugin_id, expected, actual)
            console.print(mismatch_table)

        if self.market_changes:
            console.print()
            console.print(
                Rule(title="[bold cyan]Market Changes[/bold cyan]", style="cyan")
            )
            market_table = Table(
                show_header=True,
                header_style="bold cyan",
                box=box.ROUNDED,
            )
            market_table.add_column("Market", style="cyan")
            market_table.add_column("Old State", style="yellow")
            market_table.add_column("New State", style="green")
            for market_name, old_state, new_state in self.market_changes:
                market_table.add_row(market_name, old_state, new_state)
            console.print(market_table)

        if self.version_changes:
            console.print()
            console.print(
                Rule(title="[bold green]Version Changes[/bold green]", style="green")
            )
            version_table = Table(
                show_header=True,
                header_style="bold green",
                box=box.ROUNDED,
            )
            version_table.add_column("Plugin", style="cyan")
            version_table.add_column("Old Version", style="yellow")
            version_table.add_column("New Version", style="green")
            for plugin_id, old_version, new_version in self.version_changes:
                version_table.add_row(plugin_id, old_version, new_version)
            console.print(version_table)

        if self.messages:
            console.print()
            console.print(Rule(title="[bold]Details[/bold]", style="dim"))
            for status, msg in self.messages:
                if status == "error":
                    console.print(f"  [red]✗[/red] {msg}")
                elif status == "warning":
                    console.print(f"  [yellow]⚠[/yellow] {msg}")
                elif status == "success":
                    console.print(f"  [green]✓[/green] {msg}")
                elif status == "info":
                    console.print(f"  [dim]ℹ[/dim] {msg}")


def get_plugins_list(enabled_only: bool = True) -> list[dict[str, Any]]:
    """Get plugins from 'claude plugin list --json'.

    Args:
            enabled_only: If True, only return enabled plugins. If False, return all plugins.

    Returns:
            List of plugin info dicts
    """
    description = (
        "🔍 正在获取已启用插件..." if enabled_only else "🔍 正在获取所有插件..."
    )
    data = run_claude_command_with_progress(
        ["plugin", "list", "--json"], description=description
    )

    if not isinstance(data, list):
        return []

    plugins = []
    current_dir = os.getcwd()
    user_plugins: dict[str, dict[str, Any]] = {}

    for plugin in data:
        if enabled_only and not plugin.get("enabled"):
            continue

        scope = plugin.get("scope", "")
        project_path = plugin.get("projectPath", "")
        plugin_id = plugin.get("id", "")

        if scope == "user" and plugin_id:
            user_plugins[plugin_id] = plugin
        elif scope == "project" and project_path:
            if os.path.normpath(project_path) == os.path.normpath(current_dir):
                plugins.append(plugin)

    plugins.extend(user_plugins.values())
    return plugins


def get_latest_versions_from_marketplace() -> dict[str, str]:
    """Get latest available versions for all plugins from marketplace.

    Returns:
            Dict mapping plugin_id to latest version string
    """
    data = run_claude_command_with_progress(
        ["plugin", "list", "--json", "--all"], description="🌐 正在获取最新版本信息..."
    )

    if not isinstance(data, list):
        return {}

    latest_versions: dict[str, str] = {}
    for plugin in data:
        plugin_id = plugin.get("id", "")
        version = plugin.get("version", "")
        if plugin_id and version:
            if plugin_id not in latest_versions:
                latest_versions[plugin_id] = version

    return latest_versions


def cleanup_old_plugin_versions(
    all_plugins: list[dict[str, Any]],
    dry_run: bool = False,
) -> int:
    """清理旧版本的插件安装记录.

    Args:
            all_plugins: 更新后的所有插件列表
            dry_run: 如果为 True，仅显示将要执行的操作

    Returns:
            清理的旧版本数量
    """
    from pathlib import Path

    installed_json = Path.home() / ".claude" / "plugins" / "installed_plugins.json"

    if not installed_json.exists():
        return 0

    try:
        with open(installed_json, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return 0

    plugins_data = data.get("plugins", {})
    if not plugins_data:
        return 0

    total_cleaned = 0

    # 遍历所有插件，找出需要清理的旧版本
    for plugin in all_plugins:
        plugin_id = plugin.get("id", "")
        if not plugin_id:
            continue

        installations = plugins_data.get(plugin_id, [])
        if not installations:
            continue

        # 找出每个 plugin_id 对应的最新版本
        version_to_install = plugin.get("version", "")
        if not version_to_install:
            continue

        # 找出需要删除的旧版本记录
        to_remove = []
        to_keep = []

        for install in installations:
            version = install.get("version", "")
            if version != version_to_install:
                to_remove.append(install)
            else:
                to_keep.append(install)

        if not to_remove:
            continue

        if dry_run:
            console.print(
                f"[dim][DRY RUN] Would clean up {len(to_remove)} old version(s) of {plugin_id}[/dim]"
            )
            total_cleaned += len(to_remove)
            continue

        # 更新安装记录
        plugins_data[plugin_id] = to_keep
        total_cleaned += len(to_remove)

    if total_cleaned > 0 and not dry_run:
        # 写回文件
        with open(installed_json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    return total_cleaned


def run_claude_plugin_command(
    command: str,
    plugin_key: str,
    scope: str = "user",
    dry_run: bool = False,
    force: bool = False,
) -> tuple[bool, str]:
    """Run 'claude plugin' command for a specific plugin.

    Args:
            command: Command to run ('install' or 'enable')
            plugin_key: Plugin key in format 'plugin@market'
            scope: Plugin scope ('user' or 'project')
            dry_run: If True, show what would be done without making changes
            force: If True, add --force flag to the command

    Returns:
            Tuple of (success, output) where success is True if command succeeded
    """
    cmd = ["claude", "plugin", command, "--scope", scope, plugin_key]

    if dry_run:
        console.print(f"[dim][DRY RUN] Would run: {' '.join(cmd)}[/dim]")
        return True, ""

    result = subprocess.run(
        cmd,
        cwd=get_project_dir(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    return result.returncode == 0, result.stdout


def get_marketplace_list() -> list[dict[str, str]]:
    """Get list of installed marketplaces using 'claude plugin marketplace list --json'.

    Returns:
            List of marketplace info dicts with keys: name, source, url, installLocation
    """
    data = run_claude_command_with_progress(
        ["plugin", "marketplace", "list", "--json"],
        description="📦 正在获取市场列表...",
    )

    if isinstance(data, list):
        return data
    return []


def update_marketplace(market: str, stats: UpdateStats, dry_run: bool = False) -> bool:
    """Update marketplace using 'claude plugin marketplace update' command.

    Args:
            market: Marketplace name
            stats: Statistics object to track results
            dry_run: If True, show what would be done without making changes

    Returns:
            True if successful, False otherwise
    """
    if dry_run:
        console.print(
            f"[dim][DRY RUN] Would run: claude plugin marketplace update {market}[/dim]"
        )
        stats.market_updated += 1
        return True

    result = subprocess.run(
        ["claude", "plugin", "marketplace", "update", market],
        cwd=get_project_dir(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    if result.returncode != 0:
        stats.market_failed += 1
        return False

    stats.market_updated += 1
    return True


def update_marketplaces_concurrent(
    marketplaces: list[dict[str, str]], stats: UpdateStats, dry_run: bool = False, quiet: bool = False
) -> None:
    """Update marketplaces concurrently.

    Args:
            marketplaces: List of marketplace info dicts
            stats: Statistics object to track results
            dry_run: If True, show what would be done without making changes
            quiet: Whether to disable progress display
    """
    if not marketplaces:
        return

    with create_progress_bar(console, quiet, len(marketplaces)) as progress:
        task = progress.add_task(
            "[cyan]Updating markets...[/cyan]", total=len(marketplaces)
        )

        with ThreadPoolExecutor(max_workers=MAX_MARKET_WORKERS) as executor:
            futures = {
                executor.submit(
                    update_marketplace, m.get("name", "unknown"), stats, dry_run
                ): m
                for m in marketplaces
            }

            for future in as_completed(futures):
                market = futures[future]
                market_name = market.get("name", "unknown")
                progress.update(
                    task, description=f"[cyan]Updated {market_name}[/cyan]"
                )
                progress.advance(task)


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


def run_uv_sync(
    plugin_path: str, plugin_name: str, stats: UpdateStats, dry_run: bool = False
) -> bool:
    """Run 'uv sync' in plugin directory if pyproject.toml exists.

    Args:
            plugin_path: Path to plugin directory
            plugin_name: Name of the plugin for display
            stats: Statistics object to track results
            dry_run: If True, show what would be done without making changes

    Returns:
            True if uv sync was executed successfully or skipped, False on error
    """
    from pathlib import Path

    plugin_dir = Path(plugin_path)
    pyproject_path = plugin_dir / "pyproject.toml"

    if not pyproject_path.exists():
        return True

    if dry_run:
        return True

    result = subprocess.run(
        ["uv", "sync"],
        cwd=plugin_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    if result.returncode == 0:
        stats.uv_sync_count += 1
        stats.add_message(
            "success",
            f"uv sync completed for [cyan]{plugin_name}[/cyan] [dim]({plugin_dir.name})[/dim]",
        )
        return True
    else:
        stats.uv_sync_failed += 1
        stats.add_message(
            "error", f"uv sync failed for {plugin_name}: {result.stdout.strip()}"
        )
        return False


def run_uv_sync_concurrent(
    plugins_with_pyproject: list[tuple[str, str]], stats: UpdateStats, dry_run: bool = False, quiet: bool = False
) -> None:
    """Run uv sync concurrently for plugins with pyproject.toml.

    Args:
            plugins_with_pyproject: List of (plugin_id, install_path) tuples
            stats: Statistics object to track results
            dry_run: If True, show what would be done without making changes
            quiet: Whether to disable progress display
    """
    if not plugins_with_pyproject:
        return

    with create_progress_bar(console, quiet, len(plugins_with_pyproject)) as progress:
        task = progress.add_task(
            "[cyan]Running uv sync...[/cyan]", total=len(plugins_with_pyproject)
        )

        with ThreadPoolExecutor(max_workers=MAX_UV_WORKERS) as executor:
            futures = {
                executor.submit(
                    run_uv_sync, path, pid.split("@")[0] if pid else "unknown", stats, dry_run
                ): (pid, path)
                for pid, path in plugins_with_pyproject
            }

            for future in as_completed(futures):
                plugin_id, _ = futures[future]
                plugin_name = plugin_id.split("@")[0] if plugin_id else "unknown"
                progress.update(
                    task, description=f"[cyan]Synced {plugin_name}[/cyan]"
                )
                progress.advance(task)


def enable_plugin(plugin_id: str, dry_run: bool = False) -> bool:
    """Enable a plugin using 'claude plugin enable' command.

    Args:
            plugin_id: Plugin ID in format 'plugin@market'
            dry_run: If True, show what would be done without making changes

    Returns:
            True if successful, False otherwise
    """
    if dry_run:
        console.print(
            f"[dim][DRY RUN] Would run: claude plugin enable {plugin_id}[/dim]"
        )
        return True

    result = subprocess.run(
        ["claude", "plugin", "enable", plugin_id],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    return result.returncode == 0


def create_plugin_table(plugins: list[dict[str, Any]]) -> Table:
    """Create a rich table for displaying plugins."""
    table = Table(
        title="[bold]Enabled Plugins[/bold]",
        show_header=True,
        header_style="bold cyan",
        box=box.ROUNDED,
        pad_edge=False,
    )
    table.add_column("Plugin", style="green", no_wrap=True)
    table.add_column("Market", style="blue", no_wrap=True)
    table.add_column("Scope", style="cyan", justify="center")
    table.add_column("Version", style="yellow", justify="right")

    for plugin in plugins:
        plugin_id = plugin.get("id", "")
        parsed = parse_plugin_key(plugin_id)
        if parsed:
            plugin_name, market = parsed
            scope = plugin.get("scope", "unknown")
            version = plugin.get("version", "-")
            if scope == "user":
                scope_display = "[cyan]user[/cyan]"
            else:
                scope_display = "[magenta]project[/magenta]"
            table.add_row(plugin_name, market, scope_display, version)

    return table


def update_plugins_concurrent(
    enabled_plugins: list[dict[str, Any]], stats: UpdateStats, dry_run: bool = False, quiet: bool = False
) -> list[tuple[str, bool, str]]:
    """Update plugins concurrently.

    Args:
            enabled_plugins: List of enabled plugin info dicts
            stats: Statistics object to track results
            dry_run: If True, show what would be done without making changes
            quiet: Whether to disable progress display

    Returns:
            List of (plugin_name, success, output) tuples
    """
    update_outputs: list[tuple[str, bool, str]] = []

    with create_progress_bar(console, quiet, len(enabled_plugins)) as progress:
        task = progress.add_task(
            "[cyan]Updating plugins...[/cyan]", total=len(enabled_plugins)
        )

        with ThreadPoolExecutor(max_workers=MAX_PLUGIN_WORKERS) as executor:
            futures = {}
            for plugin in enabled_plugins:
                plugin_id = plugin.get("id", "")
                plugin_name = plugin_id.split("@")[0] if plugin_id else "unknown"
                future = executor.submit(
                    run_claude_plugin_command,
                    "install",
                    plugin_id,
                    plugin.get("scope", "user"),
                    dry_run,
                    True,
                )
                futures[future] = (plugin_name, plugin)

            for future in as_completed(futures):
                plugin_name, plugin = futures[future]
                progress.update(task, description=f"[cyan]Updating {plugin_name}...[/cyan]")

                try:
                    success, output = future.result()
                    update_outputs.append((plugin_name, success, output))

                    if success:
                        stats.updated_count += 1
                    else:
                        stats.error_count += 1
                except Exception as e:
                    stats.error_count += 1
                    stats.add_message("error", f"Failed to update {plugin_name}: {str(e)}")
                    update_outputs.append((plugin_name, False, str(e)))

                progress.advance(task)

    # 清理旧版本的插件
    if not dry_run and not quiet:
        # 重新获取更新后的插件列表，以获取最新版本号
        updated_plugins = get_plugins_list(enabled_only=True)

        if updated_plugins:
            with create_progress_bar(console, quiet, len(updated_plugins)) as progress:
                task = progress.add_task(
                    "[cyan]Cleaning up old versions...[/cyan]", total=len(updated_plugins)
                )

                cleaned_total = cleanup_old_plugin_versions(updated_plugins, dry_run)
                if cleaned_total > 0:
                    stats.add_message(
                        "info",
                        f"Cleaned up [cyan]{cleaned_total}[/cyan] old version(s) in total",
                    )
                    progress.update(task, completed=len(updated_plugins))
                else:
                    progress.update(task, completed=len(updated_plugins))

    return update_outputs


def verify_versions(
    enabled_plugins: list[dict[str, Any]],
    latest_versions: dict[str, str],
    stats: UpdateStats,
) -> bool:
    """Verify all enabled plugins are at latest versions.

    Args:
            enabled_plugins: List of enabled plugin info dicts
            latest_versions: Dict of plugin_id -> latest version
            stats: Statistics object to track mismatches

    Returns:
            True if all versions match, False otherwise
    """
    all_match = True

    for plugin in enabled_plugins:
        plugin_id = plugin.get("id", "")
        current_version = plugin.get("version", "")
        latest_version = latest_versions.get(plugin_id, "")

        if latest_version and current_version != latest_version:
            stats.add_mismatch(plugin_id, latest_version, current_version)
            all_match = False

    return all_match


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="update.py",
        description="🔌 CCPlugin 插件更新工具 - 使用 Claude 官方命令更新已启用的插件",
        add_help=False,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="模拟运行，仅显示将要执行的操作",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="静默模式，不输出任何信息",
    )
    parser.add_argument(
        "--no-market-update",
        action="store_true",
        help="跳过市场更新（更快，但可能使用过时数据）",
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="跳过更新后的版本验证",
    )
    parser.add_argument(
        "--auto-enable",
        action="store_true",
        help="自动启用被禁用的插件",
    )
    parser.add_argument(
        "--no-uv-sync",
        action="store_true",
        help="跳过插件目录的 uv sync 操作",
    )
    parser.add_argument(
        "-h",
        "--help",
        action="store_true",
        help="显示帮助信息",
    )

    args = parser.parse_args()

    if args.help:
        from lib.utils import print_help

        print_help(parser, console)
        return 0

    set_quiet_mode(args.quiet)

    console.print(
        Panel.fit(
            "[bold cyan]🔌 Plugin Update Tool[/bold cyan]\n"
            f"[dim]Project:[/dim] [white]{get_project_dir()}[/white]",
            border_style="blue",
            box=box.DOUBLE,
        )
    )
    console.print()

    stats = UpdateStats()

    if args.auto_enable:
        console.print(
            Rule(title="[bold cyan]Auto-Enabling Plugins[/bold cyan]", style="cyan")
        )
        all_plugins = get_plugins_list(enabled_only=False)
        disabled_plugins = [p for p in all_plugins if not p.get("enabled")]

        if disabled_plugins:
            console.print(
                f"[yellow]Found {len(disabled_plugins)} disabled plugin(s)[/yellow]"
            )
            with create_progress_bar(
                console, args.quiet, len(disabled_plugins)
            ) as progress:
                task = progress.add_task(
                    "[cyan]Enabling plugins...[/cyan]", total=len(disabled_plugins)
                )
                for plugin in disabled_plugins:
                    plugin_id = plugin.get("id", "")
                    plugin_name = plugin_id.split("@")[0] if plugin_id else "unknown"
                    progress.update(
                        task, description=f"[cyan]Enabling {plugin_name}...[/cyan]"
                    )
                    if enable_plugin(plugin_id, dry_run=args.dry_run):
                        stats.add_message("success", f"Enabled plugin: {plugin_name}")
                    else:
                        stats.add_message(
                            "error", f"Failed to enable plugin: {plugin_name}"
                        )
                    progress.advance(task)
            console.print()
        else:
            console.print("[green]All plugins are already enabled[/green]")
            console.print()

    enabled_plugins = get_plugins_list(enabled_only=True)

    plugin_count_text = Text()
    plugin_count_text.append("Found ")
    plugin_count_text.append(str(len(enabled_plugins)), style="bold green")
    plugin_count_text.append(" enabled plugin(s)")
    console.print(plugin_count_text)
    console.print()

    if not enabled_plugins:
        console.print(
            Panel(
                "[yellow]No enabled plugins found[/yellow]",
                border_style="yellow",
                box=box.ROUNDED,
            )
        )
        return 0

    console.print(create_plugin_table(enabled_plugins))
    console.print()

    marketplaces = get_marketplace_list()
    market_count_text = Text()
    market_count_text.append("Found ")
    market_count_text.append(str(len(marketplaces)), style="bold blue")
    market_count_text.append(" marketplace(s)")
    console.print(market_count_text)
    console.print()

    if marketplaces and not args.no_market_update:
        console.print(
            Rule(title="[bold cyan]Updating Marketplaces[/bold cyan]", style="cyan")
        )
        update_marketplaces_concurrent(marketplaces, stats, dry_run=args.dry_run, quiet=args.quiet)
        console.print()

    console.print(Rule(title="[bold cyan]Updating Plugins[/bold cyan]", style="cyan"))
    console.print("[dim]Using 'claude plugin install --force' command[/dim]")
    console.print()

    update_outputs = update_plugins_concurrent(enabled_plugins, stats, dry_run=args.dry_run, quiet=args.quiet)

    console.print()

    if update_outputs:
        console.print(Rule(title="[bold]Update Details[/bold]", style="dim"))
        for plugin_name, success, output in update_outputs:
            if output.strip():
                for line in output.strip().split("\n"):
                    if line.strip():
                        if success:
                            console.print(f"  [dim]{line}[/dim]")
                        else:
                            console.print(f"  [red]{line}[/red]")
        console.print()

    if not args.no_uv_sync and not args.dry_run:
        console.print(
            Rule(title="[bold cyan]Running UV Sync[/bold cyan]", style="cyan")
        )
        console.print("[dim]Checking for pyproject.toml in plugin directories...[/dim]")
        console.print()

        plugins_with_pyproject = []
        for plugin in enabled_plugins:
            install_path = plugin.get("installPath", "")
            plugin_id = plugin.get("id", "")
            if install_path:
                from pathlib import Path

                plugin_dir = Path(install_path)
                pyproject_path = plugin_dir / "pyproject.toml"
                if pyproject_path.exists():
                    plugins_with_pyproject.append((plugin_id, install_path))

        if plugins_with_pyproject:
            console.print(
                f"[cyan]Found {len(plugins_with_pyproject)} plugin(s) with pyproject.toml[/cyan]"
            )
            console.print()

            run_uv_sync_concurrent(plugins_with_pyproject, stats, dry_run=args.dry_run, quiet=args.quiet)
            console.print()
        else:
            console.print("[dim]No plugins with pyproject.toml found[/dim]")
            console.print()

    if not args.no_verify:
        console.print(
            Rule(title="[bold cyan]Verifying Versions[/bold cyan]", style="cyan")
        )

        latest_versions = get_latest_versions_from_marketplace()
        enabled_plugins = get_plugins_list(enabled_only=True)

        market_check_passed = verify_versions(enabled_plugins, latest_versions, stats)

        plugin_versions: dict[str, list[tuple[str, str]]] = {}
        for plugin in enabled_plugins:
            plugin_id = plugin.get("id", "")
            scope = plugin.get("scope", "")
            version = plugin.get("version", "")
            if plugin_id:
                if plugin_id not in plugin_versions:
                    plugin_versions[plugin_id] = []
                plugin_versions[plugin_id].append((scope, version))

        scope_version_mismatches = []
        for plugin_id, versions in plugin_versions.items():
            if len(versions) > 1:
                unique_versions = set(v for _, v in versions)
                if len(unique_versions) > 1:
                    scope_version_mismatches.append((plugin_id, versions))

        if market_check_passed and not scope_version_mismatches:
            console.print("[green]✓ All plugins are at latest versions[/green]")
        else:
            if not market_check_passed:
                console.print(
                    f"[yellow]⚠ Found {len(stats.version_mismatches)} plugin(s) with version mismatches from marketplace[/yellow]"
                )
            if scope_version_mismatches:
                console.print(
                    f"[yellow]⚠ Found {len(scope_version_mismatches)} plugin(s) with different versions across scopes[/yellow]"
                )
                for plugin_id, versions in scope_version_mismatches:
                    version_str = ", ".join(
                        [f"{scope}: {version}" for scope, version in versions]
                    )
                    console.print(f"  [yellow]•[/yellow] {plugin_id}: {version_str}")

        console.print()

    stats.print_summary()

    if stats.version_mismatches:
        console.print()
        console.print(
            Panel(
                "[yellow]Some plugins may need manual update. Try running 'update' again or check the marketplace.[/yellow]",
                border_style="yellow",
                box=box.ROUNDED,
            )
        )
        return 1

    return 0 if stats.error_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
