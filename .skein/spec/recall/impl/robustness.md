---
title: robustness
layer: recall
category: impl
keywords: [error,robustness,json,corruption,config,default,budget,batch-side-effect,migration]
status: active
---

## 单个 task.json 损坏隔离（skip + 告警）

### 触发场景
仓库中发现某个 task.json 半写或手工破坏。

### 陷阱-正解
**陷阱**：crash 整个看板。
**正解**：try/except JSONDecodeError，跳过该 task 并告警。

### 规则
_all() 读取时容错，DBG.log red 记录。

### 关联
impl/graceful-degradation

## config 数值默认变更触发批量副作用需先评估存量

### 规律

改 config 数值类默认 (如 spec_core_budget), 若新默认低于现存量实际值, maintain --apply 批量副作用 (24 条 core→recall 全降)。

### 铁律
- MUST: 改 config 数值默认前, 先跑存量统计 (core 实际字符 vs 新默认), 评估批量降级/归档影响
- MUST: 批量降级不可逆成本高 (SessionStart 注入稀薄, 索引断裂), 默认值调整需显式提示用户接受批量影响
- MUST: 新仓 vs 现仓场景区分 — 现仓已存量配置不应被新默认值覆盖 (init 幂等只补缺不重写)

### 反例
spec-memory-extend 把 spec_core_budget 默认 8000→1000 (未先查现 core ~11K), specer maintain --apply 触发 24 条全降, core 11055→777 字符, SessionStart 注入剩 3 条。
