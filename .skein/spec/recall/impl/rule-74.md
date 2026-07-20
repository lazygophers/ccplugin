---
title: config 数值默认变更触发批量副作用需先评估存量
layer: recall
category: impl
keywords: [config,default,budget,batch-side-effect,migration]
source: -
authored-by: skein-spec
created: 1784561412
status: active
related: []
updated: 1784561412
---

## 规律

改 config 数值类默认 (如 spec_core_budget), 若新默认低于现存量实际值, maintain --apply 批量副作用 (24 条 core→recall 全降)。

## 铁律
- MUST: 改 config 数值默认前, 先跑存量统计 (core 实际字符 vs 新默认), 评估批量降级/归档影响
- MUST: 批量降级不可逆成本高 (SessionStart 注入稀薄, 索引断裂), 默认值调整需显式提示用户接受批量影响
- MUST: 新仓 vs 现仓场景区分 — 现仓已存量配置不应被新默认值覆盖 (init 幂等只补缺不重写)

## 反例
spec-memory-extend 把 spec_core_budget 默认 8000→1000 (未先查现 core ~11K), specer maintain --apply 触发 24 条全降, core 11055→777 字符, SessionStart 注入剩 3 条。
