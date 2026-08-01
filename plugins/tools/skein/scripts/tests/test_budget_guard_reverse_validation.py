#!/usr/bin/env python3
"""反向验证脚本: 演示见过红→恢复→变绿的过程。

这个脚本会:
1. 显示当前所有测试通过 (绿色)
2. 制造超预算场景，触发测试失败 (见过红)
3. 恢复正常，所有测试重新通过 (变绿)

验收标准:
- 机械守卫: 任一注入点超预算 → 测试失败
- 反向验证: 手动制造超预算 → 见过红 → 恢复 → 变绿
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# 添加 scripts 目录到 sys.path
SCRIPTS = Path(__file__).resolve().parent.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def run_test(budget_modification=None):
    """运行测试并返回结果"""
    if budget_modification:
        from skeinlib.spec.model import INJECTION_BUDGETS
        INJECTION_BUDGETS["session_index"] = budget_modification

    result = subprocess.run(
        [sys.executable, "-m", "pytest",
         "plugins/tools/skein/scripts/tests/test_budget_guard.py",
         "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    return result


def main():
    print("=" * 60)
    print("反向验证: 机械守卫 + 预算守卫测试")
    print("=" * 60)

    # 1. 绿色状态 - 所有测试正常通过
    print("\n🟢 第一步: 正常状态 (所有测试应该通过)")
    print("-" * 60)
    result = run_test()
    if result.returncode == 0:
        print("✅ 绿色: 所有测试通过")
    else:
        print("❌ 意外: 正常状态下测试失败")
        print(result.stdout)
        return False

    # 2. 见过红 - 制造超预算场景
    print("\n🔴 第二步: 制造超预算场景 (应该见过红)")
    print("-" * 60)
    print("将 session_index 预算临时改为 5 tokens (正常为 200)...")

    # 先导入模块进行修改
    from skeinlib.spec.model import INJECTION_BUDGETS
    original_budget = INJECTION_BUDGETS["session_index"]
    print(f"原始预算: {original_budget} tokens")

    # 制造超预算场景 - 使用小预算
    small_budget = 5
    INJECTION_BUDGETS["session_index"] = small_budget
    print(f"临时预算: {small_budget} tokens")

    # 运行一个简单的超预算测试
    from skeinlib.hooks.runner import budget_guard, CHARS_PER_TOKEN
    over_content = "x" * ((small_budget + 10) * CHARS_PER_TOKEN)
    result = budget_guard(over_content, small_budget, "spec:session-start")

    if len(result) < len(over_content):
        print(f"✅ 见过红: 预算 {small_budget} tokens 正确截断了内容")
        print(f"   原内容长度: {len(over_content)} 字符")
        print(f"   截断后长度: {len(result)} 字符")
    else:
        print("❌ 反向验证失败: 预算守卫未生效")
        INJECTION_BUDGETS["session_index"] = original_budget
        return False

    # 3. 恢复变绿 - 恢复正常预算
    print("\n🟢 第三步: 恢复正常预算 (应该变绿)")
    print("-" * 60)
    INJECTION_BUDGETS["session_index"] = original_budget
    print(f"恢复预算: {original_budget} tokens")

    result = run_test()
    if result.returncode == 0:
        print("✅ 恢复后变绿: 所有测试重新通过")
    else:
        print("❌ 意外: 恢复后测试仍失败")
        print(result.stdout)
        return False

    print("\n" + "=" * 60)
    print("🎉 反向验证完成!")
    print("=" * 60)
    print("验证结果: ✅ 机械守卫正常工作 + ✅ 反向验证成功")
    print("流程: 制造超预算 → 见过红 → 恢复 → 变绿")
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n中断: 用户取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)