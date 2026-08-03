---
title: flow-auto-plan
category: flow
keywords: [补plan, plan产物, pending, 清空模式, prd未填, 无subtask, estimate, 自动规划]
status: active
inclusion: auto
---

## flow 编排层补 plan 缺失

### 触发条件
- flow 清空模式（无参数或带 `flow` 参数）扫描 pending task
- task 状态为 `pending`
- task 的判据检查显示「缺 plan 产物」（PRD 未填、无 subtask、estimate 缺失等）
- 所有前置依赖已完成（depends_on 全 done）

### 行为
flow 主循环在发现上述条件时，自动补全 plan 流程：
1. 基于现有 PRD 框架（若存在）补完 PRD 正文
2. 生成初始 subtask 列表
3. 添加 estimate 信息
4. 之后自动推进 `skein confirm` 进入 `active` 阶段

不需用户手动运行 `skein plan` 或逐步填表。该路径走 flow 主循环内的自动分流，属编排层职责。

### 目标
避免 flow 清空模式跳过缺 plan 的待处理 task；确保流程不遗漏、自动驱动规划不完善的任务向前推进。

### 实现细节
- 参考提交：5528969f4 "fix(skein-flow): 补 plan 产物收敛路径"
- 参考文档：plugins/tools/skein/skills/skein-flow/references/flow-loop.md 第 79 行
- 状态转移：pending → (auto plan补全) → active via confirm

### 约束
- 该路径仅在「全空」flow 模式或特定调度条件下触发
- plan 补全仍需符合全量流程（confirm 前人审检查仍可拒绝）
- 不改变 brainstorm/grill 的深度思考过程，仅补最小可行的 plan 框架

### 关联规则
`plugins/tools/skein/skills/skein-flow/references/flow-loop.md` — §3 主循环骨架 (pending 三分路) / §1.1 task 状态。
写成路径而非 wikilink: flow-loop 是仓库 skill 文档, spec 库无同名条目, wikilink 解析不到。
