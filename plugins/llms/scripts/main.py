"""
LLMS.txt Plugin - Main Entry Point

处理 llms.txt 相关的 hook 事件
"""

from lib import logging
from hooks import handle_hook
import click
from functools import wraps


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
    LLMS.txt Plugin - Hook 处理入口

    此插件通过 Agent 来生成 llms.txt 文件，
    scripts 仅负责处理 hook 事件。
    """
    pass


@main.command()
@with_debug
def hooks() -> None:
    """Hook 模式：从 stdin 读取 JSON"""
    handle_hook()


if __name__ == "__main__":
    main()
