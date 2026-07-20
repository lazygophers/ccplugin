---
title: start 强制 prd 硬门
layer: core
category: planning
keywords: [start,prd,validation,hard-gate,completeness]
source: task-detail-enhance
authored-by: skein-spec
created: 1784546599
status: active
related: []
updated: 1784546599
---

## 铁律
- MUST：任何 task start 前必过 prd 校验（章节齐 + 无占位）
- MUST：prd.md 存在且四标准章节齐备（目标/边界/验收标准/索引）
- MUST：无 `- [ ] TODO` 占位（模板初始态，说明该节未填实）
- MUST：不通过 raise SystemExit 阻断 start

## 反例表
| 禁 | 改为 |
|---|---|
| start 不检查 prd 就绪 | start 前跑 _validate_prd 校验 |
| prd 章节残缺仍允许 start | 检查四标准章节齐备且顺序一致 |
| prd 含 TODO 占位仍 start | 检测占位并拒绝 start |
| prd 缺失仍允许 start | 先 skein create + 填 prd 再 start |

## 关联
- task.json status 状态机 (PENDING → ACTIVE 转换守卫)
- subtask 拆分前置门 (start 前须有 subtask 登记)
