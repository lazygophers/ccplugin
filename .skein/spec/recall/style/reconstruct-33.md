---
title: 状态常量前缀（S_/SS_）
layer: recall
category: style
keywords: [naming,constant,state,prefix]
source: reconstruct
authored-by: skein-spec
created: 1784346042
status: active
related: []
updated: 1784346042
---

## 触发场景
定义新状态枚举。

## 陷阺-正解
**陷阺**：PENDING/ACTIVE 无前缀混淆。
**正解**：task 级 `S_PENDING`；subtask 级 `SS_PENDING`；值为中文枚举字符串。
