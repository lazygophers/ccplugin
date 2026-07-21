---
title: plan 阶段完成判据门
layer: core
category: planning
keywords: [[plan,完成判据,exec,checklist,硬门,4条,planning收敛]]
source: plan-done-criteria
authored-by: skein-spec
created: 1784647149
status: active
related: []
updated: 1784647149
---

## 铁律
- MUST：plan 阶段完成判据门勾满才转 exec（4 条 checklist 全勾）
- MUST：判据门为硬约束，未勾满禁 `skein start`
- MUST：4 条判据：①task 已 create (含可读 slug) ②prd.md 已填完 (各章 `- [ ] TODO` 全勾) ③subtask 已规划 (`subtask add` 落 task.json DAG) ④设计方案已定 (design.md 正文; 或 main 豁免)
- MUST：豁免条件仅 main 可判定（简单任务可略设计方案，但其余 3 条仍须勾）

## 反例表
| 禁 | 改为 |
|---|---|
| prd TODO 未勾完即 start | 勾满 4 条才 start |
| 无 subtask 规划即转 exec | 至少拆分 subtask 并登记 DAG |
| 设计方案未定即 start | 填完 design.md 正文 (或 main 判定豁免) |
| 自降判据标准「差不多就行」 | 4 条逐条硬核验 |

## 触发场景
- plan 阶段收尾前自查 4 条 checklist
- `skein start` 前脚本校验判据门（未过拒 start）
- planning 流程 checkpoint

## 关联
- 铁律: start 强制 prd 硬门 (core/planning/task-detail-enhance-52.md) — 互补，本门是 plan 完成判据，prd 门是 start 前校验
- 实现细节: skein-plan SKILL.md §✅ plan 阶段完成判据 (2026-07-21落地)
