<!-- STATIC_CONTENT: Phase 4流程文档，可缓存 -->

# Phase 4: Planning & Confirmation

## 目标

MECE任务分解 | DAG依赖建模 | Agents/Skills分配 | 用户确认

## 智能路径选择

| 场景 | iteration | replan_trigger | 流程 |
|------|-----------|----------------|------|
| 首次规划 | 1 | None | task:planner + 用户确认 |
| 用户重新设计 | >1 | "user" | task:planner + 用户确认 |
| Adjuster重规划 | >1 | "adjuster" | 直接生成 + (auto_approve ? 自动批准 : 用户确认) |
| Verifier建议优化 | >1 | "verifier" | 直接生成 + (auto_approve ? 自动批准 : 用户确认) |

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
4. 调用 task:plan-formatter skill 写入文件(frontmatter+JSON→Markdown)
5. if auto_approve: 自动批准 → save_checkpoint → goto任务执行
   else: AskUserQuestion 请求用户批准 → 批准→goto任务执行 | 拒绝→replan_trigger="user"→goto计划设计

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
4. 调用 task:plan-formatter skill 写入文件
5. AskUserQuestion 展示计划摘要，请求用户批准：
   - 批准 → save_checkpoint → goto任务执行
   - 拒绝 → 提取用户反馈 → replan_trigger="user" → goto计划设计

## 状态转换

- 路径A → 自动批准 → Phase 5(任务执行)
- 路径B：用户批准 → Phase 5 | 拒绝 → Phase 4(重新设计) | 无需执行 → Phase 8

<!-- /STATIC_CONTENT -->
