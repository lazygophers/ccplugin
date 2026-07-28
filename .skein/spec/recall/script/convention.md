---
title: convention
layer: recall
category: script
keywords: [typing,docstring,annotation]
status: active
---

## 函数签名类型注解 + 中文 docstring（Args/Returns）

### 触发场景
编写公共函数。

### 陷阱-正解
**陷阱**：无类型注解，docstring 不清楚。
**正解**：函数签名带 `(param: Type) -> Type` 注解 + Args/Returns 中文 docstring。
