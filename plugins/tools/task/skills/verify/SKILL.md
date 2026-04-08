---
description: 结果校验，验证执行结果是否符合预期
memory: project
color: cyan
model: haiku
permissionMode: plan
background: false
disable-model-invocation: true
user-invocable: false
context: fork
agent: task:verify
---

# Verify Skill

## 执行流程

> 对照验收标准逐一检查，与用户交互确认
> **任何未通过的验收点都要无限制重试直到通过**

```python
# 读取验收标准和执行结果
align_file = f".lazygophers/tasks/{task_id}/align.json"
align = read_json(align_file)
criteria = align["acceptance_criteria"]

# 读取执行结果
task_file = f".lazygophers/tasks/{task_id}/task.json"
exec_result = read_json(task_file)

# 无限制重试循环：直到所有验收点通过
while True:
    # === 迭代开始 ===
    
    all_passed = True
    failed_items = []
    
    # 阶段1：功能验收
    functional_criteria = criteria.get("functional", [])
    for item in functional_criteria:
        check_result = verify_functional_item(item, exec_result)
        if not check_result["passed"]:
            all_passed = False
            failed_items.append({
                "category": "功能",
                "item": item,
                "reason": check_result["reason"]
            })
    
    # 如果功能验收失败，立即重试
    if not all_passed:
        fix_response = AskUserQuestion(
            questions=[{
                "question": f"功能验收未通过：\\n\\n{format_failures(failed_items)}\\n\\n请确认如何处理",
                "header": "功能验收失败",
                "options": [
                    {"label": "立即修复", "description": "现在修复这些功能点"},
                    {"label": "调整标准", "description": "验收标准不合理，需要调整"},
                    {"label": "重新执行", "description": "执行有误，需要重新执行"}
                ],
                "multiSelect": False
            }]
        )
        
        # 根据用户选择处理
        if fix_response["功能验收失败"] == "立即修复":
            # 触发修复，然后重试
            fix_failed_items(failed_items)
            continue  # ← 重新开始循环
        elif fix_response["功能验收失败"] == "调整标准":
            # 收集新标准，更新 align.json，然后重试
            new_criteria = collect_new_criteria(failed_items)
            update_align_criteria(new_criteria)
            continue  # ← 重新开始循环
        else:  # 重新执行
            # 重新执行任务，然后重试
            reexecute_task()
            continue  # ← 重新开始循环
    
    # 阶段2：质量标准
    quality_criteria = criteria.get("quality", {})
    quality_check = verify_quality(quality_criteria, exec_result)
    if not quality_check["passed"]:
        quality_response = AskUserQuestion(
            questions=[{
                "question": f"质量标准未通过：\\n\\n{format_quality_failures(quality_check)}\\n\\n请确认如何处理",
                "header": "质量验收失败",
                "options": [
                    {"label": "改进代码", "description": "现在改进代码质量"},
                    {"label": "调整标准", "description": "质量标准不合理，需要调整"},
                    {"label": "接受当前质量", "description": "当前质量可接受"}
                ],
                "multiSelect": False
            }]
        )
        
        if quality_response["质量验收失败"] == "改进代码":
            improve_code_quality(quality_check["failures"])
            continue  # ← 重新开始循环
        elif quality_response["质量验收失败"] == "调整标准":
            new_quality_criteria = collect_quality_adjustment()
            update_align_quality_criteria(new_quality_criteria)
            continue  # ← 重新开始循环
        # 接受当前质量，继续下一步
    
    # 阶段3：边界条件
    boundary_criteria = criteria.get("constraints", [])
    boundary_check = verify_boundaries(boundary_criteria, exec_result)
    if not boundary_check["passed"]:
        boundary_response = AskUserQuestion(
            questions=[{
                "question": f"边界条件未通过：\\n\\n{format_boundary_failures(boundary_check)}\\n\\n请确认如何处理",
                "header": "边界验收失败",
                "options": [
                    {"label": "修复问题", "description": "现在修复边界问题"},
                    {"label": "调整约束", "description": "约束条件不合理，需要调整"},
                    {"label": "接受边界", "description": "当前边界情况可接受"}
                ],
                "multiSelect": False
            }]
        )
        
        if boundary_response["边界验收失败"] == "修复问题":
            fix_boundary_issues(boundary_check["failures"])
            continue  # ← 重新开始循环
        elif boundary_response["边界验收失败"] == "调整约束":
            new_constraints = collect_constraint_adjustment()
            update_align_constraints(new_constraints)
            continue  # ← 重新开始循环
        # 接受当前边界，继续下一步
    
    # 阶段4：最终确认
    final_response = AskUserQuestion(
        questions=[{
            "question": f"所有验收点已通过：\\n\\n{summarize_verification()}\\n\\n请确认验收结果",
            "header": "最终验收确认",
            "options": [
                {"label": "验收通过", "description": "所有标准符合，任务完成"},
                {"label": "仍有问题", "description": "还有未解决的问题"}
            ],
            "multiSelect": False
        }]
    )
    
    # 如果用户选择"仍有问题"，继续重试
    if final_response["最终验收确认"] == "仍有问题":
        remaining_issues = AskUserQuestion(
            questions=[{
                "question": "请说明剩余问题",
                "header": "剩余问题",
                "options": [
                    {"label": "功能问题", "description": "功能仍有缺陷"},
                    {"label": "质量问题", "description": "代码质量不足"},
                    {"label": "其他问题", "description": "其他类型问题"}
                ],
                "multiSelect": True
            }]
        )
        # 处理剩余问题，然后重试
        handle_remaining_issues(remaining_issues)
        continue  # ← 重新开始循环
    
    # === 用户明确确认"验收通过" ===
    # 退出循环，返回通过
    quality_score = calculate_quality_score(exec_result, criteria)
    
    # 输出格式：所有输出必须包含前缀 [flow·{task_id}·{state}]
    print(f"[flow·{task_id}·verify] 验收通过，质量分：{quality_score}")
    
    return {
        "status": True,
        "quality_score": quality_score
    }
```

## 执行逻辑

```python
# 核心原则：任何验收失败都触发无限制重试
# 每次重试都会：
# 1. 向用户展示失败详情
# 2. 通过 AskUserQuestion 询问处理方式
# 3. 根据用户选择修复/调整/重新执行
# 4. 重新验收
# 5. 循环直到所有验收通过

# 重试触发条件：
# - 功能验收失败 → 立即修复/调整标准/重新执行 → continue
# - 质量验收失败 → 改进代码/调整标准/接受 → continue
# - 边界验收失败 → 修复问题/调整约束/接受 → continue
# - 最终确认："仍有问题" → 收集问题 → continue

# 唯一退出条件：
# - 所有验收点通过
# - 最终确认选择"验收通过"
```

## 检查清单

### 验收检查
- [ ] 功能验收已对照
- [ ] 质量标准已检查
- [ ] 边界条件已验证

### 用户交互（核心）
- [ ] 已实现无限制重试机制
- [ ] 每个 AskUserQuestion 都有重试路径
- [ ] 验收失败立即触发重试

### 循环控制
- [ ] while True 循环直到验收通过
- [ ] 每次重试都根据用户选择处理

### 输出
- [ ] status: True (验收通过)
- [ ] quality_score: 0-100

## 输出格式

所有输出必须包含前缀：`[flow·{task_id}·{state}]`

- task_id：当前任务ID
- state：当前状态（verify）
