#!/usr/bin/env python3
"""
Claude Code 系统通知插件 CLI 入口点

支持四种运行模式：
  1. MCP 服务器模式 - 提供 MCP 工具接口
  2. Hook 处理模式 - 处理 Stop/Notification hooks
  3. 配置初始化模式 - 初始化用户和项目通知配置
  4. 正常通知模式 - 直接发送系统通知
"""

import sys
import logging
import asyncio
from pathlib import Path
from typing import Optional

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

sys.path.insert(0, str(project_root))

try:
    from lib.notify import notify, init_notify_config
    from lib.notify.hooks import handle_stop_hook, handle_notification_hook
    from lib.notify.mcp_server import run_mcp_server
except ImportError as e:
    print(f"导入错误: {e}", file=sys.stderr)
    sys.exit(1)


def setup_logging(debug: bool = False):
    """设置日志"""
    log_dir = Path.home() / ".lazygophers" / "ccplugin"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "error.log"

    from logging.handlers import RotatingFileHandler

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

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


def show_help():
    """显示帮助信息"""
    print("""使用方法:
  notify <message> [title] [timeout]      # 发送系统通知
  notify --mode mcp [--debug]              # 启动 MCP 服务器
  notify --mode hook --hook-type TYPE     # 处理 hook（TYPE: stop|notification）
  notify --mode init [-v, --verbose]      # 初始化配置文件
  notify -h, --help                        # 显示帮助信息

参数:
  message        通知消息（必填）
  title          通知标题（可选，默认: 'Claude Code'）
  timeout        显示时间（毫秒，可选，默认: 5000）

选项:
  --mode mcp              以 MCP 服务器模式运行
  --mode hook             处理 hook 事件
  --mode init             初始化通知配置文件
  --hook-type TYPE        Hook 类型：stop 或 notification
  --debug                 启用调试日志
  -v, --verbose           详细输出（用于 init 模式）

示例:
  notify '任务已完成'                      # 使用默认标题
  notify '任务已完成' '完成'               # 指定标题
  notify '任务已完成' '完成' 8000          # 指定标题和超时
  notify --mode mcp                        # 启动 MCP 服务器
  notify --mode hook --hook-type stop     # 处理 Stop hook
  notify --mode init -v                   # 初始化配置文件（详细输出）
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
        debug = "--debug" in sys.argv

        if debug:
            setup_logging(debug=True)

        if mode == "mcp":
            try:
                asyncio.run(run_mcp_server())
            except KeyboardInterrupt:
                sys.exit(0)
            except Exception as e:
                print(f"MCP 服务器错误: {e}", file=sys.stderr)
                sys.exit(1)

        elif mode == "hook":
            if "--hook-type" not in sys.argv:
                print("错误: --mode hook 需要 --hook-type 参数", file=sys.stderr)
                sys.exit(1)

            hook_type_idx = sys.argv.index("--hook-type")
            if hook_type_idx + 1 >= len(sys.argv):
                print("错误: --hook-type 需要指定值", file=sys.stderr)
                sys.exit(1)

            hook_type = sys.argv[hook_type_idx + 1]

            if hook_type == "stop":
                exit_code = handle_stop_hook()
                sys.exit(exit_code)
            elif hook_type == "notification":
                exit_code = handle_notification_hook()
                sys.exit(exit_code)
            else:
                print(f"错误: 未知的 hook 类型: {hook_type}（有效值: stop, notification）", file=sys.stderr)
                sys.exit(1)

        elif mode == "init":
            verbose = "-v" in sys.argv or "--verbose" in sys.argv
            try:
                success = init_notify_config(verbose=verbose)
                if success:
                    if verbose:
                        print("✓ 配置初始化完成")
                    sys.exit(0)
                else:
                    print("✗ 配置初始化失败", file=sys.stderr)
                    sys.exit(1)
            except Exception as e:
                print(f"配置初始化错误: {e}", file=sys.stderr)
                sys.exit(1)

        else:
            print(f"错误: 未知的模式: {mode}（有效值: mcp, hook, init）", file=sys.stderr)
            sys.exit(1)

    # 正常通知模式
    else:
        # 解析消息、标题、超时
        message = sys.argv[1]
        title = sys.argv[2] if len(sys.argv) > 2 else "Claude Code"

        timeout = 5000
        if len(sys.argv) > 3:
            try:
                timeout = int(sys.argv[3])
            except ValueError:
                print(f"错误: 超时时间必须是整数，得到: {sys.argv[3]}", file=sys.stderr)
                sys.exit(1)

        # 发送通知
        success = notify(title, message, timeout)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
