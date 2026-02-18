from functools import wraps
import asyncio

import rich_click as click

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


@main.command()
@with_debug
def mcp() -> None:
    """启动 MCP Server（Model Context Protocol）
    
    启动 MCP 服务器，让 AI Agent 能直接通过 MCP 协议操作记忆系统。
    
    可用工具:
    - read_memory: 读取记忆
    - create_memory: 创建记忆
    - update_memory: 更新记忆
    - delete_memory: 删除记忆
    - search_memory: 搜索记忆
    - preload_memory: 预加载记忆
    - save_session: 保存会话
    - list_memories: 列出记忆
    - get_memory_stats: 获取统计
    - export_memories: 导出记忆
    - import_memories: 导入记忆
    - add_alias: 添加别名
    - get_memory_versions: 获取版本历史
    - rollback_memory: 回滚记忆
    - diff_versions: 对比版本
    - list_rollbacks: 列出可回滚版本
    - detect_patterns: 检测操作模式
    - detect_conflicts: 检测冲突
    - resolve_conflict: 解决冲突
    - generate_report: 生成分析报告
    - get_recommendations: 获取推荐
    """
    from mcps import main as mcp_main
    asyncio.run(mcp_main())


if __name__ == "__main__":
    main()
