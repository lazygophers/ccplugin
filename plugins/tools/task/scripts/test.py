"""Task 插件测试命令

使用 Claude Agent SDK 模拟 Claude Code 调用，测试插件行为。
"""

import asyncio
import os
import shutil
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
DEFAULT_BASE_URL = "http://127.0.0.1:14005"
DEFAULT_AUTH_TOKEN = "PROXY_MANAGED"
DEFAULT_SONNET_MODEL = "claude-sonnet-4-5"
DEFAULT_OPUS_MODEL = "claude-opus-4-7"
DEFAULT_HAIKU_MODEL = "claude-haiku-4-5"


def get_env_with_default(key: str, default: str = "") -> str:
    """获取环境变量，如果不存在或为空则使用默认值"""
    value = os.environ.get(key, default)
    # 如果环境变量存在但为空字符串，使用默认值
    return value if value else default


def print_message(message: any, verbose: bool = False) -> None:
    """打印消息

    Agent SDK 消息结构：
    - AssistantMessage.content = [ThinkingBlock, TextBlock, ToolUseBlock]
    - UserMessage.content = [ToolResultBlock]
    - ResultMessage.result = str
    - SystemMessage.subtype = init/hook_started/hook_response
    """
    cls = type(message).__name__

    if cls == "SystemMessage":
        if verbose:
            subtype = getattr(message, "subtype", "")
            if subtype == "init":
                data = getattr(message, "data", {})
                plugins = data.get("plugins", [])
                skills = data.get("skills", [])
                agents = data.get("agents", [])
                print("[系统] 会话初始化")
                if plugins:
                    print(f"  插件: {', '.join(p.get('name', '?') for p in plugins)}")
                if skills:
                    print(f"  Skills: {', '.join(skills)}")
                if agents:
                    print(f"  Agents: {', '.join(agents)}")

    elif cls == "ResultMessage":
        result = getattr(message, "result", "")
        if result:
            print("\n" + "=" * 60)
            print("📋 执行结果")
            print("=" * 60)
            print(f"\n{result}\n")
            print("=" * 60)

    elif cls == "AssistantMessage":
        for block in getattr(message, "content", []):
            block_type = type(block).__name__
            if block_type == "TextBlock":
                text = getattr(block, "text", "")
                if text:
                    print(text)
            elif block_type == "ThinkingBlock":
                if verbose:
                    thinking = getattr(block, "thinking", "")
                    if thinking:
                        print(
                            f"  💭 {thinking[:200]}{'...' if len(thinking) > 200 else ''}"
                        )
            elif block_type == "ToolUseBlock":
                name = getattr(block, "name", "")
                tool_input = getattr(block, "input", {})
                if verbose:
                    print(f"  🔧 {name}")
                    if isinstance(tool_input, dict):
                        for k, v in list(tool_input.items())[:3]:
                            print(f"     {k}: {str(v)[:80]}")
                else:
                    print(f"  🔧 {name}")

    elif cls == "UserMessage":
        for block in getattr(message, "content", []):
            if type(block).__name__ == "ToolResultBlock":
                is_error = getattr(block, "is_error", False)
                if verbose:
                    content = str(getattr(block, "content", ""))
                    if is_error:
                        print(f"  ❌ {content[:150]}")
                    else:
                        print(f"  ✓ (结果 {len(content)} 字符)")
                elif is_error:
                    print("  ❌ 工具执行错误")

    elif cls == "ErrorMessage":
        error_msg = getattr(message, "error", message)
        print(f"\n❌ [错误] {error_msg}\n")


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
    help="API 端点 URL（默认: http://127.0.0.1:14005）",
)
@click.option(
    "--api-key",
    default=None,
    help="API 密钥（默认从环境变量读取）",
)
@click.option(
    "--auto-approve",
    is_flag=True,
    default=False,
    help="自动确认所有 AskUserQuestion（选择第一个选项）",
)
@click.option(
    "--cleanup/--no-cleanup",
    default=True,
    help="测试后自动清理产物（默认开启）",
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
    auto_approve: bool,
    cleanup: bool,
):
    """Task 插件测试命令

    直接传入提示词进行测试，类似 claude -p "提示词" 的用法。

    示例:
        task test "修复登录 Bug"
        task test "/task:flow 添加日志功能" --model opus
        task test "优化查询性能" -m haiku -v

    环境变量（带默认值）:
        ANTHROPIC_BASE_URL: API 端点（默认: http://127.0.0.1:14005）
        ANTHROPIC_AUTH_TOKEN 或 ANTHROPIC_API_KEY: API 密钥
        ANTHROPIC_DEFAULT_SONNET_MODEL: sonnet 模型名（默认: claude-sonnet-4-5）
        ANTHROPIC_DEFAULT_OPUS_MODEL: opus 模型名（默认: claude-opus-4-7）
        ANTHROPIC_DEFAULT_HAIKU_MODEL: haiku 模型名（默认: claude-haiku-4-5）
    """
    # 设置环境变量默认值
    base_url = api_url or get_env_with_default("ANTHROPIC_BASE_URL", DEFAULT_BASE_URL)
    auth_token = api_key or get_env_with_default(
        "ANTHROPIC_AUTH_TOKEN",
        get_env_with_default("ANTHROPIC_API_KEY", DEFAULT_AUTH_TOKEN),
    )

    # 模型映射
    model_map = {
        "sonnet": get_env_with_default(
            "ANTHROPIC_DEFAULT_SONNET_MODEL", DEFAULT_SONNET_MODEL
        ),
        "opus": get_env_with_default(
            "ANTHROPIC_DEFAULT_OPUS_MODEL", DEFAULT_OPUS_MODEL
        ),
        "haiku": get_env_with_default(
            "ANTHROPIC_DEFAULT_HAIKU_MODEL", DEFAULT_HAIKU_MODEL
        ),
    }

    # 设置环境变量（Agent SDK 会读取）
    os.environ["ANTHROPIC_BASE_URL"] = base_url
    os.environ["ANTHROPIC_AUTH_TOKEN"] = auth_token

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

    # 构建最终 prompt
    final_prompt = prompt
    if auto_approve:
        final_prompt = (
            "<system-hint>测试模式：当任何 Skill 或 Agent 需要通过 AskUserQuestion 向用户确认时，"
            "自动选择第一个选项并继续，不等待回复。</system-hint>\n\n"
            f"{prompt}"
        )

    print(f"测试提示词: {prompt}")
    print(f"使用模型: {model} ({model_map[model]})")
    print(f"API 端点: {base_url}")
    print(f"允许工具: {', '.join(allowed_tools)}")
    if auto_approve:
        print("自动确认: 开启")
    if load_task_plugin:
        print(f"加载插件: task (路径: {plugin_path})")
    print("-" * 60)

    # 创建消息收集器
    collector = MessageCollector()

    async def run():
        try:
            async with asyncio.timeout(timeout):
                async for message in query(
                    prompt=final_prompt,
                    options=ClaudeAgentOptions(
                        model=model_map[model],
                        setting_sources=["project"],
                        allowed_tools=allowed_tools,
                        permission_mode="bypassPermissions",
                        plugins=plugins,
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

        if collector.actual_model:
            print(f"实际模型: {collector.actual_model}")

        msg_types = {}
        for m in collector.messages:
            msg_types[type(m).__name__] = msg_types.get(type(m).__name__, 0) + 1
        print(f"消息统计: {msg_types}")

        print(f"工具调用: {len(collector.tool_calls)} 次")
        print(f"工具结果: {len(collector.tool_results)} 次")
        errors = sum(1 for r in collector.tool_results if r.get("is_error"))
        if errors:
            print(f"工具错误: {errors} 次")
        print(f"思考次数: {len(collector.thinking_outputs)} 次")

        if collector.tool_calls:
            print("\n工具调用详情:")
            tool_counts = {}
            for call in collector.tool_calls:
                tool_name = call["name"]
                tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
            for tool_name, count in sorted(tool_counts.items()):
                print(f"  {tool_name}: {count}")

        if collector.state_transitions:
            print(f"\n状态流转: {' → '.join(collector.state_transitions)}")
        else:
            print("\n状态流转: (无)")

        print("=" * 60)

    asyncio.run(run())

    if cleanup:
        import subprocess

        lazygophers_dir = os.path.join(os.getcwd(), ".lazygophers")
        if os.path.isdir(lazygophers_dir):
            shutil.rmtree(lazygophers_dir, ignore_errors=True)
            print("\n🧹 已清理 .lazygophers/")

        result = subprocess.run(
            ["git", "diff", "--stat", "--exit-code"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            subprocess.run(["git", "checkout", "--", "."], capture_output=True)
            print("🧹 已恢复 git 工作区")


if __name__ == "__main__":
    test_main()
