"""Task 插件测试命令

使用 Claude Agent SDK 模拟 Claude Code 调用，测试插件行为。
"""

import asyncio
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


def print_message(message: any, verbose: bool = False) -> None:
    """打印消息（根据 verbose 级别）"""
    msg_type = getattr(message, "type", "unknown")

    if msg_type == "system":
        subtype = getattr(message, "subtype", "")
        if subtype == "init" and verbose:
            session_id = getattr(message, "session_id", "N/A")
            print(f"[系统] 会话初始化: {session_id}")

    elif msg_type == "result":
        result = getattr(message, "result", "")
        if result:
            print(f"\n{result}\n")

    elif msg_type == "tool_use" and verbose:
        tool_name = getattr(message, "name", "unknown")
        print(f"[工具] 调用 {tool_name}")

    elif msg_type == "text" and verbose:
        text = getattr(message, "text", "")
        if text:
            print(f"[输出] {text}")


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
def test_main(prompt: str, model: str, verbose: bool, timeout: int, tools: tuple):
    """Task 插件测试命令

    直接传入提示词进行测试，类似 claude -p "提示词" 的用法。

    示例:
        task test "修复登录 Bug"
        task test "/task:flow 添加日志功能" --model opus
        task test "优化查询性能" -m haiku -v
    """
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

    print(f"测试提示词: {prompt}")
    print(f"使用模型: {model}")
    print(f"允许工具: {', '.join(allowed_tools)}")
    print("-" * 60)

    # 创建消息收集器
    collector = MessageCollector()

    async def run():
        try:
            async with asyncio.timeout(timeout):
                async for message in query(
                    prompt=prompt,
                    options=ClaudeAgentOptions(
                        model=model,
                        setting_sources=["project"],  # 加载 .claude/ 配置
                        allowed_tools=allowed_tools,
                        permission_mode="bypassPermissions",
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
