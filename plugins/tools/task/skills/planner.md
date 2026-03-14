---
agent: task:planner
description: 计划设计规范 - 收集项目信息、任务分解、依赖建模、agents/skills 分配的执行规范
model: opus
context: fork
user-invocable: true
---

# Skills(task:planner) - 计划设计规范

## 适用场景

- Loop 命令步骤 1：计划设计（信息收集是计划设计的内置部分）
- 需要收集项目信息并理解需求
- 需要将任务分解为子任务
- 需要建立任务依赖关系
- 需要分配 Agent 和 Skills

## 执行流程

### 1. 调用 planner agent

```
planner_result = Agent(task:planner, prompt="执行 loop 步骤 1 的计划设计工作：
1. 深度分析代码结构，收集：目标、依赖、现状、边界
2. 将任务分解为原子子任务
3. 建立任务依赖关系
4. 为每个任务分配合适的 Agent 和 Skills
5. 返回简短精炼的执行报告（≤200字）

任务目标：$ARGUMENTS")
```

### 2. 处理结果

- 检查 `planner_result.status`
- 如果有 `questions`，通过 `AskUserQuestion` 向用户确认
- 检查计划是否合理
- 确认依赖关系无循环
- 确认资源分配合理

### 3. 输出执行计划

```
print(f"[MindFlow·{$ARGUMENTS}·步骤1/{iteration + 1}·running]")
print("计划设计完成：")
print(planner_result.report)
```

【阶段 2：计划设计】
1. 将任务分解为原子子任务
2. 建立任务依赖关系
3. 为每个任务分配合适的 Agent 和 Skills
4. 返回简短精炼的执行报告（≤300字）

任务目标：$ARGUMENTS")
```

### 2. 处理收集和计划结果

- 检查 `planner_result.status`
- 如果有 `questions`，通过 `AskUserQuestion` 向用户确认
- 检查计划是否合理
- 确认依赖关系无循环
- 确认资源分配合理

### 3. 输出执行计划

```
print(f"[MindFlow·{$ARGUMENTS}·步骤1-2/{iteration + 1}·running]")
print("信息收集与计划设计完成：")
print(planner_result.report)
```

## 输出格式

planner agent 返回格式（合并信息收集和计划设计）：

```json
{
	"status": "completed" | "questions",
	"report": "项目分析：Go 项目，使用 Gin 框架。计划：3个子任务。T1：JWT 工具（coder）→ T2：认证中间件（coder）→ T3：测试（tester）。依赖：T2→T3。",
	"gathered_info": {
		"goal": "添加用户认证功能",
		"dependencies": ["JWT 库", "密码加密库"],
		"current_state": "已有用户模型",
		"boundaries": "仅认证功能，不含权限管理",
		"tech_stack": ["Go", "Gin", "MySQL"]
	},
	"tasks": [
		{
			"id": "T1",
			"description": "实现 JWT 工具函数",
			"agent": "coder",
			"skills": ["golang:core"],
			"files": ["internal/auth/jwt.go"],
			"acceptance_criteria": ["生成和验证 Token 功能完整", "单元测试覆盖率 ≥ 90%"],
			"dependencies": []
		}
	],
	"dependencies": {
		"T2": ["T1"],
		"T3": ["T2"]
	},
	"parallel_groups": [["T1"], ["T2"], ["T3"]],
	"iteration_goal": "完成用户认证功能的实现和测试",
	"acceptance_criteria": ["所有子任务完成", "整体测试通过"],
	"questions": ["是否需要支持多种认证方式？"]
}
```

## 核心原则

- **MECE**：相互独立，完全穷尽
- **可交付原子化**：每个任务必须产生可验证的交付物
- **可量化可验证**：每个任务必须有明确的验收标准
- **依赖闭环**：任务之间的依赖关系必须形成闭环

## 避坑指南

- 禁止过度拆分：避免将简单任务拆得太细
- 权责模糊：每个任务的职责必须明确
- 完成标准模糊：每个任务的验收标准必须清晰

## 注意事项

- 执行报告必须简短精炼（≤300字）
- 使用 Agent(task:planner) 调用 planner agent
- 确认依赖关系无循环
- 确认资源分配合理
- 最多支持 2 个任务并行