import sys
from pathlib import Path

# 设置 sys.path 以找到 lib 模块
script_dir = Path(__file__).resolve().parent
current = script_dir

# 向上搜索 lib 目录（最多 10 层）
for _ in range(10):
	if (current / "lib").exists():
		sys.path.insert(0, str(current))
		break
	current = current.parent

from lib import logging
from lib.utils.env import set_app
from hooks import handle_hook
import typer

# 注册应用名称
set_app("notify")

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
		logging.enable_debug()

	if hooks:
		handle_hook()


if __name__ == "__main__":
	typer.run(main)