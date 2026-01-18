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

# 添加脚本目录到 sys.path，使 lib 指向本地 lib/
script_path = Path(__file__).resolve().parent
sys.path.insert(0, str(script_path))

try:
    from lib.notify import notify, speak, init_notify_config
    from lib.notify.init_config import get_effective_config
    from lib.notify.hooks import handle_stop_hook, handle_notification_hook
    from lib.notify.mcp_server import run_mcp_server
    from lib.notify.simple_hook import main as simple_hook_main
    from lib.notify.pretooluse_hook import main as pretooluse_hook_main
    from lib.notify.posttooluse_hook import main as posttooluse_hook_main
    from lib.notify.precompact_hook import main as precompact_hook_main
    from lib.notify.notification_hook import main as notification_hook_main
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
  notify <message> [title] [timeout] --voice     # 发送通知并语音播报
  notify <message> [title] [timeout] --voice-only # 仅语音播报
  notify --mode mcp [--debug]              # 启动 MCP 服务器
  notify --mode hook --hook-event EVENT   # 处理 hook 事件
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
  --hook-event EVENT      Hook 事件类型:
                          - SessionStart, SessionEnd
                          - UserPromptSubmit
                          - PreToolUse, PostToolUse
                          - Notification
                          - Stop
                          - SubagentStop
                          - PreCompact
  --voice                 启用语音播报（与通知同时进行）
  --voice-only            仅语音播报，不显示系统通知
  --debug                 启用调试日志
  -v, --verbose           详细输出（用于 init 模式）

示例:
  notify '任务已完成'                      # 使用默认标题
  notify '任务已完成' '完成'               # 指定标题
  notify '任务已完成' '完成' 8000          # 指定标题和超时
  notify '任务已完成' '完成' 8000 --voice  # 通知 + 语音播报
  notify '任务已完成' --voice-only        # 仅语音播报
  notify --mode mcp                        # 启动 MCP 服务器
  notify --mode hook --hook-event Stop    # 处理 Stop hook
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
            if "--hook-event" not in sys.argv:
                print("错误: --mode hook 需要 --hook-event 参数", file=sys.stderr)
                sys.exit(1)

            event_idx = sys.argv.index("--hook-event")
            if event_idx + 1 >= len(sys.argv):
                print("错误: --hook-event 需要指定值", file=sys.stderr)
                sys.exit(1)

            hook_event = sys.argv[event_idx + 1]

            # Hook 事件处理映射
            try:
                if hook_event == "Stop":
                    exit_code = handle_stop_hook()
                    sys.exit(exit_code)
                elif hook_event == "Notification":
                    exit_code = handle_notification_hook()
                    sys.exit(exit_code)
                elif hook_event in ("SessionStart", "SessionEnd"):
                    # 对于 SessionStart，调用初始化；对于 SessionEnd，使用 simple_hook
                    if hook_event == "SessionStart":
                        success = init_notify_config(verbose=False)
                        sys.exit(0 if success else 1)
                    else:
                        exit_code = simple_hook_main(hook_event)
                        sys.exit(exit_code)
                elif hook_event in ("UserPromptSubmit", "SubagentStop"):
                    exit_code = simple_hook_main(hook_event)
                    sys.exit(exit_code)
                elif hook_event == "PreToolUse":
                    exit_code = pretooluse_hook_main()
                    sys.exit(exit_code)
                elif hook_event == "PostToolUse":
                    exit_code = posttooluse_hook_main()
                    sys.exit(exit_code)
                elif hook_event == "PreCompact":
                    exit_code = precompact_hook_main()
                    sys.exit(exit_code)
                else:
                    print(f"错误: 未知的 hook 事件: {hook_event}", file=sys.stderr)
                    sys.exit(1)
            except Exception as e:
                if debug:
                    print(f"Hook 处理错误: {e}", file=sys.stderr)
                sys.exit(0)  # Hook 错误不应中断主程序

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
        # 检查语音参数
        voice_enabled = "--voice" in sys.argv
        voice_only = "--voice-only" in sys.argv

        # 移除语音参数后的参数列表
        args = [arg for arg in sys.argv[1:] if arg not in ["--voice", "--voice-only"]]

        if len(args) < 1:
            show_help()
            sys.exit(0)

        # 解析消息、标题、超时
        message = args[0]
        title = args[1] if len(args) > 1 else "Claude Code"

        timeout = 5000
        if len(args) > 2:
            try:
                timeout = int(args[2])
            except ValueError:
                print(f"错误: 超时时间必须是整数，得到: {args[2]}", file=sys.stderr)
                sys.exit(1)

        # 读取配置，检查是否应该发送通知
        config = get_effective_config()

        # 获取全局级别的配置（如果存在）
        config_notify_enabled = config.get('notify', True) if config else True
        config_voice_enabled = config.get('voice', False) if config else False

        # 执行操作
        success = True

        # 检查配置是否禁用了通知
        if not config_notify_enabled and not voice_only:
            # 配置禁用了通知，不执行任何操作
            sys.exit(0)

        # 如果只做语音播报
        if voice_only:
            # 检查配置是否禁用了语音
            if config_voice_enabled or not config:
                success = speak(message)
            # 否则配置禁用了语音播报，不执行
        else:
            # 先发送通知（已经检查过配置了）
            success = notify(title, message, timeout)
            # 如果启用语音播报（命令行参数或配置），则播报消息
            if (voice_enabled or config_voice_enabled) and success:
                speak(message)

        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
