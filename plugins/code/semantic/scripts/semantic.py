#!/usr/bin/env python3
"""
Claude Code 语义搜索插件 CLI 入口点

支持两种运行模式：
  1. MCP 服务器模式 - 提供 MCP 工具接口
  2. 正常 CLI 模式 - 直接语义搜索操作
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到 sys.path
script_path = Path(__file__).resolve().parent
plugin_path = script_path.parent
project_root = plugin_path.parent.parent

if not (project_root / 'lib').exists():
    # 备选：向上查找
    current = Path(__file__).resolve().parent
    for _ in range(5):
        if (current / 'lib').exists():
            project_root = current
            break
        current = current.parent

# 确保能导入到原始的 semantic_old.py（作为核心模块）
sys.path.insert(0, str(script_path))
sys.path.insert(1, str(project_root))


def run_mcp_mode():
    """运行 MCP 服务器模式"""
    try:
        from mcp_server import SemanticSearchMCPServer
        import logging
        from logging.handlers import RotatingFileHandler

        # 设置日志
        log_dir = Path.home() / ".lazygophers" / "ccplugin"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "error.log"

        logger = logging.getLogger("semantic-mcp-server")
        logger.setLevel(logging.INFO)

        file_handler = RotatingFileHandler(
            str(log_file),
            maxBytes=100 * 1024 * 1024,
            backupCount=2,
            encoding='utf-8'
        )
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(file_handler)
        logger.propagate = False

        server = SemanticSearchMCPServer()
        asyncio.run(server.run())
    except ImportError as e:
        print(f"MCP 依赖不可用: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"MCP 服务器错误: {e}", file=sys.stderr)
        sys.exit(1)


def run_cli_mode(args):
    """运行 CLI 模式 - 将参数传递给原始 semantic_old.py 的 main 函数"""
    try:
        # 导入原始的 semantic 模块功能
        from semantic_old import main as semantic_main

        # 设置 sys.argv 为传递的参数
        sys.argv = ["semantic.py"] + args

        # 调用原始的 main 函数
        semantic_main()
    except Exception as e:
        print(f"语义搜索错误: {e}", file=sys.stderr)
        sys.exit(1)


def show_help():
    """显示帮助信息"""
    print("""使用方法:
  semantic [command] [options]           # 语义搜索操作（默认）
  semantic --mode mcp                    # 启动 MCP 服务器
  semantic -h, --help                    # 显示帮助信息

命令 (默认模式):
  init [--path PATH]                     # 初始化代码索引
  index [--path PATH] [--incremental]    # 构建代码索引
  search <query>                         # 语义搜索代码
  stats [--verbose]                      # 显示索引统计信息

选项:
  --mode mcp                 以 MCP 服务器模式运行
  --path PATH                指定代码目录路径
  --incremental              增量索引模式
  --verbose                  详细输出
  --debug                    启用调试日志

示例:
  semantic init                          # 初始化索引
  semantic index --path ./src            # 构建索引
  semantic search "find user auth"       # 搜索相关代码
  semantic stats                         # 显示统计
  semantic --mode mcp                    # 启动 MCP 服务器
""")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)

    # 处理帮助标志
    if sys.argv[1] in ["-h", "--help"]:
        show_help()
        sys.exit(0)

    # 处理 MCP 模式
    if "--mode" in sys.argv:
        mode_idx = sys.argv.index("--mode")
        if mode_idx + 1 >= len(sys.argv):
            print("错误: --mode 需要指定值", file=sys.stderr)
            sys.exit(1)

        mode = sys.argv[mode_idx + 1]

        if mode == "mcp":
            run_mcp_mode()
        else:
            print(f"错误: 未知的模式: {mode}（有效值: mcp）", file=sys.stderr)
            sys.exit(1)

    # 正常 CLI 模式 - 将所有参数传递给原始的 semantic_old
    else:
        run_cli_mode(sys.argv[1:])


if __name__ == "__main__":
    main()
