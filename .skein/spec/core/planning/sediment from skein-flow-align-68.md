---
title: skein 工作流连线（create → plan → 确认 → start → exec → check → finish）
layer: core
category: planning
keywords: [workflow,连线,阶段,确认,start,自动,状态转移]
source: sediment from skein-flow-align
authored-by: skein-spec
created: 1784822958
status: active
related: []
updated: 1784822958
---

## 铁律

- MUST：skein 工作流必须明确连线：create → plan → （用户确认）→ start → exec → check → finish
- MUST：plan 阶段完成后需**明确的用户确认**（UI 按钮/命令行提示）才能 start
- MUST：start 之后自动进入 exec 阶段（无需额外用户操作）
- MUST：各阶段职责明确，阶段间状态转移在脚本中硬编码（非隐式推断）

## 反例表
| 禁 | 改为 |
|---|---|
| plan 直接自动 start | plan 完成后等待用户确认再 start |
| plan 与 start 界限模糊 | 明确的确认操作作为分界点 |
| 阶段转移隐式进行 | 阶段转移在代码中明确处理 |

## 触发场景
- task 工作流设计
- skein flow 图与执行逻辑对齐
- UI/CLI 交互设计

## 关联
- 铁律: plan 阶段完成判据门
- 铁律: task 状态流转规则
- 实现细节: skein-flow.mmd 流程图
