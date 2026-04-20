"""Task 插件测试命令

使用 Claude Agent SDK 模拟 Claude Code 调用，测试插件行为。
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import click

try:
    from claude_agent_sdk import query, ClaudeAgentOptions
except ImportError:
    print("错误: 未安装 claude-agent-sdk")
    print("请运行: uv pip install claude-agent-sdk")
    sys.exit(1)

from test_helpers import MessageCollector, TaskStateVerifier, TestReport, TestVerifier


def load_scenarios() -> Dict[str, Any]:
    """加载测试场景配置"""
    scenarios_file = Path(__file__).parent / "test_scenarios.json"

    if not scenarios_file.exists():
        return {}

    with open(scenarios_file) as f:
        return json.load(f)


def print_message(message: Any, verbose: bool = False) -> None:
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


async def run_test(
    scenario_name: str, model: str, verbose: bool = False, timeout: int = 300
) -> TestReport:
    """运行单个测试场景

    Args:
        scenario_name: 场景名称
        model: 使用的模型 (sonnet/opus/haiku)
        verbose: 是否详细输出
        timeout: 超时时间（秒）

    Returns:
        TestReport: 测试报告
    """
    scenarios = load_scenarios()

    if scenario_name not in scenarios:
        print(f"错误: 未找到测试场景 '{scenario_name}'")
        print(f"可用场景: {', '.join(scenarios.keys())}")
        sys.exit(1)

    test_case = scenarios[scenario_name]

    print(f"开始测试: {test_case['name']}")
    print(f"描述: {test_case.get('description', 'N/A')}")
    print(f"模型: {model}")
    print(f"Prompt: {test_case['prompt']}")
    print("-" * 60)

    # 创建消息收集器
    collector = MessageCollector()

    # 执行查询
    try:
        async with asyncio.timeout(timeout):
            async for message in query(
                prompt=test_case["prompt"],
                options=ClaudeAgentOptions(
                    model=model,
                    setting_sources=["project"],  # 加载 .claude/ 配置
                    allowed_tools=test_case.get("allowed_tools", []),
                    permission_mode="bypassPermissions",
                ),
            ):
                collector.add_message(message)
                print_message(message, verbose=verbose)

    except asyncio.TimeoutError:
        print(f"\n错误: 测试超时（{timeout}秒）")
        return TestReport(results=[])

    except KeyboardInterrupt:
        print("\n测试被用户中断")
        return TestReport(results=[])

    except Exception as e:
        print(f"\n错误: {e}")
        return TestReport(results=[])

    # 验证结果
    print("\n" + "=" * 60)
    print("验证结果...")
    print("=" * 60)

    verifier = TestVerifier(collector, test_case.get("expectations", {}))
    report = verifier.verify_all()

    return report


@click.group()
def test_main():
    """Task 插件测试命令"""
    pass


@test_main.command()
@click.option(
    "--scenario",
    type=str,
    default="simple-bug-fix",
    help="测试场景名称",
)
@click.option(
    "--model",
    type=click.Choice(["sonnet", "opus", "haiku"]),
    default="sonnet",
    help="使用的模型",
)
@click.option("--verbose", is_flag=True, help="详细输出")
@click.option("--timeout", type=int, default=300, help="超时时间（秒）")
def workflow(scenario: str, model: str, verbose: bool, timeout: int):
    """测试完整工作流

    示例:
        task test workflow --scenario simple-bug-fix --model sonnet --verbose
        task test workflow --scenario new-feature --model opus
    """

    async def run():
        report = await run_test(scenario, model, verbose, timeout)
        print(report)
        sys.exit(0 if report.all_passed else 1)

    asyncio.run(run())


@test_main.command()
@click.option(
    "--name",
    type=str,
    required=True,
    help="Skill 名称 (flow/align/explore/plan/exec/verify/adjust/done/resume)",
)
@click.option(
    "--scenario",
    type=str,
    help="测试场景名称（可选，默认使用 {name}-only）",
)
@click.option(
    "--model",
    type=click.Choice(["sonnet", "opus", "haiku"]),
    default="sonnet",
    help="使用的模型",
)
@click.option("--verbose", is_flag=True, help="详细输出")
@click.option("--timeout", type=int, default=300, help="超时时间（秒）")
def skill(
    name: str, scenario: Optional[str], model: str, verbose: bool, timeout: int
):
    """测试单个 Skill

    示例:
        task test skill --name flow --scenario simple-bug-fix --model sonnet
        task test skill --name explore --model opus --verbose
    """
    # 如果未指定场景，使用默认场景
    if not scenario:
        scenario = f"{name}-only"

    async def run():
        report = await run_test(scenario, model, verbose, timeout)
        print(report)
        sys.exit(0 if report.all_passed else 1)

    asyncio.run(run())


@test_main.command()
@click.option(
    "--name",
    type=str,
    required=True,
    help="Agent 名称 (explore/plan/verify/adjust/done)",
)
@click.option(
    "--input",
    type=str,
    required=True,
    help="测试输入（任务描述）",
)
@click.option(
    "--model",
    type=click.Choice(["sonnet", "opus", "haiku"]),
    default="sonnet",
    help="使用的模型",
)
@click.option("--verbose", is_flag=True, help="详细输出")
@click.option("--timeout", type=int, default=300, help="超时时间（秒）")
def agent(name: str, input: str, model: str, verbose: bool, timeout: int):
    """测试单个 Agent

    示例:
        task test agent --name explore --input "修复登录问题" --model sonnet
        task test agent --name plan --input "添加日志功能" --model opus
    """
    print(f"开始测试 Agent: {name}")
    print(f"输入: {input}")
    print(f"模型: {model}")
    print("-" * 60)

    # 创建消息收集器
    collector = MessageCollector()

    async def run():
        try:
            async with asyncio.timeout(timeout):
                async for message in query(
                    prompt=f"/task:{name} {input}",
                    options=ClaudeAgentOptions(
                        model=model,
                        setting_sources=["project"],
                        allowed_tools=[
                            "Read",
                            "Glob",
                            "Grep",
                            "Bash",
                            "AskUserQuestion",
                        ],
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
            sys.exit(1)

        # 输出摘要
        print("\n" + "=" * 60)
        print("测试摘要")
        print("=" * 60)
        print(f"消息数量: {len(collector.messages)}")
        print(f"工具调用: {len(collector.tool_calls)}")
        if collector.tool_calls:
            print("\n调用的工具:")
            for call in collector.tool_calls:
                print(f"  - {call['name']}")
        print("=" * 60)

    asyncio.run(run())


@test_main.command()
def list_scenarios():
    """列出所有可用的测试场景"""
    scenarios = load_scenarios()

    if not scenarios:
        print("未找到测试场景配置")
        return

    print("可用的测试场景:")
    print("=" * 60)

    for name, config in scenarios.items():
        print(f"\n{name}")
        print(f"  名称: {config['name']}")
        print(f"  描述: {config.get('description', 'N/A')}")
        print(f"  Prompt: {config['prompt']}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_main()
