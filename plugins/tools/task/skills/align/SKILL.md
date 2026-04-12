---
description: 范围对齐，确认任务边界和验收标准
memory: project
color: blue
model: sonnet
permissionMode: bypassPermissions
background: false
context: fork
user-invocable: false
effort: high
---

# Align Skill

## 执行流程

> 自动生成对齐结果，总是需要用户确认
> **锁定项目风格，验收标准遵循 SMART-V 原则，使用语义化 name**

```python
# 检查上下文文件是否存在且完整
context_file = f".lazygophers/tasks/{task_id}/context.json"

# 如果上下文文件不存在，标记需要探索
if not exists(context_file):
	return {
		"need_explore": True,
		"feedback": "上下文文件不存在，需要探索项目现状"
	}

# 读取探索结果
context = read_json(context_file)

# 验证上下文完整性
if not context or not context.get("task_related") or not context.get("code_style"):
	return {
		"need_explore": True,
		"feedback": "上下文不完整，缺少关键字段（task_related 或 code_style）"
	}

# 检查是否已有对齐结果
align_file = f".lazygophers/tasks/{task_id}/align.json"
existing_align = read_json(align_file) if exists(align_file) else None

# 如果是从 adjust 返回，加载之前的反馈
previous_feedback = adjust_result.get("reason") if adjust_result else None

# === 阶段1：锁定项目风格 ===
code_style = context.get("code_style", {})
# 自动使用探索阶段检测的风格，无需确认（除非明显错误）
locked_style = code_style

# === 阶段2：自动生成任务目标 ===
task_goal = extract_goal_from(user_prompt, context, previous_feedback)

# === 阶段3：自动生成验收标准（SMART-V 原则）===
# AI 根据 user_prompt 和 context 自主生成合理的验收标准
# 每个标准必须包含：name（语义化）、description、SMART-V 属性
acceptance_criteria = generate_criteria_from_context(user_prompt, context, previous_feedback)

# === 阶段4：自动界定边界 ===
boundary = {
	"in_scope": extract_scope_from(user_prompt, context),
	"out_of_scope": ["新功能添加（除非明确要求）", "架构重构", "性能优化（除非必要）", "文档更新（除非明确要求）"]
}

# === 阶段5：构建对齐结果 ===
align_result = {
	"task_id": task_id,
	"task_goal": task_goal,
	"acceptance_criteria": acceptance_criteria,
	"boundary": boundary,
	"code_style_follow": locked_style
}

# === 阶段6：确认对齐结果 ===
# align 总是需要用户确认对齐结果
final_response = AskUserQuestion(
	questions=[{
		"question": f"对齐结果：\\n\\n目标：{task_goal}\\n\\n验收标准：\\n{format_criteria(acceptance_criteria)}\\n\\n边界：\\n{format_boundary(boundary)}\\n\\n项目风格：\\n{format_code_style(locked_style)}\\n\\n确认此对齐结果？",
		"header": f"[flow·{task_id}·align] 范围对齐确认",
		"options": [
			{"label": "确认继续", "description": "对齐结果正确，开始规划"},
			{"label": "需要调整", "description": "需要修改对齐结果"}
		],
		"multiSelect": False
	}]
)

if final_response["范围对齐确认"] == "需要调整":
	adjustment = AskUserQuestion(
		questions=[{
			"question": "请说明需要调整的部分",
			"header": f"[flow·{task_id}·align] 调整说明",
			"options": [
				{"label": "目标不准确", "description": "任务目标理解有误"},
				{"label": "标准不合理", "description": "验收标准需要调整"},
				{"label": "边界不清晰", "description": "范围界定需要明确"},
				{"label": "风格检测错误", "description": "项目风格识别有误"}
			],
			"multiSelect": True
		}]
	)

	# 根据用户反馈调整，返回需要重新探索
	return {
		"need_explore": True,
		"feedback": f"用户反馈需要调整：{adjustment['调整说明']}"
	}

# === 写入对齐结果 ===
write_json(align_file, align_result)

return align_result
```

## SMART-V 原则

每个验收标准必须满足：
- **Specific**: 具体明确，不模糊
- **Measurable**: 可量化或可明确验证
- **Achievable**: 可实现，不超出能力范围
- **Relevant**: 与任务目标相关
- **Time-bound**: 有明确的完成定义
- **Verifiable**: 可通过客观证据验证

## 验收标准生成指南

AI 应根据具体任务自主生成 3-5 个验收标准，每个标准必须：

**结构要求**：
- `name`: 语义化名称（如 functionality, style_compliant, no_regression）
- `description`: 清晰的验收描述
- SMART-V 属性：verifiable, measurable, achievable, relevant, result_oriented（至少包含一个）

**常见标准示例**（仅供参考，不强制使用）：
- 功能正确性：functionality, correctness, bug_resolved
- 代码质量：style_compliant, readability, maintainability
- 安全性：no_regression, no_new_risk, vulnerability_fixed
- 性能：performance_improved, complexity_controlled
- 完整性：error_handling, coverage, boundary_cases

## 确认策略

**总是需要确认** — align 阶段必须与用户确认对齐结果，无例外

## 检查清单

### 对齐输出
- [ ] task_goal: 清晰的任务目标
- [ ] acceptance_criteria: 符合 SMART-V 的验收标准（使用语义化 name）
- [ ] boundary: in_scope 和 out_of_scope
- [ ] code_style_follow: 锁定的项目风格

### 确认策略
- [ ] 总是需要用户确认，无例外
- [ ] 确认内容一次性展示所有结果
- [ ] 支持调整反馈

## 任务模板

预定义的常见任务类型模板见 [template.json](template.json)，包含 bug-fix / new-feature / refactor / add-tests / security-fix 五种类型的预设验收标准和边界。当用户任务匹配已知模板时，优先使用模板作为初始值。

## 输出格式

所有输出必须包含前缀：`[flow·{task_id}·{state}]`

- task_id：当前任务ID
- state：当前状态（align）
