from lib import logging
import click
from functools import wraps
from version import get_version
from hooks import handle_hook
import asyncio
from mcp import VersionMCPServer
 
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

@main.command()
@with_debug
def info() -> None:
	"""Show version information"""
	click.echo(f"Version: {get_version()}")

@main.command()
@with_debug
def hooks_cmd() -> None:
	"""Hook 模式：从 stdin 读取 JSON"""
	handle_hook()

@main.command()
def mcp() -> None:
	"""MCP 服务器模式：启动版本管理 MCP 服务器"""
	server = VersionMCPServer()
	asyncio.run(server.run())

if __name__ == "__main__":
	main()