---
description: "HITL人工审批 - 关键决策点插入人工审批，风险分级(低/中/高)自动或手动审批，安全优先默认拒绝高风险操作"
model: sonnet
context: fork
user-invocable: false
---

<!-- STATIC_CONTENT: Cacheable (5200+ tokens) -->

# Skills(task:hitl) - HITL 审批规范

## 概述

在 task:loop 关键决策点插入人工审批，确保高风险操作得到用户确认。符合 EU AI Act 2026 Article 14（Human Oversight）。

**原则**：安全优先（默认拒绝高风险）、80%+操作自动通过、所有决策可追溯

## 风险分级

| 级别 | 评分 | 行为 | 示例 |
|------|------|------|------|
| auto | 0-3 | 自动通过 | Read、Grep、go test |
| review | 4-6 | 需审查 | Edit、Write、npm install |
| mandatory | 7-10 | 强制审批 | rm -rf、git push --force |

评估维度：可逆性(40%) + 影响范围(30%) + 敏感性(20%) + 外部影响(10%)

## 集成点

| 位置 | 时机 | 审批内容 |
|------|------|---------|
| 计划确认(Planning) | planner生成计划后 | 风险评估摘要(auto/review/mandatory分布) |
| 任务执行(Execution) | 每个工具调用前 | 拦截Edit/Write/Bash，按风险等级决定 |
| 危险操作(Adjustment) | adjuster建议危险操作时 | 自愈操作(删除文件/修改配置)需确认 |

## API

`hitl_approve_operation(operation, context, user_config)` → `{approved, risk_classification, approval}`

详见 `approval-policies.md` 和 `risk-classifier.md`

## 配置

内置默认值：enabled | trust_mode(review→auto) | timeout(review:5min, mandatory:10min) | overrides。用户可在 loop 调用时通过参数覆盖。

审批日志：`.claude/plans/{task_id}/approval-log.json`（操作详情+风险分级+用户决策+执行结果）

<!-- /STATIC_CONTENT -->
