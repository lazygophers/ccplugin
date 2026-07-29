---
title: harness-tool-responsibility
layer: recall
category: planning
keywords: [harness,工具,task,TaskCreate,责任,职责,finisher,agent,文档,内置工具,main,分工,hook,删除]
status: active
---

## harness 工具责任边界 (skein-drop-builtin-task-tools 后续约束)

### 触发场景

- skein-finisher 重新定义职责边界后，future task 需要重新分配「悬挂后台 agent 清理」职责
- skein 文档（agent.md/SKILL.md/references）需要描述能力要求或约束
- 检讨 skein 与 harness 之间的工具使用边界
- 已删除 TaskCreate 拦截 hook，skein 从此不干预 harness task 创建

### 陷阱-正解

**陷阱 1**：skein-finisher 的 finish 收尾中包含「清掉本 task 悬挂的后台 agent」这个逻辑，导致职责混淆（finisher 作为 sub-agent 看不到同级 agent）。

**正解**：「清悬挂后台 agent」职责归 main 不归 sub-agent——后台 agent 由 main 派出，main 掌握全景，main 在派 skein-finisher 前需清理完毕；skein-finisher 仅负责 skein 侧的闭环检查（subtask 全 done、验收完成等）。

---

**陷阱 2**：skein 侧文档（agent.md、SKILL.md、references）描述能力要求时具名「使用 TaskList 检查」「调用 TaskStop 清理」等 harness 内置工具。

**正解**：skein 侧文档只写「要达成什么状态」（如"清掉所有后台 agent"），不具名任何 harness 内置工具。手段（用哪个工具达成）交给 main 的 harness，harness 换工具名时 skein 文档不用改。

---

**陷阱 3**：删除 TaskCreate 拦截 hook 后，仍假设 hook 对「走 flow 决策」有拦截兜底作用。

**正解**：TaskCreate hook 已删除，skein 从此不干预 harness 建 task。该 hook 原本兼作「走 flow 的机械兜底」，删后该兜底消失——现在仅靠 hook prompt 的文案判定（@discipline.md hook 判定防自降级护栏）维持约束，无脚本拦截。这是已知的强制力削弱，用户明示接受。

### 反例表

| 禁 | 改为 |
|---|---|
| skein-finisher 定义「使用 TaskList 检查后台 agent」logic | skein-finisher 文档说「main 负责清理悬挂的后台 agent」，finisher 仅检查 subtask 完成度 |
| 文档写「调用 TaskStop 清理」或「使用 TaskCreate 验证」 | 文档写「清理完成」或「后台 agent 全退出」，工具选择交给 main 的 harness |
| 假设 TaskCreate 拦截 hook 作为「走 flow」的兜底 | 仅依赖 hook prompt 文案约束，hook 有强制力删弱是已知约束 |
| TaskCreate 拦截删除后仍在 hooks.py/plugin.json/docs 中留残留记载 | 同步清 TaskCreated 钩子、cmd_task_created、DISPATCH 中 task-created 键、模块 docstring、_CTX 上方注释中相关句 |

### 案例

- **职责转移**：task `skein-drop-builtin-task-tools` 的目标第 7 条 — skein-finisher 不再持有 TaskList/TaskStop，改由 main 在派 finisher 前承担清理职责
- **文档改写**：skein-flow SKILL.md finish 阶段 / skein-finisher.md 中的「清悬挂后台 agent」改为标记 main 职责且不具名工具
- **Hook 删除**：plugins/tools/skein/scripts/hooks.py 中删除 cmd_task_created 函数；plugin.json 删除 TaskCreated 钩子块；docs 中 hook 表去行
- **Commit**：`035fa1546 skein(skein-drop-builtin-task-tools): 移除 skein 插件对 harness 内置 task 工具的用法与拦截`

### 规则（关键约束）

- MUST：skein-finisher 工具白名单仅含 `Read, Bash, Grep, Glob`，不含任何 harness 内置 task 工具
- MUST：skein 侧文档描述约束时只写目标状态（如"确保后台 agent 全退出"），禁具名 TaskCreate/TaskList/TaskStop/TaskUpdate/TaskGet/TaskOutput/TodoWrite
- MUST：TaskCreate 拦截删除后，hooks.py/plugin.json/docs 中相关记载全部清干净，禁留悬空引用
- MUST：finish 前清掉本 task 悬挂的后台 agent 这项要求不丢失，改由 main 在派 finisher 前承担；验证职责在 skein-checker 或 main 确认

### 关联

- 铁律: hook 判定防自降级护栏 (@recall/planning/discipline.md) — TaskCreate 删除后，走 flow 判定完全交 AI 读 _CTX
- 铁律: flow 文档禁假设分工下沉 (@recall/flow/载体分工同步.md) — 职责转移需同步 flow/agent.md/references 三处
- 铁律: skein 工作流连线 (@recall/planning/workflow.md) — finish 阶段的闭环判据中，后台 agent 清理职责已转移
- 铁律: sub-agent 工具白名单 + 禁 Task/Agent (@recall/skill/agent.md) — 工具限制的一致性
- 代码证据: plugins/tools/skein/agents/skein-finisher.md:4 工具白名单 / skein-flow/references/for-finish.md 职责描述
- 背景: task skein-drop-builtin-task-tools PRD (目标 ①②⑨ 和边界约束)
