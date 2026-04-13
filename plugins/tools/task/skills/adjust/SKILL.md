---
description: 失败调整。分析验收失败根因，通过 AskUserQuestion 让用户选择调整策略（补充上下文/重新对齐/重新规划/放弃）
memory: project
color: yellow
model: sonnet
permissionMode: bypassPermissions
background: false
user-invocable: false
effort: high
context: fork
agent: task:adjust
---

# Adjust Skill

## 执行流程

> 分析校验失败原因，制定修正策略
> **1 次交互确认调整方向，所有修复必须遵循项目现有风格**
> **停滞检测：相同错误 3 次或 A→B→A→B 振荡 → 立即 ask_user**

```python
# 读取校验结果和上下文
verify_result = environment["verify_result"]
align_file = f".lazygophers/tasks/{task_id}/align.json"
context_file = f".lazygophers/tasks/{task_id}/context.json"
align = read_json(align_file)
context = read_json(context_file)

# 获取锁定的项目风格
code_style = align.get("code_style_follow", {})

# 读取任务文件（如果存在）
task_file = f".lazygophers/tasks/{task_id}/task.json"
existing_plan = read_json(task_file) if exists(task_file) else None

# 无限制重试循环：直到用户确认调整方向
while True:
    # 阶段1：分析失败原因
    root_cause = analyze_failure({
        "verify_result": verify_result,
        "failed_criteria": verify_result.get("failed_criteria", []),
        "existing_plan": existing_plan,
        "code_style": code_style
    })

    # 阶段2：分类失败类型
    failure_type = classify_failure({
        "root_cause": root_cause,
        "context": context
    })

    # 阶段2.5：自动修复判定 — 可自动验证的失败类型直接重试，不问用户
    auto_fixable = is_auto_fixable(failure_type, verify_result)
    if auto_fixable and auto_fix_attempts < 2:
        auto_fix_attempts += 1
        # test-failure: 重新执行失败的子任务
        # style-violation: 运行格式化工具后重新验证
        return {
            "status": "重新计划",
            "reason": f"自动修复（第{auto_fix_attempts}次）：{root_cause}",
            "auto_fix": True
        }

    # 阶段3：一次性展示分析结果并请求用户选择策略
    response = AskUserQuestion(
        questions=[{
            "question": f"失败分析：\n\n{format_failure_analysis(root_cause, failure_type)}\n\n{'（已尝试自动修复 '+str(auto_fix_attempts)+' 次仍失败）' if auto_fix_attempts > 0 else ''}所有修复将遵循项目现有风格。请选择调整策略：",
            "header": f"[flow·{task_id}·adjust] 失败分析与调整策略",
            "options": [
                {"label": "补充上下文", "description": "对项目理解不足，返回探索"},
                {"label": "重新对齐", "description": "需求理解有偏差，返回对齐"},
                {"label": "重新规划", "description": "执行计划有问题，重新规划"},
                {"label": "重新分析", "description": "分析有误，重新审视失败原因"},
                {"label": "放弃任务", "description": "无法完成，停止执行"}
            ],
            "multiSelect": False
        }]
    )

    choice = response["失败分析与调整策略"]

    # 重新分析 → 继续循环
    if choice == "重新分析":
        continue

    # 映射用户选择到 status
    status_map = {
        "补充上下文": "上下文缺失",
        "重新对齐": "需求偏差",
        "重新规划": "重新计划",
        "放弃任务": "放弃"
    }

    return {
        "status": status_map[choice],
        "reason": root_cause
    }
```

## 自动修复判定

```python
def is_auto_fixable(failure_type, verify_result):
    """判断失败是否可自动修复（不需要用户介入）"""
    auto_fixable_types = {
        "test-failure",      # 测试失败 → 重新执行失败子任务
        "style-violation",   # 风格违规 → 运行格式化工具
    }
    
    # 必须同时满足：
    # 1. 失败类型在可自动修复列表中
    # 2. 失败标准都有明确的验证命令（非主观判断）
    # 3. 不涉及 scope-creep 或 missing-context（这类需要人工判断）
    if failure_type not in auto_fixable_types:
        return False
    
    for criteria in verify_result.get("failed_criteria", []):
        if criteria.get("category") in ("安全", "完整"):
            return False  # 安全和完整性问题不自动修复
    
    return True
```

> **自动修复上限**：最多 2 次自动重试。超过后必须 AskUserQuestion，防止无限循环。

## 失败类型与策略

| 类型 | 特征 | 可自动修复 | 策略 |
|------|------|-----------|------|
| test-failure | 测试未通过、断言失败 | ✅（≤2次） | 重新执行失败子任务 |
| style-violation | lint 错误、命名不一致 | ✅（≤2次） | 运行格式化工具后重验 |
| scope-creep | 修改了计划外文件 | ❌ | 需求偏差 → align |
| missing-context | 引用不存在的函数/模块 | ❌ | 上下文缺失 → explore |
| integration-issue | 接口不匹配、类型不兼容 | ❌ | 重新计划 → plan |

## 检查清单

### 失败分析
- [ ] 根本原因已分析
- [ ] 失败类型已分类
- [ ] 风格符合性已检查

### 用户交互
- [ ] 1 次 AskUserQuestion 展示分析 + 选择策略
- [ ] 无限制重试循环（"重新分析"可循环）
- [ ] 所有修复遵循项目现有风格

### 输出
- [ ] status: 上下文缺失 | 需求偏差 | 重新计划 | 放弃
- [ ] reason: 失败原因

## 失败模式模板

预定义的常见失败模式和修复策略见 [strategies.json](strategies.json)，包含 test-failure / style-violation / scope-creep / missing-context / integration-issue 五种模式。分析失败原因时优先匹配已知模式。

