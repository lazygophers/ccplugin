<!-- STATIC_CONTENT: Phase 4流程文档，可缓存 -->

# Phase 4: Planning & Confirmation

## 目标

MECE任务分解 | DAG依赖建模 | Agents/Skills分配 | 用户确认

## 核心设计：单次 Skill() 调用完成整个阶段

**planner 内部完成所有工作**：设计计划 → 写入文件 → 用户确认（或自动批准）→ 返回最终结果。Loop 只需一次 `Skill(skill="task:planner")` 调用，无需链式调用其他工具。

## 上下文传递规范

调用 task:planner skill 时必须显式传递以下字段：

| 字段 | 说明 | 来源 |
|------|------|------|
| project_path | 项目根目录绝对路径 | context.project_path |
| task_id | 任务唯一标识（Phase 1生成） | context.task_id |
| iteration | 当前迭代轮次 | iteration变量 |
| plan_md_path | 计划文件绝对路径（首次为null） | context.plan_md_path |
| working_directory | 工作目录 | context.working_directory |
| user_task | 用户原始任务描述 | user_task变量 |
| auto_approve | 是否自动批准 | 见下方路径选择 |
| user_feedback | 用户修改意见（如有） | 上一轮用户反馈 |

## 路径选择（由 loop 通过 auto_approve 参数控制）

| 场景 | auto_approve | planner 行为 |
|------|-------------|-------------|
| 首次规划 (iteration=1) | false | 设计 → 写文件 → AskUserQuestion → 返回 |
| 用户重新设计 (replan_trigger="user") | false | 设计 → 写文件 → AskUserQuestion → 返回 |
| Adjuster重规划 | true/false | 设计 → 写文件 → (auto_approve ? 自动返回 : AskUserQuestion) |
| Verifier建议优化 | true/false | 设计 → 写文件 → (auto_approve ? 自动返回 : AskUserQuestion) |

## Planner 返回值处理

planner 返回 JSON，loop 根据 `status` 字段处理：

| status | 含义 | loop 处理 |
|--------|------|----------|
| `confirmed` | 用户批准或自动批准 | 提取 plan_md_path → save_checkpoint → goto Phase 5 |
| `rejected` | 用户要求修改 | 提取 user_feedback → replan_trigger="user" → goto Phase 4 |
| `no_tasks` | 无需执行任何任务 | goto Phase 8 |
| `cancelled` | 用户取消任务 | goto Phase 8 |

## 批准判定规则（planner 内部执行）

planner 调用 AskUserQuestion 后，按以下规则判定用户意图：

| 用户响应 | 判定 | planner 返回 |
|---------|------|-------------|
| 选择"批准执行"选项 | **批准** | `{status: "confirmed", plan_md_path: "..."}` |
| 选择"Other"并输入文本 | **修改意见** | `{status: "rejected", user_feedback: "..."}` |
| 选择其他非批准选项 | **拒绝/修改** | `{status: "rejected", user_feedback: "..."}` |
| 选择"取消任务" | **取消** | `{status: "cancelled"}` |

**关键规则**：只有用户明确选择"批准执行"选项才视为批准。所有其他响应都视为修改意见。

## 强制状态转换

**每个状态转换必须立即在同一回复中执行，禁止在本阶段后结束回复：**

| status | 下一阶段 | 强制要求 |
|--------|---------|---------|
| confirmed | Phase 5(任务执行) | **必须立即**继续执行，不允许停止 |
| rejected | Phase 4(重新设计) | **必须立即**带 user_feedback 重新调用 planner |
| no_tasks | Phase 8(完成) | **必须立即**进入 Finalizer 清理 |
| cancelled | Phase 8(完成) | **必须立即**进入 Finalizer 清理 |

**禁止**：处理完 planner 返回结果后就结束回复。Loop 流程不可中断，必须继续到 Finalizer。

<!-- /STATIC_CONTENT -->
