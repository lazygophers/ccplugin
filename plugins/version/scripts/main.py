#!/usr/bin/env python3
"""
Version management plugin for Claude Code.

Supports debug logging mode and hook integration.
"""

import typer
from lib.logging import enable_debug
from hooks import handle_hook
from lib.utils.env import set_app

# 注册应用名称
set_app("version")


def main(
    debug_mode: bool = typer.Option(False, "--debug", help="启用 DEBUG 模式"),
    hooks: bool = typer.Option(False, "--hooks", help="Hook 模式：从 stdin 读取 JSON"),
) -> None:
    """
    Version management plugin.

    Args:
        debug_mode: 是否启用 DEBUG 模式
        hooks: 是否启用 Hook 模式
    """
    if debug_mode:
        enable_debug()

    if hooks:
        handle_hook()


if __name__ == "__main__":
    typer.run(main)