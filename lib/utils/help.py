#!/usr/bin/env python3
"""Custom help formatter for argparse with rich output."""

import argparse
from typing import Optional

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class RichHelpFormatter(argparse.HelpFormatter):
    """A help formatter that uses rich for beautiful output."""

    def __init__(self, prog: str, **kwargs):
        super().__init__(prog, **kwargs)
        self._console = Console()

    def format_help(self) -> str:
        """Format the help message."""
        return super().format_help()


def print_help(
    parser: argparse.ArgumentParser,
    console: Optional[Console] = None,
) -> None:
    """Print a beautifully formatted help message.

    Args:
        parser: The argument parser
        console: Optional console instance
    """
    if console is None:
        console = Console()

    prog = parser.prog or "script"
    description = parser.description or ""

    console.print(Panel.fit(
        f"[bold cyan]{prog}[/bold cyan]\n"
        f"[dim]{description}[/dim]" if description else f"[bold cyan]{prog}[/bold cyan]",
        border_style="blue",
        box=box.DOUBLE,
    ))
    console.print()

    usage = parser.format_usage().strip()
    if usage:
        usage_text = Text()
        usage_text.append("用法: ", style="bold yellow")
        usage_text.append(usage.replace("usage: ", "").strip(), style="white")
        console.print(usage_text)
        console.print()

    positionals = []
    optionals = []

    for action in parser._actions:
        if action.dest == "help":
            continue
        if not action.option_strings:
            if action.dest != "help":
                positionals.append(action)
        else:
            optionals.append(action)

    if optionals:
        console.print("[bold]选项:[/bold]")
        table = Table(show_header=False, box=box.ROUNDED, padding=(0, 2))
        table.add_column("Option", style="cyan", no_wrap=True, width=20)
        table.add_column("Description", style="white")

        for action in optionals:
            opts = ", ".join(action.option_strings)
            if action.metavar:
                opts += f" [yellow]{action.metavar}[/yellow]"
            elif action.nargs not in (None, 0):
                opts += f" [yellow]{action.dest.upper()}[/yellow]"
            help_text = action.help or ""
            table.add_row(opts, help_text)

        console.print(table)
        console.print()

    if positionals:
        console.print("[bold]位置参数:[/bold]")
        table = Table(show_header=False, box=box.ROUNDED, padding=(0, 2))
        table.add_column("Argument", style="cyan", no_wrap=True, width=20)
        table.add_column("Description", style="white")

        for action in positionals:
            name = action.metavar or action.dest
            help_text = action.help or ""
            table.add_row(name, help_text)

        console.print(table)
        console.print()

    console.print("[dim]使用 --help 查看此帮助信息[/dim]")
