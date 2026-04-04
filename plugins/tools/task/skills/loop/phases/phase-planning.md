
# Planning: Planning & Confirmation

## 目标

MECE 任务分解 | DAG 依赖建模 | Agents/Skills 分配 | 用户确认

## 关联资源

| 类型 | 名称 | 说明 |
|------|------|------|
| Agent | `task:planner` | 计划设计代理 |
| Skill | `task:planner` | 计划设计规范（MECE 分解、DAG 建模、资源分配） |

## 调用 Agent

**单次调用完成整个阶段**：planner 内部完成设计 → 写文件 → 用户确认（或自动批准）→ 返回结果。

```
Agent(subagent_type="task:planner", prompt="
  project_path: {project_path}
  task_id: {task_id}
  iteration: {iteration}
  plan_md_path: .claude/tasks/{task_id}/plan.md
  working_directory: {working_directory}
  user_task: {user_task}
  auto_approve: {auto_approve}
  user_feedback: {user_feedback | null}")
```

### auto_approve 路径选择（由 loop 控制）

| 场景 | auto_approve | 说明 |
|------|-------------|------|
| 首次规划 (iteration=1) | false | 需要用户确认 |
| 用户重新设计 (replan_trigger="user") | false | 需要用户确认 |
| Adjuster 重规划 | true/false | 视情况决定 |
| Verifier 建议优化 | true/false | 视情况决定 |

Planner 内部完成：信息收集（三层上下文学习）→ 计划设计（MECE 分解）→ 写入 plan.md + tasks.json → 用户确认 → 写入 metadata.json result。详见 agent 定义。

## 结果处理

读取 metadata.json 的 `result` 字段：

| result.status | 含义 | loop 处理 |
|---------------|------|----------|
| `confirmed` | 用户批准或自动批准 | 设 plan_md_path → save_checkpoint → goto Execution |
| `rejected` | 用户要求修改 | 读取 result.user_feedback → goto PromptOptimization |
| `no_tasks` | 无需执行任何任务 | goto Cleanup |
| `cancelled` | 用户取消任务 | goto Cleanup |

## 强制状态转换

**每个状态转换必须立即在同一回复中执行，禁止在本阶段后结束回复：**

| status | 下一阶段 | 强制要求 |
|--------|---------|---------|
| confirmed | Execution（任务执行） | **必须立即**继续执行 |
| rejected | PromptOptimization（重新评估） | **必须立即**回到提示词评估 |
| no_tasks | Cleanup（完成） | **必须立即**进入清理 |
| cancelled | Cleanup（清理） | **必须立即**进入清理 |
