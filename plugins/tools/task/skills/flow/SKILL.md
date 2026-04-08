from click import command---
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

对任务的计划、执行、监控进行管理

## 执行流程(严格遵守、禁止偏离)

> 新任务时触发
> 用户有新的会中断语义的任务触发

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
Skills(
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
```

## 用户主动取消

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
