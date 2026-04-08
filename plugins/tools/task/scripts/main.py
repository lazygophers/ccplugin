from lib import logging
import click
from functools import wraps
from lib.utils.gitignore import add_gitignore_rule
from hooks import handle_hook
from hooks_skills import handle_hook_skills
from task import task_main


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
	"""Task plugin CLI"""
	pass


@main.command(name="hooks")
def hooks() -> None:
	"""Hook 模式：从 stdin 读取 JSON"""
	handle_hook()


@main.command(name="hooks-skills.bak")
def hooks_skills() -> None:
	"""Hook 模式：处理 skills.bak 相关事件（从 stdin 读取 JSON）"""
	handle_hook_skills()


# 将 task_main（本身是 @click.group）注册为 main 的子命令
main.add_command(task_main, name="task")


if __name__ == "__main__":
	main()
