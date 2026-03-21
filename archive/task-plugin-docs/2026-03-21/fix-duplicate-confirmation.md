# 修复重复确认问题（已完成 - 全自动化方案）

## 问题描述

用户报告：在使用 `@plugins/tools/task` 插件时，迭代过程中会不断询问用户是否继续，希望除了计划部分外的所有流程都是自动的。

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

## 修复方案（已实施）

### 设计思路

采用全自动化方案，只在计划确认阶段需要用户交互，其他所有阶段都自动化：

| 阶段 | 是否需要用户确认 | 说明 |
|------|----------------|------|
| 计划确认 | ✓ 需要确认 | 用户审核执行计划 |
| 任务执行 | ✗ 自动执行 | 自动执行所有任务 |
| 结果验证 - passed | ✗ 自动完成 | 直接完成任务 |
| 结果验证 - suggestions | ✗ 自动继续优化 | 自动进入下一轮迭代 |
| 失败调整 | ✗ 自动调整 | 按策略自动调整（retry/debug/replan） |

### 实现细节

#### 1. 验证流程自动化（flows/verify.md）

移除了验证阶段的所有用户询问：

```python
# 之前：passed状态时询问是否继续优化
# 现在：直接完成
if status == "passed" and quality_passed:
    return "completed"

# 之前：suggestions状态时询问是否继续
# 现在：自动继续优化
elif status == "suggestions":
    print(f"检测到优化建议，自动继续下一轮迭代...")
    for s in verification_result['suggestions']:
        print(f"  - {s['suggestion']}")
    return "continue"
```

#### 2. 详细流程自动化（detailed-flow.md）

更新验证阶段逻辑，移除用户询问：

```python
if status == "passed":
    goto("全部完成")

elif status == "suggestions":
    # 自动继续优化
    print(f"检测到优化建议，自动继续下一轮迭代...")
    context["replan_trigger"] = "verifier"
    goto("计划设计")
```

#### 3. 文档更新

- `verifier-output-passed-suggestions.md`: 更新 suggestions 状态说明为"自动继续"
- `deep-iteration/implementation.md`: 移除最小迭代次数检查和用户询问
- `deep-iteration-core.md`: 更新持续改进说明
- `README.md`: 更新流程说明

## 验证场景

### 场景1：标准流程（一次通过）

```
Loop 启动 → 生成计划 → ✓ 用户确认 → 执行 → 验证passed → 自动完成
```

### 场景2：优化建议场景

```
Loop 启动 → 生成计划 → ✓ 用户确认 → 执行 → 验证suggestions → 自动继续优化 → 生成新计划 → ✓ 用户确认 → 执行...
```

### 场景3：执行失败自动重试

```
执行 → 验证failed → Adjuster选择retry → 自动重新执行
```

### 场景4：执行失败自动重新规划

```
执行 → 验证failed → Adjuster选择replan → 生成新计划 → ✓ 用户确认 → 执行
```

### 场景5：用户主动重新设计

```
生成计划 → 用户选择"重新设计" → 生成新计划 → ✓ 用户确认 → 执行
```

## 影响分析

### 改动文件

1. `plugins/tools/task/skills/loop/flows/verify.md`：验证流程自动化
2. `plugins/tools/task/skills/loop/detailed-flow.md`：验证阶段自动化
3. `plugins/tools/task/skills/verifier/verifier-output-passed-suggestions.md`：文档更新
4. `plugins/tools/task/skills/deep-iteration/implementation.md`：深度迭代逻辑更新
5. `plugins/tools/task/skills/deep-iteration/deep-iteration-core.md`：核心机制更新
6. `plugins/tools/task/README.md`：流程说明更新

### 向后兼容性

⚠️ 行为变更（改进）：
- 验证阶段不再询问用户，全自动化
- suggestions 状态自动触发下一轮迭代
- 移除了最小迭代次数的用户确认
- 计划确认阶段保持不变（仍需用户确认）

### 用户体验提升

- **全自动化迭代**：只在计划阶段需要确认，其他全自动
- **更高效的优化流程**：发现优化点后自动继续，无需等待用户确认
- **保持控制权**：计划阶段仍需用户审核，确保执行方向正确

## 测试建议

### 单元测试

```python
def test_verification_passed_auto_complete():
    """验证passed状态自动完成"""
    result = {"status": "passed", "quality_score": 85}
    next_state = handle_verification(result)
    assert next_state == "completed"
    # 不应调用 AskUserQuestion

def test_verification_suggestions_auto_continue():
    """验证suggestions状态自动继续"""
    result = {
        "status": "suggestions",
        "suggestions": [{"suggestion": "优化性能"}]
    }
    next_state = handle_verification(result)
    assert next_state == "continue"
    # 不应调用 AskUserQuestion

def test_verification_failed_adjustment():
    """验证failed状态进入调整"""
    result = {"status": "failed"}
    next_state = handle_verification(result)
    assert next_state == "adjustment"
```

### 集成测试

1. **测试自动完成流程**：
   - 启动 loop → 确认计划 → 执行 → 验证passed
   - 验证：自动完成，无额外用户询问

2. **测试自动优化流程**：
   - 启动 loop → 确认计划 → 执行 → 验证suggestions
   - 验证：自动生成新计划并再次确认，无中间询问

3. **测试失败重试流程**：
   - 启动 loop → 确认计划 → 执行失败 → adjuster选择retry
   - 验证：自动重新执行，无用户询问

## 发布说明

### 用户可见变更

**重大改进**：全自动化迭代流程
- 迭代过程中不再询问用户是否继续优化
- 验证通过后自动完成任务
- 发现优化建议后自动触发下一轮迭代
- 执行失败后按策略自动调整（retry/debug/replan）
- **唯一需要用户交互的时机**：计划确认阶段（审核执行计划）

### 升级指南

无需任何操作，自动生效。建议在使用时：
- 仔细审核计划阶段生成的执行计划
- 确保验收标准准确定义了任务完成的条件
- 相信系统会自动处理迭代优化流程

## 相关文档

- [loop 详细流程](../skills/loop/detailed-flow.md)
- [计划设计流程](../skills/loop/flows/plan.md)
- [Adjuster 策略](../skills/adjuster/adjuster-strategies.md)
