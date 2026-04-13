---
description: 任务范围对齐。自动生成目标、SMART-V 验收标准和边界，通过 AskUserQuestion 确认后写入 align.json
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

# === 快速上下文推断：用户 prompt 是否已包含足够信息 ===
# 当 prompt 明确指定了文件路径和修改内容时，可跳过 explore
if not exists(context_file) and is_prompt_self_contained(user_prompt):
	# 从 prompt 中直接提取上下文（不需要全局探索）
	context = infer_context_from_prompt(user_prompt)
	# 补充基本的 code_style（从指定文件中快速采样）
	if context.get("task_related", {}).get("files"):
		context["code_style"] = quick_style_sample(context["task_related"]["files"][:3])
	write_json(context_file, context)

# 如果上下文文件不存在，标记需要探索
elif not exists(context_file):
	return {
		"need_explore": True,
		"feedback": "上下文文件不存在，需要探索项目现状"
	}

# 读取探索结果
context = read_json(context_file) if exists(context_file) else context

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

# === 阶段2：识别任务类型并加载模板 ===
# 从 user_prompt 中识别任务类型，匹配 template.json 中的预定义模板
templates = read_json("template.json")["templates"]
task_type = classify_task_type(user_prompt, context)
# 分类规则：
#   "修复"/"fix"/"bug"/"报错"/"失败" → bug-fix
#   "添加"/"新增"/"实现"/"开发"/"功能" → new-feature
#   "重构"/"优化"/"整理"/"简化"    → refactor
#   "测试"/"test"/"覆盖"           → add-tests
#   "安全"/"漏洞"/"CVE"/"注入"     → security-fix
#   无法识别                        → None（不使用模板）
template = templates.get(task_type)

# === 阶段3：自动生成任务目标 ===
if template:
    # 有模板：以模板为基础，根据 user_prompt 细化
    task_goal = template["task_goal"].replace("$ARGUMENTS", user_prompt)
    acceptance_criteria = customize_criteria(template["acceptance_criteria"], user_prompt, context)
    boundary = customize_boundary(template["boundary"], user_prompt, context)
else:
    # 无模板：完全自主生成
    task_goal = extract_goal_from(user_prompt, context, previous_feedback)
    acceptance_criteria = generate_criteria_from_context(user_prompt, context, previous_feedback)
    boundary = {
        "in_scope": extract_scope_from(user_prompt, context),
        "out_of_scope": ["新功能添加（除非明确要求）", "架构重构", "性能优化（除非必要）", "文档更新（除非明确要求）"]
    }

# 验收标准必须满足 SMART-V 原则（无论是否使用模板）
# 每个标准必须包含：name（语义化）、description、SMART-V 属性

# === 阶段4.5：生成三层行为规约 ===
# 基于任务类型和上下文，生成 agent 执行时的行为约束
behavior_spec = {
	"always_do": [
		# 根据任务类型生成，示例：
		"修改代码后运行相关测试确认通过",
		"使用项目现有的错误处理模式",
		"遵循 code_style_follow 中锁定的风格"
	],
	"ask_first": [
		# 高风险但可能需要的操作
		"修改数据库 schema 或数据模型",
		"删除现有代码或文件"
	],
	"never_do": [
		# 硬止点：从 boundary.out_of_scope 自动派生
		*[f"执行: {item}" for item in boundary["out_of_scope"]],
		"提交包含 secrets/credentials 的代码",
		"跳过 lint/类型检查"
	]
}

# === 阶段5：构建对齐结果 ===
align_result = {
	"task_id": task_id,
	"task_goal": task_goal,
	"acceptance_criteria": acceptance_criteria,
	"boundary": boundary,
	"behavior_spec": behavior_spec,
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

预定义的常见任务类型模板见 [template.json](template.json)，包含 5 种类型：

| 类型 | 触发关键词 | 预设标准数 |
|------|-----------|-----------|
| bug-fix | 修复/fix/bug/报错/失败 | 3 |
| new-feature | 添加/新增/实现/开发/功能 | 4 |
| refactor | 重构/优化/整理/简化 | 3 |
| add-tests | 测试/test/覆盖 | 3 |
| security-fix | 安全/漏洞/CVE/注入 | 3 |

模板使用规则：
- 匹配到模板时，以模板的 acceptance_criteria 和 boundary 为初始值，根据具体任务细化
- 模板中的 `$ARGUMENTS` 替换为用户输入的任务描述
- 无论是否使用模板，最终标准都必须满足 SMART-V 原则

