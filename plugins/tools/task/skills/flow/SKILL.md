---
description: 任务流程，协调任务在各状态间的流转和调度
memory: project
color: purple
model: sonnet
permissionMode: bypassPermissions
background: false
disable-model-invocation: true
argument-hint: [任务描述]
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
adjust_result = None

# CRITICAL: 验证并生成中文task_id
if not task_id or not contains_chinese(task_id):
	task_id = generate_task_id(user_prompt)
	# 要求：中文、≤10字符、准确无歧义
	# 示例：修复登录Bug、优化查询性能、添加单元测试

def update_status(status):
	exec(f"CLAUDE_PROJECT_DIR=\"$(pwd)\" uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py task update {task_id} --status={status}")

# 状态机主循环
state = "align"

while state != "done":

	if state == "align":
		update_status("align")
		align_result = Skill(
			skill="task:align",
			environment={
				"task_id": task_id,
				"context_file": f".lazygophers/tasks/{task_id}/context.json",
				"adjust_result": adjust_result
			}
		)
		if align_result.get("need_explore"):
			state = "explore"
		else:
			state = "plan"

	elif state == "explore":
		update_status("explore")
		Agent(
			description="探索项目上下文",
			subagent_type="task:explore",
			prompt=f"{user_prompt}",
			mode="bypassPermissions",
			environment={
				"task_id": task_id,
				"align_feedback": align_result.get("feedback"),
				"adjust_result": adjust_result
			}
		)
		state = "align"

	elif state == "plan":
		update_status("plan")
		plan_result = Agent(
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
		if plan_result.get("status") == "上下文缺失":
			state = "explore"
		else:
			state = "exec"

	elif state == "exec":
		update_status("exec")
		Skill(
			skill="task:exec",
			environment={
				"task_id": task_id,
				"context_file": f".lazygophers/tasks/{task_id}/context.json",
				"task_file": f".lazygophers/tasks/{task_id}/task.json"
			}
		)
		state = "verify"

	elif state == "verify":
		update_status("verify")
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
		if verify_result.get("status"):
			state = "done"
		else:
			state = "adjust"

	elif state == "adjust":
		update_status("adjust")
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
		# 根据调整结果路由到对应状态
		status = adjust_result.get("status", "plan")
		if status == "上下文缺失":
			state = "explore"
		elif status == "需求偏差":
			state = "align"
		elif status == "重新计划":
			state = "plan"
		elif status == "放弃":
			state = "done"
		else:
			state = "plan"

# 完成：清理任务
Skill(skill="task:done", environment={"task_id": task_id})
exec(f"CLAUDE_PROJECT_DIR=\"$(pwd)\" uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py task clean {task_id} --force")
```

## 用户新输入

> 用户有新的会中断语义的输入时触发

```python
from claude import Skill

# 清理当前任务
if task_id:
	Skill(
		skill="task:done",
		environment={
			"task_id": task_id,
		}
	)
```

## 状态转换规则

| 从 | 到 | 条件 |
|---|---|------|
| pending | align | 任务创建 |
| align | explore | 上下文缺失 |
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
