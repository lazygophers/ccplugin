"""fasthttp 插件主入口"""
import click
from hooks import handle_hook

@click.group()
def main():
    """fasthttp 库插件命令"""
    pass

@main.command()
def hooks():
    """处理 Hook 事件"""
    handle_hook()

if __name__ == "__main__":
    main()
