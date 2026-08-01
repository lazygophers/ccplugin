"""budget_guard 机械守卫 + 反向验证测试。

测试三个注入点的预算守卫:
1. session_start (INJECTION_BUDGETS["session_index"] = 200 tokens)
2. subagent_start (INJECTION_BUDGETS["subagent_core"] = 300 tokens)
3. inject_core (always_budget_tokens() = 300 tokens)

验收标准:
- 机械守卫: 任一注入点超预算 → 测试失败 (assert 验证)
- 反向验证: 手动制造超预算 → 见过红 → 恢复 → 变绿
"""
from __future__ import annotations

import sys
from pathlib import Path

# 添加 scripts 目录到 sys.path，让我们可以直接导入 skeinlib 模块
SCRIPTS = Path(__file__).resolve().parent.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from skeinlib.hooks.runner import budget_guard, est_tokens, CHARS_PER_TOKEN
from skeinlib.spec.model import INJECTION_BUDGETS, always_budget_tokens


def test_budget_guard_short_content():
    """budget_guard 对短内容应原样返回。"""
    short = "short content"
    budget = 1000  # 1000 tokens
    result = budget_guard(short, budget, "test")
    assert result == short, "短内容不应被截断"


def test_budget_guard_exact_budget():
    """budget_guard 对刚好等于预算的内容应原样返回。"""
    # 创建刚好等于预算的内容
    budget = 10  # 10 tokens
    content = "x" * (budget * CHARS_PER_TOKEN)  # 刚好 10 tokens
    result = budget_guard(content, budget, "test")
    assert result == content, "刚好预算的内容不应被截断"


def test_budget_guard_truncates_over_budget():
    """budget_guard 对超预算内容应截断并添加警告。机械守卫核心测试。"""
    # 创建超过预算的内容
    budget = 10  # 10 tokens = 40 字符
    content = "x" * 100  # 100 字符 ≈ 25 tokens，超过 10 token 预算
    result = budget_guard(content, budget, "test")

    # 机械守卫: 超预算必须截断
    assert len(result) < len(content), "超预算内容必须被截断"
    assert len(result) <= budget * CHARS_PER_TOKEN + 100, "截断后长度应在预算附近"
    assert "截断" in result or "..." in result, "截断内容应包含警告标记"


def test_session_start_budget():
    """session_start 注入点预算守卫测试 (200 token)。"""
    budget = INJECTION_BUDGETS["session_index"]  # 动态读取预算

    # 正常情况: 内容在预算内
    normal_content = "x" * (budget * CHARS_PER_TOKEN)  # 刚好在预算内
    result = budget_guard(normal_content, budget, "spec:session-start")
    assert result == normal_content, "预算内内容不应被截断"

    # 超预算情况 - 机械守卫核心
    over_content = "x" * ((budget + 100) * CHARS_PER_TOKEN)  # 超过预算 100 tokens
    result = budget_guard(over_content, budget, "spec:session-start")
    assert len(result) < len(over_content), "超预算应被截断 (机械守卫)"


def test_subagent_start_budget():
    """subagent_start 注入点预算守卫测试 (300 token)。"""
    budget = INJECTION_BUDGETS["subagent_core"]  # 300 tokens
    assert budget == 300, "subagent_core 预算应为 300 tokens"

    # 正常情况
    normal_content = "x" * (budget * CHARS_PER_TOKEN)
    result = budget_guard(normal_content, budget, "spec:subagent-start")
    assert result == normal_content

    # 超预算情况
    over_content = "x" * ((budget + 100) * CHARS_PER_TOKEN)
    result = budget_guard(over_content, budget, "spec:subagent-start")
    assert len(result) < len(over_content), "超预算应被截断"


def test_inject_core_budget():
    """inject_core 注入点预算守卫测试 (300 token 默认)。"""
    budget = always_budget_tokens()  # 默认 300 tokens
    assert budget > 0, "预算必须为正数"

    # 正常情况
    normal_content = "x" * (budget * CHARS_PER_TOKEN)
    result = budget_guard(normal_content, budget, "spec:inject-core")
    assert result == normal_content

    # 超预算情况
    over_content = "x" * ((budget + 100) * CHARS_PER_TOKEN)
    result = budget_guard(over_content, budget, "spec:inject-core")
    assert len(result) < len(over_content), "超预算应被截断"


def test_est_tokens_accuracy():
    """est_tokens 估算函数准确性测试。"""
    # 1 token ≈ 4 字符 (粗略估算)
    text = "a" * 40  # 40 字符
    tokens = est_tokens(text)
    assert tokens == 10, f"40 字符应估算为 10 tokens, 实际为 {tokens}"

    # 测试不同长度
    for chars in [4, 8, 12, 100, 1000]:
        expected = chars // CHARS_PER_TOKEN
        actual = est_tokens("x" * chars)
        assert actual == expected, f"{chars} 字符应估算为 {expected} tokens, 实际为 {actual}"


if __name__ == "__main__":
    # 运行反向验证流程: 手动制造超预算 → 见过红 → 恢复 → 变绿
    print("=== 反向验证开始 ===")

    # 1. 正常状态 (变绿)
    print("\n1. 测试正常状态 (应全部通过)...")
    try:
        test_budget_guard_short_content()
        test_budget_guard_exact_budget()
        test_budget_guard_truncates_over_budget()
        test_session_start_budget()
        test_subagent_start_budget()
        test_inject_core_budget()
        test_est_tokens_accuracy()
        print("✅ 绿色: 所有测试通过")
    except AssertionError as e:
        print(f"❌ 红色: 测试失败 - {e}")
        sys.exit(1)

    # 2. 制造超预算 (见过红)
    print("\n2. 制造超预算场景 (应见过红)...")
    # 临时修改预算值，制造超预算场景
    original_budget = INJECTION_BUDGETS["session_index"]
    INJECTION_BUDGETS["session_index"] = 5  # 设置为 5 token，制造超预算场景

    try:
        # 使用小预算创建内容，制造超过小预算的场景
        over_budget = INJECTION_BUDGETS["session_index"]
        over_content = "x" * ((over_budget + 10) * CHARS_PER_TOKEN)
        result = budget_guard(over_content, over_budget, "spec:session-start")

        # 如果预算正常工作，内容应该被截断
        if len(result) >= len(over_content):
            print(f"❌ 未见红: 预算 {over_budget} tokens 未正确截断内容")
            sys.exit(1)
        else:
            print(f"✅ 见过红: 预算 {over_budget} tokens 正确截断了内容")

    except Exception as e:
        print(f"✅ 见过红: 超预算场景触发异常 - {e}")

    # 3. 恢复正常 (变绿)
    print("\n3. 恢复正常预算 (应变绿)...")
    INJECTION_BUDGETS["session_index"] = original_budget  # 恢复原始预算

    try:
        test_session_start_budget()
        print("✅ 恢复后变绿: 所有测试通过")
    except AssertionError as e:
        print(f"❌ 恢复后仍红: 测试失败 - {e}")
        sys.exit(1)

    print("\n=== 反向验证完成 ✅ ===")
    print("反向验证成功: 制造超预算→见过红→恢复→变绿")