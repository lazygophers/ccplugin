#!/usr/bin/env python3
"""
b0 可行性实测: 800 内能留下什么

实测三个注入点的实际 token 消耗，评估 800 token 约束下能保留哪些规则。
"""

import json
import sys
from pathlib import Path

# 添加 scripts 目录到 sys.path
SCRIPTS = Path(__file__).resolve().parent.parent / "plugins/tools/skein/scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from skeinlib.token_conversion import estimate_tokens_from_chars
from skeinlib.spec.model import INJECTION_BUDGETS


def get_session_start_output() -> tuple[str, int, int]:
    """获取 session-start 输出和字符数、token数"""
    import subprocess
    import os

    cwd = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        ["python3", "plugins/tools/skein/scripts/spec.py", "session-start"],
        cwd=str(cwd),
        input='{"agent_type": "skein-executor"}',
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )
    data = json.loads(result.stdout)
    ctx = data["hookSpecificOutput"]["additionalContext"]
    chars = len(ctx)
    tokens = estimate_tokens_from_chars(chars)
    return ctx, chars, tokens


def get_subagent_start_output() -> tuple[str, int, int]:
    """获取 subagent-start 输出和字符数、token数"""
    import subprocess
    import os

    cwd = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        ["python3", "plugins/tools/skein/scripts/spec.py", "subagent-start"],
        cwd=str(cwd),
        input='{"agent_type": "skein-executor"}',
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )
    data = json.loads(result.stdout)
    ctx = data["hookSpecificOutput"]["additionalContext"]
    chars = len(ctx)
    tokens = estimate_tokens_from_chars(chars)
    return ctx, chars, tokens


def get_inject_core_output() -> tuple[str, int, int]:
    """获取 inject-core 输出和字符数、token数"""
    import subprocess
    import os

    # 确保在正确的目录运行
    cwd = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        ["python3", "plugins/tools/skein/scripts/spec.py", "inject-core"],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env=os.environ.copy(),
    )
    # 只取 stdout，忽略 stderr
    ctx = result.stdout
    chars = len(ctx)
    tokens = estimate_tokens_from_chars(chars)
    return ctx, chars, tokens


def main():
    print("=" * 70)
    print("b0 可行性实测: 800 token 约束下能留下什么")
    print("=" * 70)

    # 获取三个注入点的实际输出
    session_ctx, session_chars, session_tokens = get_session_start_output()
    subagent_ctx, subagent_chars, subagent_tokens = get_subagent_start_output()
    core_ctx, core_chars, core_tokens = get_inject_core_output()

    print("\n## 实测结果")
    print(f"1. session-start: {session_chars} 字符 ≈ {session_tokens} tokens")
    print(f"   预算: {INJECTION_BUDGETS['session_index']} tokens")
    print(f"   状态: {'✅ 通过' if session_tokens <= INJECTION_BUDGETS['session_index'] else '❌ 超支'}")

    print(f"\n2. inject-core: {core_chars} 字符 ≈ {core_tokens} tokens")
    print(f"   预算: {INJECTION_BUDGETS['session_core']} tokens")
    print(f"   状态: {'✅ 通过' if core_tokens <= INJECTION_BUDGETS['session_core'] else '❌ 超支'}")

    print(f"\n3. subagent-start: {subagent_chars} 字符 ≈ {subagent_tokens} tokens")
    print(f"   预算: {INJECTION_BUDGETS['subagent_core']} tokens")
    print(f"   状态: {'✅ 通过' if subagent_tokens <= INJECTION_BUDGETS['subagent_core'] else '❌ 超支'}")

    total_tokens = session_tokens + core_tokens + subagent_tokens
    total_budget = sum(INJECTION_BUDGETS.values())

    print(f"\n## 总计")
    print(f"实际总 token: {total_tokens} tokens")
    print(f"预算总和: {total_budget} tokens")
    print(f"超标: {total_tokens - total_budget} tokens ({(total_tokens/total_budget - 1)*100:.1f}%)")

    print(f"\n## 结论")
    if total_tokens <= total_budget:
        print("✅ 可行: 三个注入点总计在 800 token 预算内")
        print(f"\n可保留规则清单:")
        print(f"- session-start 索引: {session_tokens} tokens (保留)")
        print(f"- inject-core 全文: {core_tokens} tokens (保留)")
        print(f"- subagent-start 全文: {subagent_tokens} tokens (保留)")
    else:
        print("❌ 不可行: 三个注入点总计超出 800 token 预算")
        print(f"\n问题分析:")
        print(f"- 主要超支来源: inject-core ({core_tokens} tokens > 预算 {INJECTION_BUDGETS['session_core']} tokens)")
        print(f"- 超支幅度: {core_tokens - INJECTION_BUDGETS['session_core']} tokens ({(core_tokens/INJECTION_BUDGETS['session_core'] - 1)*100:.1f}%)")

        print(f"\n压缩到 800 token 需要压掉:")
        excess_tokens = total_tokens - total_budget
        print(f"- 需减少: {excess_tokens} tokens")
        print(f"- 压缩比例: {(excess_tokens / total_tokens) * 100:.1f}%")
        print(f"\n按 design.md 指出，现状约 38000 token 需压掉 98%，")
        print(f"这要求「常驻只留索引 + 全文改按需检索」的结构性取舍。")

        print(f"\n建议:")
        print(f"1. 按 PRD 约定回报用户重定口径，禁自行放宽")
        print(f"2. 若确认 800 token 为硬约束，需采用结构性方案:")
        print(f"   - session-start: 只保留索引 ({session_tokens} tokens ✅)")
        print(f"   - inject-core: 降级为按需检索 ({core_tokens} tokens ❌ 超支)")
        print(f"   - subagent-start: 可能需压缩或分类注入 ({subagent_tokens} tokens ✅)")


if __name__ == "__main__":
    main()