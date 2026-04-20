"""Task 插件测试命令

使用 Claude Agent SDK 模拟 Claude Code 调用，测试插件行为。
"""

import asyncio
import os
import sys
from pathlib import Path

import click

try:
    from claude_agent_sdk import query, ClaudeAgentOptions
except ImportError:
    print("错误: 未安装 claude-agent-sdk")
    print("请运行: uv pip install claude-agent-sdk")
    sys.exit(1)

from test_helpers import MessageCollector


# 环境变量默认值
DEFAULT_BASE_URL = "https://api.anthropic.com"
DEFAULT_SONNET_MODEL = "claude-sonnet-4-5"
DEFAULT_OPUS_MODEL = "claude-opus-4-7"
DEFAULT_HAIKU_MODEL = "claude-haiku-4-5"


def get_env_with_default(key: str, default: str = "") -> str:
    """获取环境变量，如果不存在则使用默认值"""
    return os.environ.get(key, default)


def print_message(message: any, verbose: bool = False) -> None:
    """打印消息（根据 verbose 级别）"""
    msg_type = getattr(message, "type", "unknown")

    if msg_type == "system":
        subtype = getattr(message, "subtype", "")
        if verbose:
            print(f"[系统] {subtype}: {getattr(message, 'data', {})}")
        if subtype == "init":
            session_id = getattr(message, "session_id", "N/A")
            print(f"[系统] 会话初始化: {session_id}")

    elif msg_type == "result":
        result = getattr(message, "result", "")
        if result:
            print(f"\n{result}\n")
        else:
            print("[结果] (空)")

    elif msg_type == "tool_use":
        tool_name = getattr(message, "name", "unknown")
        if verbose:
            print(f"[工具] 调用 {tool_name}: {getattr(message, 'input', {})}")
        else:
            print(f"[工具] {tool_name}")

    elif msg_type == "text":
        text = getattr(message, "text", "")
        if text:
            print(f"[输出] {text}")

    elif msg_type == "error" or msg_type == "input_json_delta":
        if verbose:
            print(f"[{msg_type}] {message}")

    elif verbose:
        # 其他未处理的消息类型
        print(f"[{msg_type}] {message}")


@click.command()
@click.argument("prompt", required=True)
@click.option(
    "--model",
    "-m",
    type=click.Choice(["sonnet", "opus", "haiku"]),
    default="sonnet",
    help="使用的模型",
)
@click.option("--verbose", "-v", is_flag=True, help="详细输出")
@click.option("--timeout", "-t", type=int, default=300, help="超时时间（秒）")
@click.option(
    "--tools",
    multiple=True,
    help="允许使用的工具（可多次指定），默认为常用工具集",
)
@click.option(
    "--load-task-plugin",
    is_flag=True,
    default=True,
    help="加载 task 插件（默认启用）",
)
@click.option(
    "--api-url",
    default=None,
    help=f"API 端点 URL（默认: {DEFAULT_BASE_URL}）",
)
@click.option(
    "--api-key",
    default=None,
    help="API 密钥（默认从环境变量读取）",
)
def test_main(
    prompt: str,
    model: str,
    verbose: bool,
    timeout: int,
    tools: tuple,
    load_task_plugin: bool,
    api_url: str,
    api_key: str,
):
    """Task 插件测试命令

    直接传入提示词进行测试，类似 claude -p "提示词" 的用法。

    示例:
        task test "修复登录 Bug"
        task test "/task:flow 添加日志功能" --model opus
        task test "优化查询性能" -m haiku -v

    环境变量（带默认值）:
        ANTHROPIC_BASE_URL: API 端点（默认: https://api.anthropic.com）
        ANTHROPIC_AUTH_TOKEN 或 ANTHROPIC_API_KEY: API 密钥
        ANTHROPIC_DEFAULT_SONNET_MODEL: sonnet 模型名（默认: claude-sonnet-4-5）
        ANTHROPIC_DEFAULT_OPUS_MODEL: opus 模型名（默认: claude-opus-4-7）
        ANTHROPIC_DEFAULT_HAIKU_MODEL: haiku 模型名（默认: claude-haiku-4-5）
    """
    # 设置环境变量默认值
    base_url = api_url or get_env_with_default("ANTHROPIC_BASE_URL", DEFAULT_BASE_URL)
    auth_token = api_key or get_env_with_default(
        "ANTHROPIC_AUTH_TOKEN", get_env_with_default("ANTHROPIC_API_KEY", "")
    )

    # 模型映射
    model_map = {
        "sonnet": get_env_with_default(
            "ANTHROPIC_DEFAULT_SONNET_MODEL", DEFAULT_SONNET_MODEL
        ),
        "opus": get_env_with_default("ANTHROPIC_DEFAULT_OPUS_MODEL", DEFAULT_OPUS_MODEL),
        "haiku": get_env_with_default(
            "ANTHROPIC_DEFAULT_HAIKU_MODEL", DEFAULT_HAIKU_MODEL
        ),
    }

    # 设置环境变量（Agent SDK 会读取）
    os.environ["ANTHROPIC_BASE_URL"] = base_url
    if auth_token:
        os.environ["ANTHROPIC_AUTH_TOKEN"] = auth_token
    else:
        print("⚠️  警告: 未设置 API 密钥")
        print("请设置环境变量 ANTHROPIC_AUTH_TOKEN 或 ANTHROPIC_API_KEY")
        print("或使用 --api-key 参数")

    # 默认工具集
    default_tools = [
        "Read",
        "Write",
        "Edit",
        "Glob",
        "Grep",
        "Bash",
        "AskUserQuestion",
    ]

    # 使用指定的工具或默认工具
    allowed_tools = list(tools) if tools else default_tools

    # 获取插件路径（当前目录的父目录）
    plugin_path = str(Path(__file__).parent.parent.absolute())

    # 构建插件配置
    plugins = []
    if load_task_plugin:
        plugins.append({"type": "local", "path": plugin_path})

    print(f"测试提示词: {prompt}")
    print(f"使用模型: {model} ({model_map[model]})")
    print(f"API 端点: {base_url}")
    print(f"允许工具: {', '.join(allowed_tools)}")
    if load_task_plugin:
        print(f"加载插件: task (路径: {plugin_path})")
    print("-" * 60)

    # 创建消息收集器
    collector = MessageCollector()

    async def run():
        try:
            async with asyncio.timeout(timeout):
                async for message in query(
                    prompt=prompt,
                    options=ClaudeAgentOptions(
                        model=model_map[model],  # 使用映射后的实际模型名
                        setting_sources=["project"],  # 加载 .claude/ 配置
                        allowed_tools=allowed_tools,
                        permission_mode="bypassPermissions",
                        plugins=plugins,  # 加载插件
                    ),
                ):
                    collector.add_message(message)
                    print_message(message, verbose=verbose)

        except asyncio.TimeoutError:
            print(f"\n错误: 测试超时（{timeout}秒）")
            sys.exit(1)

        except KeyboardInterrupt:
            print("\n测试被用户中断")
            sys.exit(1)

        except Exception as e:
            print(f"\n错误: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)

        # 输出摘要
        print("\n" + "=" * 60)
        print("测试摘要")
        print("=" * 60)
        print(f"消息数量: {len(collector.messages)}")
        print(f"工具调用数: {len(collector.tool_calls)}")

        if collector.tool_calls:
            print("\n调用的工具:")
            tool_counts = {}
            for call in collector.tool_calls:
                tool_name = call["name"]
                tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1

            for tool_name, count in sorted(tool_counts.items()):
                print(f"  - {tool_name}: {count} 次")

        if collector.state_transitions:
            print(f"\n状态转换: {' → '.join(collector.state_transitions)}")
            print(f"最终状态: {collector.get_final_state()}")

        print("=" * 60)

    asyncio.run(run())


if __name__ == "__main__":
    test_main()
