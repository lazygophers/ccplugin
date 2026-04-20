import click

from hooks import handle_hook
from task import task_main
from test import test_main


@click.group()
@click.pass_context
def main(ctx) -> None:
	"""Task plugin CLI"""
	pass


@main.command(name="hooks")
def hooks() -> None:
	"""Hook 模式：从 stdin 读取 JSON"""
	handle_hook()


# 将 task_main（本身是 @click.group）注册为 main 的子命令
main.add_command(task_main, name="task")

# 注册 test 子命令
main.add_command(test_main, name="test")


if __name__ == "__main__":
	main()
