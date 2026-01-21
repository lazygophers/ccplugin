#!/usr/bin/env python3
"""
Version management plugin for Claude Code.

Supports debug logging mode and hook integration.
"""

import typer
import sys
from pathlib import Path

# Find project root and ccplugin package
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent.parent

# Add ccplugin/ccplugin to sys.path to make lib available
ccplugin_path = project_root / "ccplugin" / "ccplugin"
if ccplugin_path.exists():
	sys.path.insert(0, str(ccplugin_path))
else:
	# Fallback: search upward for lib directory
	current = script_dir
	for _ in range(5):
		if (current / "ccplugin" / "ccplugin" / "lib").exists():
			sys.path.insert(0, str(current / "ccplugin" / "ccplugin"))
			break
		current = current.parent

from lib.logging import enable_debug, set_app
from hooks import handle_hook


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