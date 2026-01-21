#!/usr/bin/env python3
"""
Version management plugin for Claude Code.

Supports debug logging mode.
"""

import sys
from pathlib import Path
import typer

# 设置 sys.path 以导入 lib 模块
# 脚本路径: plugins/version/scripts/version.py
# 项目根: plugins/version/../../
script_dir = Path(__file__).resolve().parent  # scripts 目录
plugin_dir = script_dir.parent  # plugins/version 目录
project_root = plugin_dir.parent.parent  # 项目根

# 确保 lib 目录存在
lib_path = project_root / "lib"
if not lib_path.exists():
    # 向上搜索以防出现特殊情况
    current = script_dir
    for _ in range(5):
        if (current / "lib").exists():
            project_root = current
            break
        current = current.parent

sys.path.insert(0, str(project_root))

# 导入日志模块
from lib.logging import enable_debug


def main(debug_mode: bool = typer.Option(False, "--debug", help="启用 DEBUG 模式")) -> None:
    """
    Version management plugin.

    Args:
        debug_mode: 是否启用 DEBUG 模式
    """
    if debug_mode:
        enable_debug()


if __name__ == "__main__":
    typer.run(main)
