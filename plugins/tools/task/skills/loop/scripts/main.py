from lib import logging
import click
from functools import wraps

# Support both direct execution and module import
try:
    from .md2html import md2html_command
    from .fill_plan_template import fill_plan_command
except ImportError:
    from md2html import md2html_command
    from fill_plan_template import fill_plan_command


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
    Task management plugin CLI.
    """
    pass


# 注册命令
main.add_command(md2html_command, name="md2html")
main.add_command(fill_plan_command, name="fill-plan")


if __name__ == "__main__":
    main()
