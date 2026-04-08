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
> **必须确认现有项目风格，后续所有实现都遵循此风格**

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
    
    # === 阶段0：确认现有项目风格（最重要）===
    code_style = context.get("code_style", {})
    style_response = AskUserQuestion(
        questions=[{
            "question": f"已检测到项目现有风格：\\n\\n{format_code_style(code_style)}\\n\\n这是项目的实际风格吗？后续所有实现都将遵循此风格。",
            "header": "项目风格确认",
            "options": [
                {"label": "确认正确", "description": "风格检测正确，后续遵循"},
                {"label": "需要修正", "description": "风格检测有误，需要调整"}
            ],
            "multiSelect": False
        }]
    )
    
    # 如果风格检测有误，立即重试
    if style_response["项目风格确认"] == "需要修正":
        correction = AskUserQuestion(
            questions=[{
                "question": "请说明正确的风格配置",
                "header": "风格修正",
                "options": [
                    {"label": "命名风格", "description": "修正命名约定"},
                    {"label": "缩进风格", "description": "修正缩进方式"},
                    {"label": "导入风格", "description": "修正导入模式"},
                    {"label": "完整描述", "description": "手动描述所有风格"}
                ],
                "multiSelect": False
            }]
        )
        
        # 收集正确的风格
        corrected_style = collect_correct_style(correction["风格修正"])
        # 更新 context 中的风格
        context["code_style"] = merge_code_style(code_style, corrected_style)
        # 更新 context.json
        write_json(context_file, context)
        # 重新开始循环，再次确认
        continue
    
    # 风格确认后，锁定为后续使用的标准
    locked_style = context["code_style"]
    
    # 阶段1：确认任务范围（强调不创造新风格）
    scope_response = AskUserQuestion(
        questions=[{
            "question": f"任务范围是否正确？\\n\\n{current_understanding['scope']}\\n\\n注意：所有实现都将遵循已确认的项目风格，不创造新风格。",
            "header": "任务范围",
            "options": [
                {"label": "确认继续", "description": "范围正确"},
                {"label": "需要调整", "description": "需要修改范围"}
            ],
            "multiSelect": False
        }]
    )
    
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
        previous_feedback = adjustment["范围调整"]
        continue
    
    # 阶段2：明确验收标准
    acceptance_response = AskUserQuestion(
        questions=[{
            "question": f"验收标准是否完整？\\n\\n{current_understanding['acceptance']}\\n\\n注意：代码质量标准应遵循项目现有风格。",
            "header": "验收标准",
            "options": [
                {"label": "确认继续", "description": "标准完整"},
                {"label": "需要补充", "description": "需要添加或修改标准"}
            ],
            "multiSelect": False
        }]
    )
    
    if acceptance_response["验收标准"] == "需要补充":
        supplement = AskUserQuestion(
            questions=[{
                "question": "请说明需要补充的验收标准",
                "header": "补充标准",
                "options": [
                    {"label": "添加功能点", "description": "增加功能验收"},
                    {"label": "添加性能要求", "description": "增加性能指标"},
                    {"label": "添加代码质量", "description": "遵循现有风格的代码质量"}
                ],
                "multiSelect": True
            }]
        )
        previous_feedback = supplement
        continue
    
    # 阶段3：界定边界
    boundary_response = AskUserQuestion(
        questions=[{
            "question": f"边界界定是否正确？\\n\\n{current_understanding['boundaries']}\\n\\n注意：修改文件必须遵循项目现有风格。",
            "header": "边界界定",
            "options": [
                {"label": "确认继续", "description": "边界正确"},
                {"label": "需要调整", "description": "需要修改边界"}
            ],
            "multiSelect": False
        }]
    )
    
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
        previous_feedback = boundary_adjustment
        continue
    
    # 阶段4：最终确认
    final_response = AskUserQuestion(
        questions=[{
            "question": f"请最终确认任务理解：\\n\\n{summarize_all()}\\n\\n核心要求：后续所有实现都将遵循项目现有风格，不创造新风格。\\n\\n确认后进入规划阶段。",
            "header": "最终确认",
            "options": [
                {"label": "确认无误", "description": "理解正确，开始规划"},
                {"label": "需要修正", "description": "理解有误，需要调整"}
            ],
            "multiSelect": False
        }]
    )
    
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
        previous_feedback = correction
        continue
    
    # === 用户明确确认"确认无误" ===
    # 退出循环，保存结果
    alignment = {
        "scope": scope_response,
        "acceptance_criteria": acceptance_response,
        "boundaries": boundary_response,
        "code_style_follow": locked_style,  # 锁定的项目风格
        "confirmed_at": now()
    }
    write_json(align_file, alignment)
    return alignment
```

## 项目风格检查清单

### 风格检测（阶段0，最先执行）
- [ ] 已从 context.json 读取现有风格
- [ ] 命名约定已展示（camelCase/snake_case/PascalCase）
- [ ] 缩进风格已展示（空格/tab，2/4/8）
- [ ] 导入模式已展示（顺序/分组/别名）
- [ ] 错误处理已展示（异常类型/日志方式）
- [ ] 用户已确认风格正确
- [ ] 风格锁定为后续标准

### 风格修正（如果检测有误）
- [ ] 用户选择了需要修正
- [ ] 收集了正确的风格配置
- [ ] 更新了 context.json
- [ ] 重新确认直到正确

### 后续环节强化
- [ ] 任务范围确认时强调"遵循现有风格"
- [ ] 验收标准确认时强调"遵循现有风格"
- [ ] 边界界定确认时强调"遵循现有风格"
- [ ] 最终确认时强调"不创造新风格"

### 输出
- [ ] align.json 已写入
- [ ] **code_style_follow** 字段包含锁定的项目风格
- [ ] 后续所有阶段都必须读取并遵循此风格
