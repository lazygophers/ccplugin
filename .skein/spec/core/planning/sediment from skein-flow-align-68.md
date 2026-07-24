---
title: skein 工作流连线（create → plan → confirm(就绪) → start → exec → check → finish）
layer: core
category: planning
keywords: [workflow,连线,阶段,确认,confirm,就绪,ready,start,自动,状态转移]
source: sediment from skein-flow-align
authored-by: skein-spec
created: 1784822958
status: active
related: []
updated: 1784910100
---

## 铁律

- MUST：skein 工作流必须明确连线：create(待处理) → plan → `skein confirm`(用户确认门→就绪) → `skein start`(占槽→进行中) → exec → `skein check`(→检查中) → finish(→已完成)
- MUST：plan 阶段完成后需**明确的用户确认门 `skein confirm <id>`**（验 prd + ≥1 subtask）将 task 从**待处理→就绪**；确认是独立阶段/独立状态，不隐含在 start 内
- MUST：**就绪**是独立状态（规划完成待启动，**不占 max_active 槽**）；只有**就绪** task 可 `skein start`，待处理(规划中) 必须先 confirm 过门
- MUST：`skein start` 仅验 deps + 空槽（prd/subtask 已在 confirm 校验），start 后 task→进行中并进入 exec（无需额外用户操作）
- MUST：各阶段职责明确，阶段间状态转移在脚本中硬编码（非隐式推断）

## 反例表
| 禁 | 改为 |
|---|---|
| plan 直接自动 start | plan 完成后须先 `skein confirm` 过用户门(→就绪) 再 start |
| 待处理 task 直接 start | 仅就绪 task 可 start；待处理须先 confirm |
| 确认门隐含在 start 内 | confirm 是独立命令/独立状态(待处理→就绪)，与 start 分离 |
| 就绪/检查中 占 max_active 槽 | 仅进行中占槽；就绪/检查中不占 |
| 阶段转移隐式进行 | 阶段转移在代码中明确处理 |

## 触发场景
- task 工作流设计
- skein flow 图与执行逻辑对齐
- UI/CLI 交互设计

## 关联
- 铁律: plan 阶段完成判据门
- 铁律: task 状态流转规则
- 实现细节: skein-flow.mmd 流程图
