"""lrpc 插件 CLI 入口"""

import click

@click.group()
def main():
    """lrpc 高性能 RPC 框架插件"""
    pass

if __name__ == "__main__":
    main()
