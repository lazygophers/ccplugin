# 修复重复确认问题

## 问题描述

用户报告：在使用 `@plugins/tools/task` 插件时，已经确认过执行计划后，在执行过程中还会多次弹出"执行计划已准备就绪，是否开始执行？"的确认提示。

## 根本原因

### 问题场景

1. **首次确认**：用户启动 loop → 生成计划 → `flows/plan.md` 阶段4确认 ✓
2. **重复确认**：执行失败 → adjuster 选择 "replan" → 回到"计划设计" → 再次执行 `flows/plan.md` → 又弹出阶段4确认 ✗

### 代码层面

`flows/plan.md` 的阶段4（计划确认）没有区分不同的规划场景：

```python
# 原始代码 - 无条件确认
user_decision = AskUserQuestion(
    question="执行计划已准备就绪，是否开始执行？",
    options=["立即执行", "重新设计"]
)
```

当 adjuster 触发 replan 时：

```python
# detailed-flow.md:469
elif strategy == "replan":
    goto("计划设计")  # 直接跳回，导致重复确认
```

## 修复方案

### 设计思路

引入 `context["replan_trigger"]` 状态变量，区分三种规划场景：

| 场景 | `iteration` | `replan_trigger` | 是否确认 |
|------|-------------|------------------|---------|
| 首次规划 | 1 | None | ✓ 需要确认 |
| 用户主动重新设计 | >1 | "user" | ✓ 需要确认 |
| Adjuster 自动重新规划 | >1 | "adjuster" | ✗ 跳过确认 |
| Verifier 建议优化（用户同意） | >1 | "verifier" | ✗ 跳过确认 |

### 实现细节

#### 1. 初始化阶段（detailed-flow.md:13-24）

```python
context = {
    "replan_trigger": None  # 跟踪重新规划的触发来源
}
```

#### 2. 计划确认阶段（flows/plan.md:174-202）

```python
# 【智能跳过】检查是否需要用户确认
replan_trigger = context.get("replan_trigger", None)

# 跳过确认的场景
if iteration > 1 and replan_trigger in ["adjuster", "verifier"]:
    print(f"\n✓ 自动重新规划（触发来源：{replan_trigger}），跳过用户确认")
    print(f"  原因：已在{'调整阶段' if replan_trigger == 'adjuster' else '验证阶段'}告知用户")
    print(f"[MindFlow·{user_task}·计划确认/{iteration}·auto_approved]")
    return "execute"  # 直接执行，跳过确认
```

#### 3. 用户选择处理（flows/plan.md:234-241）

```python
if user_decision == "重新设计":
    # 用户主动选择重新设计，下次规划仍需确认
    context["replan_trigger"] = "user"
    return "replan"
else:
    # 用户批准执行，清除 replan_trigger 标志
    context["replan_trigger"] = None
    return "execute"
```

#### 4. Adjuster 触发重新规划（detailed-flow.md:469-471）

```python
elif strategy == "replan":
    # 标记为 adjuster 触发的重新规划，跳过用户确认
    context["replan_trigger"] = "adjuster"
    goto("计划设计")
```

#### 5. Verifier 触发重新规划（detailed-flow.md:340-343）

```python
if user_response.strip().lower() in ["是", "yes", "y"]:
    # 标记为 verifier 触发的重新规划，跳过用户确认
    context["replan_trigger"] = "verifier"
    goto("计划设计")
```

#### 6. 用户主动选择重新规划（detailed-flow.md:437-440）

```python
elif user_guidance == "重新规划":
    # 标记为用户主动触发的重新规划，需要重新确认
    context["replan_trigger"] = "user"
    goto("计划设计")
```

## 验证场景

### 场景1：首次规划

```
Loop 启动 → 生成计划 → ✓ 用户确认（首次）→ 执行
```

### 场景2：Adjuster 自动重新规划

```
执行失败 → Adjuster 分析 → 选择 replan → 生成新计划 → ✗ 跳过确认（已在调整阶段告知）→ 执行
```

### 场景3：Verifier 建议优化

```
验证完成 → Verifier 提出优化建议 → 用户同意优化 → 生成新计划 → ✗ 跳过确认（已同意优化）→ 执行
```

### 场景4：用户主动重新设计

```
首次确认 → 用户选择"重新设计" → 生成新计划 → ✓ 用户确认（主动要求）→ 执行
```

### 场景5：用户在调整阶段选择重新规划

```
Adjuster 建议被拒绝 → 用户选择"重新规划" → 生成新计划 → ✓ 用户确认（主动要求）→ 执行
```

## 影响分析

### 改动文件

1. `plugins/tools/task/skills/loop/flows/plan.md`：计划确认逻辑
2. `plugins/tools/task/skills/loop/detailed-flow.md`：状态管理和跳转逻辑

### 向后兼容性

✓ 完全向后兼容：
- 首次规划行为不变（仍需确认）
- 仅优化了重复确认的场景（减少不必要的用户交互）
- 不影响现有功能和 API

### 用户体验提升

- **减少重复确认**：从每次重新规划都确认 → 仅必要时确认
- **保持透明度**：跳过确认时仍显示原因和风险摘要
- **尊重用户意图**：用户主动重新设计时仍需确认

## 测试建议

### 单元测试

```python
def test_replan_trigger_adjuster():
    context = {"replan_trigger": "adjuster"}
    iteration = 2
    assert should_skip_confirmation(iteration, context) == True

def test_replan_trigger_user():
    context = {"replan_trigger": "user"}
    iteration = 2
    assert should_skip_confirmation(iteration, context) == False

def test_first_iteration():
    context = {"replan_trigger": None}
    iteration = 1
    assert should_skip_confirmation(iteration, context) == False
```

### 集成测试

1. **测试自动重新规划不确认**：
   - 启动 loop → 确认计划 → 模拟执行失败 → adjuster 选择 replan
   - 验证：不弹出第二次确认

2. **测试用户重新设计需要确认**：
   - 启动 loop → 第一次确认选择"重新设计" → 生成新计划
   - 验证：弹出第二次确认

3. **测试 verifier 优化不确认**：
   - 启动 loop → 确认计划 → 执行成功 → verifier 提出优化 → 用户同意
   - 验证：不弹出第二次确认

## 发布说明

### 用户可见变更

**优化**：减少重复确认提示
- 当系统自动重新规划（由 adjuster 或 verifier 触发）时，不再弹出确认对话框
- 仍会显示重新规划的原因和风险摘要，保持透明度
- 用户主动选择重新设计时，仍需确认新计划

### 升级指南

无需任何操作，自动生效。

## 相关文档

- [loop 详细流程](../skills/loop/detailed-flow.md)
- [计划设计流程](../skills/loop/flows/plan.md)
- [Adjuster 策略](../skills/adjuster/adjuster-strategies.md)
