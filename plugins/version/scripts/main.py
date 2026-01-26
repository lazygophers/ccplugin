from lib import logging
import click
from functools import wraps
from . import hooks, version

def with_debug(func):
	"""装饰器：为所有命令添加 --debug 参数支持"""
	@wraps(func)
	@click.option("--debug", "debug_mode", is_flag=True, help="启用 DEBUG 模式")
	def wrapper(debug_mode: bool, *args, **kwargs):
		if debug_mode:
			logging.enable_debug()
		return func(*args, **kwargs)
	return wrapper

@click.group()
@click.pass_context
def main(ctx) -> None:
	"""
	Version management plugin.
	"""
	pass

@click.group()
@with_debug
def info() -> None:
	"""Show version information"""
	click.echo(f"Version: {version.get_version()}")

@main.command()
@with_debug
def hooks_cmd() -> None:
	"""Hook 模式：从 stdin 读取 JSON"""
	hooks.handle_hook()


if __name__ == "__main__":
	main()