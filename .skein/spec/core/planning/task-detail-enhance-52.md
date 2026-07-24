---
title: prd 硬门（主门在 confirm，start 兜底 double-check）
layer: core
category: planning
keywords: [confirm,start,prd,validation,hard-gate,completeness,就绪]
source: task-detail-enhance
authored-by: skein-spec
created: 1784546599
status: active
related: []
updated: 1785110400
---

## 铁律
- MUST：prd 硬门**主校验在 `skein confirm`**（待处理→就绪）：prd 章节齐 + 无占位 + ≥1 subtask，通过才进就绪
- MUST：prd.md 存在且四标准章节齐备（目标/边界/验收标准/索引），无 `- [ ] TODO` 占位（模板初始态）
- MUST：`skein start`（就绪→进行中）**兜底 double-check `_validate_prd`**，防 confirm 后 prd 被改空
- MUST：不通过 raise SystemExit 阻断（confirm 阻进就绪 / start 阻进行中）

## 反例表
| 禁 | 改为 |
|---|---|
| confirm 不检查 prd/subtask 就进就绪 | confirm 跑 _validate_prd + ≥1 subtask 校验 |
| prd 章节残缺仍允许 confirm | 检查四标准章节齐备且顺序一致 |
| prd 含 TODO 占位仍 confirm | 检测占位并拒绝进就绪 |
| start 完全信任 confirm 不复检 prd | start 仍兜底 _validate_prd 防中途被改空 |

## 关联
- task.json status 状态机（待处理 →confirm→ 就绪 →start→ 进行中 守卫）
- subtask 拆分前置门（confirm 前须有 ≥1 subtask 登记）
- 铁律: skein 工作流连线（confirm 用户确认门）
