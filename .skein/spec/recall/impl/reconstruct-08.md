---
title: 单个 task.json 损坏隔离（skip + 告警）
layer: recall
category: impl
keywords: [error,robustness,json,corruption]
source: reconstruct
authored-by: skein-spec
created: 1784345975
status: active
related: []
updated: 1784345975
---

## 触发场景
仓库中发现某个 task.json 半写或手工破坏。

## 陷阱-正解
**陷阱**：crash 整个看板。
**正解**：try/except JSONDecodeError，跳过该 task 并告警。

## 规则
_all() 读取时容错，DBG.log red 记录。

## 关联
impl/graceful-degradation
