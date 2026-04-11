---
description: 任务流程，协调任务在各状态间的流转和调度
memory: project
color: purple
model: sonnet
permissionMode: plan
background: false
---

# Flow Skill

对任务的计划、执行、监控进行管理。严格遵守状态转换规则，禁止偏离。

## 绝对规则

- **输出前缀**：所有输出必须包含 `[flow·{task_id}·{state}]`
- **禁止提前终止**：必须完成所有状态流转
- **禁止带问题完成**：存在未解决问题 = 失败

## 入口点

- **新任务** → pending
- **用户新输入** → align
- **用户取消** → cancel

## 执行流程

> 新任务时触发

```python
from claude import Agent, Skill, UserPrompt
user_prompt = UserPrompt()

verify_result = None
adjust_result = None

# CRITICAL: 验证并生成中文task_id
if not task_id or not contains_chinese(task_id):
	task_id = Agent(
		description="生成中文任务ID",
		prompt=f"{user_prompt}\n\n请生成一个符合以下要求的task_id：\n1. 必须是中文的\n2. 简短（≤10个字符）\n3. 准确描述任务内容\n4. 明确的，可以准确表达任务的，不会出现歧义的\n5. 只返回task_id本身，不要其他解释\n\n示例：修复登录Bug、优化查询性能、添加单元测试",
		model="haiku",
		mode="bypassPermissions",
		run_in_background=False
	)

EXPLORE:
exec(f"CLAUDE_PROJECT_DIR=\"${{CLAUDE_PROJECT_DIR:-$(pwd)}}\" uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py task update {task_id} --status=explore")
Agent(
	description="探索项目上下文",
	subagent_type="task:explore",
	prompt=f"{user_prompt}",
	mode="bypassPermissions",
	environment={
		"task_id": task_id,
		"adjust_result": adjust_result
	}
)

ALIGN:
exec(f"CLAUDE_PROJECT_DIR=\"${{CLAUDE_PROJECT_DIR:-$(pwd)}}\" uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py task update {task_id} --status=align")
Agent(
	description="对齐任务范围",
	subagent_type="task:align",
	prompt=f"{user_prompt}",
	mode="bypassPermissions",
	environment={
		"task_id": task_id,
		"context_file": f".lazygophers/tasks/{task_id}/context.json",
		"adjust_result": adjust_result
	}
)

PLAN:
exec(f"CLAUDE_PROJECT_DIR=\"${{CLAUDE_PROJECT_DIR:-$(pwd)}}\" uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py task update {task_id} --status=plan")
Agent(
	description="制定执行计划",
	subagent_type="task:plan",
	prompt=f"{user_prompt}",
	mode="bypassPermissions",
	environment={
		"task_id": task_id,
		"context_file": f".lazygophers/tasks/{task_id}/context.json",
		"task_align_file": f".lazygophers/tasks/{task_id}/align.json",
		"adjust_result": adjust_result
	}
)

exec(f"CLAUDE_PROJECT_DIR=\"${{CLAUDE_PROJECT_DIR:-$(pwd)}}\" uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py task update {task_id} --status=exec")
Skill(
	skill="task:exec",
	environment={
		"task_id": task_id,
		"context_file": f".lazygophers/tasks/{task_id}/context.json",
		"task_file": f".lazygophers/tasks/{task_id}/task.json"
	}
)

exec(f"CLAUDE_PROJECT_DIR=\"${{CLAUDE_PROJECT_DIR:-$(pwd)}}\" uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py task update {task_id} --status=verify")
verify_result = Agent(
	description="验证执行结果",
	subagent_type="task:verify",
	prompt=f"{user_prompt}",
	mode="bypassPermissions",
	environment={
		"task_id": task_id,
		"context_file": f".lazygophers/tasks/{task_id}/context.json",
		"task_align_file": f".lazygophers/tasks/{task_id}/align.json"
	}
)

switch verify_result.status:
case False:
	exec(f"CLAUDE_PROJECT_DIR=\"${{CLAUDE_PROJECT_DIR:-$(pwd)}}\" uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py task update {task_id} --status=adjust")
	adjust_result = Agent(
		description="分析失败原因并调整",
		subagent_type="task:adjust",
		prompt=f"{user_prompt}",
		mode="bypassPermissions",
		environment={
			"task_id": task_id,
			"verify_result": verify_result,
			"context_file": f".lazygophers/tasks/{task_id}/context.json",
			"task_align_file": f".lazygophers/tasks/{task_id}/align.json"
		}
	)

	switch adjust_result.status:
	case "上下文缺失":
		goto EXPLORE
	case "需求偏差", "进一步迭代优化":
		goto ALIGN
	case "重新计划":
		goto PLAN
	default:
		goto PLAN

case True:
	Agent(
		description="完成任务清理",
		subagent_type="task:done",
		mode="bypassPermissions",
		environment={
			"task_id": task_id,
		}
	)

exec(f"CLAUDE_PROJECT_DIR=\"${{CLAUDE_PROJECT_DIR:-$(pwd)}}\" uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py task clean {task_id} --force")
```

## 用户新输入

> 用户有新的会中断语义的输入时触发

```python
from claude import Agent

# 首次，生成任务Id
if task_id:
	Agent(
		description="用户中断，清理任务",
		subagent_type="task:done",
		mode="bypassPermissions",
		environment={
			"task_id": task_id,
		}
	)
```

## 状态转换规则

| 从 | 到 | 条件 |
|---|---|------|
| pending | explore | 触发探索 |
| explore | align | 探索完成 |
| align | plan | 对齐完成 |
| plan | exec | 规划确认 |
| plan | explore | 上下文缺失 |
| exec | verify | 执行完成 |
| verify | done | 校验通过 |
| verify | adjust | 校验失败 |
| adjust | explore | 上下文缺失 |
| adjust | align | 需求偏差 |
| adjust | plan | 重新计划 |
| adjust | done | 放弃 |
| cancel | done | 取消完成 |

## 输出格式

所有输出必须包含前缀：`[flow·{task_id}·{state}]`

- task_id：当前任务ID
- state：当前状态（flow）
