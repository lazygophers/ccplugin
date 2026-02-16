from functools import wraps

import click

from lib import logging
from web import start_web
from hooks import handle_hook


def with_debug(func):
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
    pass


@main.command()
@with_debug
def hooks() -> None:
    """处理 Claude Code hooks"""
    handle_hook()


@main.command()
@click.option("-p", "--port", type=int, default=None, help="端口号（默认自动查找可用端口）")
@click.option("--no-browser", is_flag=True, help="不自动打开浏览器")
@click.option("-r", "--reload", "enable_reload", is_flag=True, help="启用热重载（开发模式）")
@with_debug
def web(port, no_browser: bool, enable_reload: bool) -> None:
    """启动 Web 管理界面"""
    logging.enable_debug()
    start_web(port=port, open_browser=not no_browser, reload=enable_reload)


if __name__ == "__main__":
    main()