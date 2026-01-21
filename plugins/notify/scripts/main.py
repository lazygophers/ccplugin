from lib import logging
from lib.utils.env import set_app
from hooks import handle_hook
import click

# 注册应用名称
set_app("notify")

@click.command()
@click.option("--debug", "debug_mode", is_flag=True, help="启用 DEBUG 模式")
@click.option("--hooks", "hooks", is_flag=True, help="Hook 模式：从 stdin 读取 JSON")
def main(debug_mode: bool, hooks: bool) -> None:
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
	main()