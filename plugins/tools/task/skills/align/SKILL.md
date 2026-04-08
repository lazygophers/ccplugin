---
description: 范围对齐，确认任务边界和验收标准
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

> 与用户交互式确认任务范围，输出结构化对齐结果
> **必须锁定项目风格，验收标准遵循 SMART-V 原则**

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
        corrected_style = collect_correct_style(correction["风格修正"])
        context["code_style"] = merge_code_style(code_style, corrected_style)
        write_json(context_file, context)
        continue
    
    # 风格确认后，锁定为后续使用的标准
    locked_style = context["code_style"]
    
    # === 阶段1：明确目标（Deliverable）===
    goal_response = AskUserQuestion(
        questions=[{
            "question": f"任务目标是否清晰？\\n\\n{build_goal_description(context, previous_feedback)}\\n\\n目标应该明确最终产出。",
            "header": "目标确认",
            "options": [
                {"label": "确认继续", "description": "目标清晰"},
                {"label": "需要澄清", "description": "目标不够明确"}
            ],
            "multiSelect": False
        }]
    )
    
    if goal_response["目标确认"] == "需要澄清":
        clarification = AskUserQuestion(
            questions=[{
                "question": "请说明期望的最终产出",
                "header": "目标澄清",
                "options": [
                    {"label": "描述功能", "description": "说明要实现的功能"},
                    {"label": "描述结果", "description": "说明最终达到的状态"},
                    {"label": "描述用户价值", "description": "说明为用户解决什么问题"}
                ],
                "multiSelect": False
            }]
        )
        previous_feedback = clarification
        continue
    
    # === 阶段2：确认验收标准（遵循 SMART-V 原则）===
    criteria_response = AskUserQuestion(
        questions=[{
            "question": f"验收标准是否完整？\\n\\n{build_criteria_checklist(context)}\\n\\n要求：可验证、可量化、独立、原子、结果导向。",
            "header": "验收标准",
            "options": [
                {"label": "确认继续", "description": "标准完整"},
                {"label": "需要补充", "description": "需要添加或修改标准"}
            ],
            "multiSelect": False
        }]
    )
    
    if criteria_response["验收标准"] == "需要补充":
        supplement = AskUserQuestion(
            questions=[{
                "question": "请说明需要补充的验收标准",
                "header": "补充标准",
                "options": [
                    {"label": "添加功能点", "description": "增加功能验收（可验证）"},
                    {"label": "添加性能要求", "description": "增加性能指标（可量化）"},
                    {"label": "添加质量标准", "description": "遵循现有风格的代码质量"}
                ],
                "multiSelect": True
            }]
        )
        previous_feedback = supplement
        continue
    
    # === 阶段3：界定边界（Guardrails）===
    boundary_response = AskUserQuestion(
        questions=[{
            "question": f"边界界定是否正确？\\n\\n{format_boundaries(context)}\\n\\nin-scope：本次要做的事\\nout-of-scope：明确不做的事",
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
                    {"label": "扩大 in-scope", "description": "允许做更多事"},
                    {"label": "缩小 in-scope", "description": "限制本次范围"},
                    {"label": "添加 out-of-scope", "description": "明确禁止事项"}
                ],
                "multiSelect": True
            }]
        )
        previous_feedback = boundary_adjustment
        continue
    
    # === 阶段4：最终确认 ===
    final_response = AskUserQuestion(
        questions=[{
            "question": f"请最终确认任务规格说明：\\n\\n{preview_spec()}\\n\\n核心：验收标准决定迭代是否继续，项目风格锁定后续实现。\\n\\n确认后写入 prompt.md。",
            "header": "最终确认",
            "options": [
                {"label": "确认无误", "description": "规格正确，写入文件"},
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
    # 生成对齐结果
    alignment = {
        "goal": build_goal_description(context, previous_feedback),
        "acceptance_criteria": build_criteria_list(context),
        "boundaries": {
            "in_scope": build_in_scope(context),
            "out_of_scope": build_out_of_scope(context)
        },
        "code_style_follow": locked_style,
        "confirmed_at": now()
    }
    
    # 写入 align.json
    align_file = f".lazygophers/tasks/{task_id}/align.json"
    write_json(align_file, alignment)
    
    # 输出格式：所有输出必须包含前缀 [flow·{task_id}·{state}]
    print(f"[flow·{task_id}·align] 范围对齐已完成")
    
    return alignment
```

## 验收标准设计原则（SMART-V）

| 原则 | 好的标准 | 差的标准 |
|------|---------|---------|
| **可验证** | "用户可通过邮箱+密码登录" | "实现登录功能" |
| **可量化** | "测试覆盖率≥80%" | "覆盖率高" |
| **独立** | 每条标准可独立验证 | 多个条件混在一句话 |
| **原子** | "API 返回 200 + 正确 JSON" | "API 工作正常" |
| **结果导向** | "用户看到成功提示" | "调用了 toast 组件" |

## align.json 输出格式

```json
{
    "goal": "明确的目标描述，说明最终产出",
    "acceptance_criteria": [
        "用户可通过邮箱+密码登录",
        "登录响应时间 < 500ms",
        "登录失败显示错误提示",
        "JWT token 有效期 7 天"
    ],
    "boundaries": {
        "in_scope": [
            "登录功能实现",
            "JWT token 生成",
            "错误处理"
        ],
        "out_of_scope": [
            "注册功能",
            "密码重置",
            "第三方登录"
        ]
    },
    "code_style_follow": {
        "naming": "snake_case",
        "indent": "4_spaces",
        "imports": "sorted"
    },
    "confirmed_at": "2026-04-08T12:00:00Z"
}
```

## 项目风格检查清单

### 风格检测（阶段0，最先执行）
- [ ] 已从 context.json 读取现有风格
- [ ] 命名约定已展示
- [ ] 缩进风格已展示
- [ ] 导入模式已展示
- [ ] 用户已确认风格正确
- [ ] 风格锁定为后续标准

### 验收标准（阶段2）
- [ ] 每条标准可验证
- [ ] 每条标准可量化
- [ ] 每条标准独立
- [ ] 每条标准原子
- [ ] 每条标准结果导向

### 边界界定（阶段3）
- [ ] in-scope 已明确
- [ ] out-of-scope 已明确
- [ ] 两者互斥且完备

### 输出
- [ ] align.json 已写入
- [ ] goal 字段包含明确目标
- [ ] acceptance_criteria 数组遵循 SMART-V 原则
- [ ] boundaries 包含 in_scope 和 out_of_scope
- [ ] code_style_follow 字段包含锁定的项目风格

## 输出格式

所有输出必须包含前缀：`[flow·{task_id}·{state}]`

- task_id：当前任务ID
- state：当前状态（align）
