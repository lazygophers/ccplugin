---
description: 范围对齐，与用户确认任务边界和验收标准
memory: project
color: cyan
model: sonnet
permissionMode: plan
background: false
disable-model-invocation: true
user-invocable: false
context: fork
agent: task:align
---

# Align Skill

## 执行流程

> 通过 AskUserQuestion 与用户交互式确认任务范围
> **任何非明确确认都将触发重新调整，无限制重试直到用户确认**

```python
# 读取探索结果
context_file = f".lazygophers/tasks/{task_id}/context.json"
context = read_json(context_file)

# 检查是否已有对齐结果
align_file = f".lazygophers/tasks/{task_id}/align.json"
existing_align = read_json(align_file) if exists(align_file) else None

# 如果是从 adjust 返回，加载之前的反馈
previous_feedback = adjust_result.get("reason") if adjust_result else None

# 无限制重试循环：直到用户明确确认
while True:
    # === 迭代开始 ===
    
    # 展示当前理解（包含之前反馈的修正）
    current_understanding = build_understanding(context, previous_feedback)
    
    # 阶段1：确认任务范围
    scope_response = AskUserQuestion(
        questions=[{
            "question": f"任务范围是否正确？\\n\\n{current_understanding['scope']}\\n\\n如有调整请说明，否则确认继续。",
            "header": "任务范围",
            "options": [
                {"label": "确认继续", "description": "范围正确"},
                {"label": "需要调整", "description": "需要修改范围"}
            ],
            "multiSelect": False
        }]
    )
    
    # 如果用户选择"需要调整"，立即重试
    if scope_response["任务范围"] == "需要调整":
        adjustment = AskUserQuestion(
            questions=[{
                "question": "请说明如何调整任务范围",
                "header": "范围调整",
                "options": [
                    {"label": "缩小范围", "description": "减少功能"},
                    {"label": "扩大范围", "description": "增加功能"},
                    {"label": "重新定义", "description": "完全重新描述"}
                ],
                "multiSelect": False
            }]
        )
        # 更新理解，立即重试
        previous_feedback = adjustment["范围调整"]
        continue  # ← 重新开始循环
    
    # 阶段2：明确验收标准
    acceptance_response = AskUserQuestion(
        questions=[{
            "question": f"验收标准是否完整？\\n\\n{current_understanding['acceptance']}\\n\\n需补充请说明，否则确认继续。",
            "header": "验收标准",
            "options": [
                {"label": "确认继续", "description": "标准完整"},
                {"label": "需要补充", "description": "需要添加或修改标准"}
            ],
            "multiSelect": False
        }]
    )
    
    # 如果用户选择"需要补充"，立即重试
    if acceptance_response["验收标准"] == "需要补充":
        supplement = AskUserQuestion(
            questions=[{
                "question": "请说明需要补充的验收标准",
                "header": "补充标准",
                "options": [
                    {"label": "添加功能点", "description": "增加功能验收"},
                    {"label": "添加性能要求", "description": "增加性能指标"},
                    {"label": "添加其他标准", "description": "安全/质量等"}
                ],
                "multiSelect": True
            }]
        )
        # 更新理解，立即重试
        previous_feedback = supplement
        continue  # ← 重新开始循环
    
    # 阶段3：界定边界
    boundary_response = AskUserQuestion(
        questions=[{
            "question": f"边界界定是否正确？\\n\\n{current_understanding['boundaries']}\\n\\n需调整请说明，否则确认继续。",
            "header": "边界界定",
            "options": [
                {"label": "确认继续", "description": "边界正确"},
                {"label": "需要调整", "description": "需要修改边界"}
            ],
            "multiSelect": False
        }]
    )
    
    # 如果用户选择"需要调整"，立即重试
    if boundary_response["边界界定"] == "需要调整":
        boundary_adjustment = AskUserQuestion(
            questions=[{
                "question": "请说明如何调整边界",
                "header": "边界调整",
                "options": [
                    {"label": "扩大编辑范围", "description": "允许修改更多文件"},
                    {"label": "缩小编辑范围", "description": "限制修改范围"},
                    {"label": "添加禁止项", "description": "增加禁止操作"}
                ],
                "multiSelect": True
            }]
        )
        # 更新理解，立即重试
        previous_feedback = boundary_adjustment
        continue  # ← 重新开始循环
    
    # 阶段4：最终确认
    final_response = AskUserQuestion(
        questions=[{
            "question": f"请最终确认任务理解：\\n\\n{summarize_all()}\\n\\n确认后进入规划阶段。",
            "header": "最终确认",
            "options": [
                {"label": "确认无误", "description": "理解正确，开始规划"},
                {"label": "需要修正", "description": "理解有误，需要调整"}
            ],
            "multiSelect": False
        }]
    )
    
    # 如果用户选择"需要修正"，立即重试
    if final_response["最终确认"] == "需要修正":
        correction = AskUserQuestion(
            questions=[{
                "question": "请说明需要修正的内容",
                "header": "修正说明",
                "options": [
                    {"label": "重新理解需求", "description": "需求理解有误"},
                    {"label": "调整优先级", "description": "重新排序重要性"},
                    {"label": "其他修正", "description": "其他需要修正的地方"}
                ],
                "multiSelect": False
            }]
        )
        # 更新理解，立即重试
        previous_feedback = correction
        continue  # ← 重新开始循环
    
    # === 用户明确确认"确认无误" ===
    # 退出循环，保存结果
    alignment = build_alignment(scope_response, acceptance_response, boundary_response)
    write_json(align_file, alignment)
    return alignment
```

## 执行逻辑

```python
# 核心原则：任何非"确认继续"的响应都触发立即重试
# 每次重试都会：
# 1. 使用用户的新输入更新理解
# 2. 重新展示更新后的理解
# 3. 再次请求确认
# 4. 循环直到用户明确确认

# 重试触发条件：
# - 任务范围："需要调整" → 收集调整说明 → continue
# - 验收标准："需要补充" → 收集补充内容 → continue
# - 边界界定："需要调整" → 收集调整说明 → continue
# - 最终确认："需要修正" → 收集修正说明 → continue

# 唯一退出条件：
# - 所有环节都选择"确认继续"
# - 最终确认选择"确认无误"
```

## 检查清单

### 用户交互（核心）
- [ ] 已实现无限制重试机制
- [ ] 每个 AskUserQuestion 都有重试路径
- [ ] 非确认响应立即触发重试
- [ ] 重试时使用用户新输入更新理解

### 循环控制
- [ ] while True 循环直到明确确认
- [ ] 每次重试都更新 previous_feedback
- [ ] 只有"确认无误"才能退出循环

### 输出
- [ ] 用户确认后，align.json 已写入
- [ ] 包含：scope, acceptance_criteria, boundaries, code_style_follow
