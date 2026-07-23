---
title: exec 阶段无验收勾选（验收全归 check）
layer: core
category: planning
keywords: [exec,验收,checkpoint,职责划分,check阶段]
source: sediment from skein-flow-align
authored-by: skein-spec
created: 1784822932
status: active
related: []
updated: 1784822932
---

## 铁律

- MUST：exec 阶段任务调度循环禁勾验收(checkpoint)，仅 done/fail 两态转移
- MUST：所有验收(checkpoint)职责转移到 check 阶段（skein-check 承载）
- MUST：exec skill 循环仅负责执行 subtask，不触发验收逻辑

## 反例表
| 禁 | 改为 |
|---|---|
| exec 调度循环内勾 subtask checkpoint | 删除 exec 中的勾验收逻辑 |
| 验收判断分散在 exec/check 两阶段 | 验收全部在 check 阶段集中 |
| exec 完成后直接标记验收 | exec 仅 done/fail，验收由 check 处理 |

## 触发场景
- exec skill 调度 subtask 时
- skein-executor agent 改进
- task 执行流程对齐

## 关联
- 铁律: skein-check 两步法（checkpoint + 场景自适应）
- 铁律: task 状态流转规则（单 task 全 done → check）
