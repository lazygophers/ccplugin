---
title: 函数签名类型注解 + 中文 docstring（Args/Returns）
layer: recall
category: script
keywords: [typing,docstring,annotation]
source: reconstruct
authored-by: skein-spec
created: 1784346042
status: active
related: []
updated: 1784346042
---

## 触发场景
编写公共函数。

## 陷阺-正解
**陷阺**：无类型注解，docstring 不清楚。
**正解**：函数签名带 `(param: Type) -> Type` 注解 + Args/Returns 中文 docstring。
