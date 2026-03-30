<!-- STATIC_CONTENT: Phase 4流程文档，可缓存 -->

# Phase 4: Planning & Confirmation

## 目标

MECE任务分解 | DAG依赖建模 | Agents/Skills分配 | 用户确认

## 智能路径选择

| 场景 | iteration | replan_trigger | 流程 |
|------|-----------|----------------|------|
| 首次规划 | 1 | None | task:planner + 用户确认 |
| 用户重新设计 | >1 | "user" | task:planner + 用户确认 |
| Adjuster重规划 | >1 | "adjuster" | task:planner + (auto_approve ? 自动批准 : 用户确认) |
| Verifier建议优化 | >1 | "verifier" | task:planner + (auto_approve ? 自动批准 : 用户确认) |

## 上下文传递规范

调用 task:planner skill 时必须显式传递以下6个上下文字段：

| 字段 | 说明 | 来源 |
|------|------|------|
| project_path | 项目根目录绝对路径 | context.project_path |
| task_id | 任务唯一标识（Phase 1生成） | context.task_id |
| iteration | 当前迭代轮次 | iteration变量 |
| plan_md_path | 计划文件绝对路径（首次为null） | context.plan_md_path |
| working_directory | 工作目录 | context.working_directory |
| user_task | 用户原始任务描述 | user_task变量 |

## 路径A：重规划（auto_approve 控制审批方式）

1. iteration++ → 调用 task:planner skill，传入必传上下文：
   - project_path: ${context.project_path}
   - task_id: ${context.task_id}
   - iteration: ${iteration}
   - plan_md_path: ${context.plan_md_path}（首次为null）
   - working_directory: ${context.working_directory}
   - user_task: ${user_task}
   - 附加：任务目标+迭代编号+标准7项要求
2. 处理questions(有则AskUserQuestion) → tasks为空则goto完成
3. 生成计划文档：mkdir .claude/plans → 命名{中文关键词}-{iteration}.md（过滤特殊字符 / \ : * ? " < > |）
4. ⚠️ 连续执行（同一消息中）：调用 task:plan-formatter skill 写入文件 → if auto_approve: 自动批准 → save_checkpoint → goto任务执行；else: **立即** AskUserQuestion 请求用户批准（按下方批准判定规则处理）

## 路径B：用户确认

1. 可选：深度研究(should_trigger_deep_research)
2. 调用 task:planner skill，传入必传上下文：
   - project_path: ${context.project_path}
   - task_id: ${context.task_id}
   - iteration: ${iteration}
   - plan_md_path: ${context.plan_md_path}（首次为null）
   - working_directory: ${context.working_directory}
   - user_task: ${user_task}
   - 附加：user_feedback（如有）
3. 处理questions → tasks为空则goto完成
4. ⚠️ 连续执行（同一消息中）：调用 task:plan-formatter skill 写入文件 → **立即** AskUserQuestion 展示计划摘要，请求用户批准（按下方批准判定规则处理）

## 批准判定规则（强制）

AskUserQuestion 返回后，**必须严格按以下规则判定用户意图**：

| 用户响应 | 判定 | 处理 |
|---------|------|------|
| 选择"批准执行"选项 | **批准** | save_checkpoint → goto任务执行 |
| 选择"Other"并输入文本 | **修改意见** | 提取Other文本为 `user_feedback` → `replan_trigger="user"` → goto计划设计 |
| 选择其他非批准选项 | **拒绝/修改意见** | 提取选项描述为 `user_feedback` → `replan_trigger="user"` → goto计划设计 |

**关键规则**：**只有用户明确选择"批准执行"选项才视为批准。所有其他响应（包括Other文本输入）都必须视为修改意见，触发重新规划并再次请求用户确认。绝对禁止将非批准响应当作批准处理。**

## 状态转换

- 路径A → 自动批准 → Phase 5(任务执行)
- 路径B：用户批准 → Phase 5 | 拒绝 → Phase 4(重新设计) | 无需执行 → Phase 8

<!-- /STATIC_CONTENT -->
