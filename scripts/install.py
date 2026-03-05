#!/usr/bin/env python3
"""
Install or update a plugin from a specified marketplace.

This script:
1. Normalizes marketplace name (supports URL, short form, etc.)
2. Checks if marketplace exists, adds if not, updates if exists
3. Checks if plugin is installed, installs if not, updates if installed

Usage:
  uv run install.py <marketplace> <plugin>
  uv run install.py lazygophers/ccplugin gin
  uv run install.py https://github.com/lazygophers/ccplugin.git gin
  uv run install.py https://github.com/lazygophers/ccplugin gin
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

from lib.utils.env import get_project_dir
from lib.utils import print_help

LOADING_MESSAGES = [
	"🔍 正在搜索插件市场...",
	"📦 正在加载插件列表...",
	"🚀 正在获取最新数据...",
	"✨ 正在整理插件信息...",
	"🎯 正在匹配插件...",
	"🌐 正在连接市场源...",
	"⚡ 正在加速数据传输...",
	"🔮 正在准备安装...",
	"🦄 正在召唤插件精灵...",
	"🌟 正在收集星光数据...",
]

console = Console()


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


def normalize_marketplace_name(market_input: str) -> tuple[str, str]:
	"""Normalize marketplace name to standard format.

	Handles three equivalent formats:
	- https://github.com/lazygophers/ccplugin.git
	- https://github.com/lazygophers/ccplugin
	- lazygophers/ccplugin

	Args:
		market_input: Raw marketplace input string

	Returns:
		Tuple of (normalized_name, full_url) where:
		- normalized_name: Short name like 'lazygophers/ccplugin'
		- full_url: Full URL like 'https://github.com/lazygophers/ccplugin.git'
	"""
	market_input = market_input.strip()

	if market_input.startswith("https://github.com/"):
		url = market_input
		if not url.endswith(".git"):
			url = url + ".git"
		short_name = market_input.replace("https://github.com/", "").replace(".git", "")
		return short_name, url
	elif "/" in market_input and not market_input.startswith("http"):
		short_name = market_input
		url = f"https://github.com/{short_name}.git"
		return short_name, url
	else:
		return market_input, market_input


def get_marketplace_list() -> list[dict[str, str]]:
	"""Get list of installed marketplaces.

	Returns:
		List of marketplace info dicts with keys: name, source, url, installLocation
	"""
	data = run_claude_command_with_progress(
		["plugin", "marketplace", "list", "--json"],
		description="📦 正在获取市场列表..."
	)

	if isinstance(data, list):
		return data
	return []


def find_marketplace(
	marketplaces: list[dict[str, str]],
	normalized_name: str,
) -> dict[str, str] | None:
	"""Find a marketplace by normalized name.

	Args:
		marketplaces: List of marketplace info dicts
		normalized_name: Normalized marketplace name

	Returns:
		Marketplace info dict or None if not found
	"""
	for market in marketplaces:
		name = market.get("name", "")
		url = market.get("url", "")
		source = market.get("source", "")

		if name == normalized_name:
			return market

		if url:
			url_normalized = url.replace("https://github.com/", "").replace(".git", "")
			if url_normalized == normalized_name:
				return market

		if source:
			source_normalized = source.replace("https://github.com/", "").replace(".git", "")
			if source_normalized == normalized_name:
				return market

	return None


def add_marketplace(url: str, dry_run: bool = False) -> bool:
	"""Add a marketplace using 'claude plugin marketplace add' command.

	Args:
		url: Marketplace URL
		dry_run: If True, show what would be done without making changes

	Returns:
		True if successful, False otherwise
	"""
	if dry_run:
		console.print(f"[dim][DRY RUN] Would run: claude plugin marketplace add {url}[/dim]")
		return True

	result = subprocess.run(
		["claude", "plugin", "marketplace", "add", url],
		cwd=get_project_dir(),
		stdout=subprocess.PIPE,
		stderr=subprocess.STDOUT,
		text=True,
	)

	if result.returncode != 0:
		console.print(f"[red]添加市场失败: {result.stdout}[/red]")
		return False

	return True


def update_marketplace(market_name: str, dry_run: bool = False) -> bool:
	"""Update a marketplace using 'claude plugin marketplace update' command.

	Args:
		market_name: Marketplace name
		dry_run: If True, show what would be done without making changes

	Returns:
		True if successful, False otherwise
	"""
	if dry_run:
		console.print(f"[dim][DRY RUN] Would run: claude plugin marketplace update {market_name}[/dim]")
		return True

	result = subprocess.run(
		["claude", "plugin", "marketplace", "update", market_name],
		cwd=get_project_dir(),
		stdout=subprocess.PIPE,
		stderr=subprocess.STDOUT,
		text=True,
	)

	if result.returncode != 0:
		console.print(f"[red]更新市场失败: {result.stdout}[/red]")
		return False

	return True


def get_plugin_list() -> list[dict[str, Any]]:
	"""Get list of installed plugins.

	Returns:
		List of plugin info dicts
	"""
	data = run_claude_command_with_progress(
		["plugin", "list", "--json"],
		description="📦 正在获取插件列表..."
	)

	if isinstance(data, list):
		return data
	return []


def find_plugin(
	plugins: list[dict[str, Any]],
	plugin_name: str,
	market_name: str,
) -> dict[str, Any] | None:
	"""Find a plugin by name and marketplace.

	Args:
		plugins: List of plugin info dicts
		plugin_name: Plugin name
		market_name: Marketplace name

	Returns:
		Plugin info dict or None if not found
	"""
	plugin_id = f"{plugin_name}@{market_name}"

	for plugin in plugins:
		pid = plugin.get("id", "")
		if pid == plugin_id:
			return plugin

	return None


def install_plugin(plugin_key: str, dry_run: bool = False) -> bool:
	"""Install a plugin using 'claude plugin install' command.

	Args:
		plugin_key: Plugin key in format 'plugin@market' or just 'plugin'
		dry_run: If True, show what would be done without making changes

	Returns:
		True if successful, False otherwise
	"""
	if dry_run:
		console.print(f"[dim][DRY RUN] Would run: claude plugin install {plugin_key}[/dim]")
		return True

	with Progress(
		SpinnerColumn(spinner_name="dots"),
		TextColumn("[progress.description]{task.description}"),
		BarColumn(bar_width=40, complete_style="green", finished_style="bold green"),
		TaskProgressColumn(),
		TimeElapsedColumn(),
		console=console,
	) as progress:
		task = progress.add_task(f"[cyan]正在安装 {plugin_key}...[/cyan]", total=100)

		result = subprocess.run(
			["claude", "plugin", "install", plugin_key],
			cwd=get_project_dir(),
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT,
			text=True,
		)

		progress.update(task, completed=100)

	if result.returncode != 0:
		console.print(f"[red]安装插件失败: {result.stdout}[/red]")
		return False

	if result.stdout.strip():
		console.print(f"[dim]{result.stdout.strip()}[/dim]")

	return True


def update_plugin(plugin_key: str, dry_run: bool = False) -> bool:
	"""Update a plugin using 'claude plugin update' command.

	Args:
		plugin_key: Plugin key in format 'plugin@market'
		dry_run: If True, show what would be done without making changes

	Returns:
		True if successful, False otherwise
	"""
	if dry_run:
		console.print(f"[dim][DRY RUN] Would run: claude plugin update {plugin_key}[/dim]")
		return True

	with Progress(
		SpinnerColumn(spinner_name="dots"),
		TextColumn("[progress.description]{task.description}"),
		BarColumn(bar_width=40, complete_style="green", finished_style="bold green"),
		TaskProgressColumn(),
		TimeElapsedColumn(),
		console=console,
	) as progress:
		task = progress.add_task(f"[cyan]正在更新 {plugin_key}...[/cyan]", total=100)

		result = subprocess.run(
			["claude", "plugin", "update", plugin_key],
			cwd=get_project_dir(),
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT,
			text=True,
		)

		progress.update(task, completed=100)

	if result.returncode != 0:
		console.print(f"[red]更新插件失败: {result.stdout}[/red]")
		return False

	if result.stdout.strip():
		console.print(f"[dim]{result.stdout.strip()}[/dim]")

	return True


def main() -> int:
	parser = argparse.ArgumentParser(
		prog="install.py",
		description="🔌 CCPlugin 插件安装工具 - 从指定市场安装或更新插件",
		add_help=False,
	)
	parser.add_argument(
		"marketplace",
		type=str,
		nargs="?",
		help="市场名称或 URL (如: lazygophers/ccplugin 或 https://github.com/lazygophers/ccplugin.git)",
	)
	parser.add_argument(
		"plugin",
		type=str,
		nargs="?",
		help="插件名称 (如: gin, python, typescript)",
	)
	parser.add_argument(
		"--dry-run",
		action="store_true",
		help="模拟运行，仅显示将要执行的操作",
	)
	parser.add_argument(
		"-h", "--help",
		action="store_true",
		help="显示帮助信息",
	)

	args = parser.parse_args()

	if args.help:
		print_help(parser, console)
		return 0

	if not args.marketplace or not args.plugin:
		console.print(Panel.fit(
			"[bold red]错误: 缺少必需参数[/bold red]\n\n"
			"[dim]用法: install.py <marketplace> <plugin>[/dim]\n\n"
			"[dim]示例:[/dim]\n"
			"  [cyan]install.py lazygophers/ccplugin gin[/cyan]\n"
			"  [cyan]install.py https://github.com/lazygophers/ccplugin.git python[/cyan]\n"
			"  [cyan]install.py https://github.com/lazygophers/ccplugin typescript[/cyan]",
			border_style="red",
			box=box.DOUBLE
		))
		return 1

	market_input = args.marketplace
	plugin_name = args.plugin

	normalized_name, full_url = normalize_marketplace_name(market_input)

	console.print(Panel.fit(
		f"[bold cyan]🔌 Plugin Install Tool[/bold cyan]\n"
		f"[dim]市场:[/dim] [white]{normalized_name}[/white]\n"
		f"[dim]插件:[/dim] [white]{plugin_name}[/white]\n"
		f"[dim]项目:[/dim] [white]{get_project_dir()}[/white]",
		border_style="blue",
		box=box.DOUBLE,
	))
	console.print()

	console.print(Rule(title="[bold cyan]Step 1: 检查市场[/bold cyan]", style="cyan"))
	console.print()

	marketplaces = get_marketplace_list()
	existing_market = find_marketplace(marketplaces, normalized_name)

	if existing_market:
		market_display_name = existing_market.get("name", normalized_name)
		console.print(f"[green]✓ 市场已存在: [cyan]{market_display_name}[/cyan][/green]")
		console.print()

		console.print(Rule(title="[bold cyan]Step 2: 更新市场[/bold cyan]", style="cyan"))
		console.print()

		if not update_marketplace(market_display_name, dry_run=args.dry_run):
			console.print("[yellow]⚠ 市场更新失败，继续尝试安装插件...[/yellow]")
		else:
			console.print(f"[green]✓ 市场已更新: [cyan]{market_display_name}[/cyan][/green]")
		console.print()
	else:
		console.print(f"[yellow]○ 市场不存在: [cyan]{normalized_name}[/cyan][/yellow]")
		console.print()

		console.print(Rule(title="[bold cyan]Step 2: 添加市场[/bold cyan]", style="cyan"))
		console.print()

		if not add_marketplace(full_url, dry_run=args.dry_run):
			console.print("[red]✗ 添加市场失败[/red]")
			return 1

		console.print(f"[green]✓ 市场已添加: [cyan]{normalized_name}[/cyan][/green]")
		console.print()

	marketplaces = get_marketplace_list()
	existing_market = find_marketplace(marketplaces, normalized_name)

	if not existing_market:
		console.print(f"[red]✗ 无法找到市场: {normalized_name}[/red]")
		return 1

	market_name = existing_market.get("name", normalized_name)

	console.print(Rule(title="[bold cyan]Step 3: 检查插件[/bold cyan]", style="cyan"))
	console.print()

	plugins = get_plugin_list()

	if "@" in plugin_name:
		plugin_key = plugin_name
		parts = plugin_name.split("@")
		plugin_name_only = parts[0]
		plugin_market = parts[1] if len(parts) > 1 else market_name
	else:
		plugin_key = f"{plugin_name}@{market_name}"
		plugin_name_only = plugin_name
		plugin_market = market_name

	existing_plugin = find_plugin(plugins, plugin_name_only, plugin_market)

	if existing_plugin:
		version = existing_plugin.get("version", "unknown")
		enabled = existing_plugin.get("enabled", False)
		status = "[green]✓ 已启用[/green]" if enabled else "[yellow]○ 已禁用[/yellow]"

		console.print(f"[green]✓ 插件已安装: [cyan]{plugin_name_only}[/cyan] [dim]v{version}[/dim] {status}[/green]")
		console.print()

		console.print(Rule(title="[bold cyan]Step 4: 更新插件[/bold cyan]", style="cyan"))
		console.print()

		if not update_plugin(plugin_key, dry_run=args.dry_run):
			console.print("[red]✗ 更新插件失败[/red]")
			return 1

		console.print(f"[green]✓ 插件已更新: [cyan]{plugin_key}[/cyan][/green]")
	else:
		console.print(f"[yellow]○ 插件未安装: [cyan]{plugin_name_only}[/cyan][/yellow]")
		console.print()

		console.print(Rule(title="[bold cyan]Step 4: 安装插件[/bold cyan]", style="cyan"))
		console.print()

		if not install_plugin(plugin_key, dry_run=args.dry_run):
			console.print("[red]✗ 安装插件失败[/red]")
			return 1

		console.print(f"[green]✓ 插件已安装: [cyan]{plugin_key}[/cyan][/green]")

	console.print()

	summary_table = Table(show_header=False, box=box.ROUNDED, padding=(0, 2))
	summary_table.add_column("Category", style="bold")
	summary_table.add_column("Status", justify="right")

	summary_table.add_row("📦 市场", f"[green]{market_name}[/green]")
	summary_table.add_row("🔌 插件", f"[green]{plugin_key}[/green]")

	console.print(Panel.fit(
		summary_table,
		title="[bold green]✓ 安装完成[/bold green]",
		border_style="green",
		box=box.DOUBLE,
	))

	return 0


if __name__ == "__main__":
	sys.exit(main())
