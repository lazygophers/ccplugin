<!-- STATIC_CONTENT: Phase 4流程文档，可缓存 -->

# Phase 4: Planning & Confirmation

## 目标

MECE任务分解 | DAG依赖建模 | Agents/Skills分配 | 用户确认

## 智能路径选择

| 场景 | iteration | replan_trigger | 流程 |
|------|-----------|----------------|------|
| 首次规划 | 1 | None | task:planner + 用户确认 |
| 用户重新设计 | >1 | "user" | task:planner + 用户确认 |
| Adjuster重规划 | >1 | "adjuster" | 直接生成+自动批准 |
| Verifier建议优化 | >1 | "verifier" | 直接生成+自动批准 |

## 路径A：自动重规划

1. iteration++ → 调用 task:planner(任务目标+迭代编号+标准7项要求)
2. 处理questions(有则AskUserQuestion) → tasks为空则goto完成
3. 生成计划文档：mkdir .claude/plans → 命名{safe_task_name}-{iteration}.md
4. 调用 task:plan-formatter 写入文件(frontmatter+JSON→Markdown)
5. 自动批准 → save_checkpoint → goto任务执行

## 路径B：用户确认

1. 可选：深度研究(should_trigger_deep_research)
2. 调用 task:planner(含user_feedback如有)
3. 处理questions → tasks为空则goto完成
4. 调用 task:plan-formatter 写入文件
5. AskUserQuestion 展示计划摘要，请求用户批准：
   - 批准 → save_checkpoint → goto任务执行
   - 拒绝 → 提取用户反馈 → replan_trigger="user" → goto计划设计

## 状态转换

- 路径A → 自动批准 → Phase 5(任务执行)
- 路径B：用户批准 → Phase 5 | 拒绝 → Phase 4(重新设计) | 无需执行 → Phase 8

<!-- /STATIC_CONTENT -->
