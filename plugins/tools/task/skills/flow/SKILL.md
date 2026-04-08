---
description: 任务流程，协调任务在各状态间的流转和调度
memory: project
color: purple
model: opus
permissionMode: plan
background: false
disable-model-invocation: true
user-invocable: false
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

# 首次，生成任务Id
if task_id:
	task_id = Agent(
		model="haiku",
		memory="local",
		background=False,
		permissionMode="bypassPermissions",
		prompt=f"{user_prompt}",
		initialPrompt="根据用户描述，生成任务Id，要求\n1. 必须是中文的\n2. 必须简短，不能超过10个字符\n3. 必须确保可以准确的描述任务"
	)

	EXPLORE:
	exec(f"uv run -directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py task update {task_id} --status=explore")
	Agent(
		subagent_type="task:explore",
		background=False,
		permissionMode="bypassPermissions",
		prompt=f"{user_prompt}",
		environment={
			"task_id": task_id,
			"adjust_result": adjust_result
		}
	)

ALIGN:
exec(f"uv run -directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py task update {task_id} --status=align")
Agent(
	subagent_type="task:align",
	background=False,
	permissionMode="bypassPermissions",
	prompt=f"{user_prompt}",
	environment={
		"task_id": task_id,
		"context_file": f".lazygophers/tasks/{task_id}/context.json",
			"adjust_result": adjust_result
	}
)

PLAN:
exec(f"uv run -directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py task update {task_id} --status=plan")
Agent(
	subagent_type="task:plan",
	background=False,
	permissionMode="bypassPermissions",
	prompt=f"{user_prompt}",
	environment={
		"task_id": task_id,
		"context_file": f".lazygophers/tasks/{task_id}/context.json",
		"task_align_file": f".lazygophers/tasks/{task_id}/align.json",
			"adjust_result": adjust_result
	}
)

exec(f"uv run -directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py task update {task_id} --status=exec")
Skill(
	skill="task:exec",
	background=False,
	permissionMode="bypassPermissions",
	environment={
		"task_id": task_id,
		"context_file": f".lazygophers/tasks/{task_id}/context.json",
		"task_file": f".lazygophers/tasks/{task_id}/task.json"
	}
)

exec(f"uv run -directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py task update {task_id} --status=verify")
verify_result = Agent(
	subagent_type="task:verify",
	background=False,
	permissionMode="bypassPermissions",
	prompt=f"{user_prompt}",
	environment={
		"task_id": task_id,
		"context_file": f".lazygophers/tasks/{task_id}/context.json",
		"task_align_file": f".lazygophers/tasks/{task_id}/align.json"
	}
)

switch verify_result.status:
case False:
	exec(f"uv run -directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py task update {task_id} --status=adjust")
	adjust_result = Agent(
		subagent_type="task:adjust",
		background=False,
		permissionMode="bypassPermissions",
		prompt=f"{user_prompt}",
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
		subagent_type="task:done",
		background=False,
		permissionMode="bypassPermissions",
		environment={
			"task_id": task_id,
		}
	)

exec(f"uv run -directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py task clean {task_id} --force")
```

## 用户新输入

> 用户有新的会中断语义的输入时触发

```python
from claude import Agent

# 首次，生成任务Id
if task_id:
	Agent(
		subagent_type="task:done",
		background=False,
		permissionMode="bypassPermissions",
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
