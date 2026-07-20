---
title: 动效尊重 prefers-reduced-motion（CSS+JS 降级）
layer: recall
category: style
keywords: [animation,accessibility,motion,css]
source: reconstruct
authored-by: skein-spec
created: 1784346092
status: active
related: []
updated: 1784346092
---

## 触发场景
动画元素。

## 陷阳-正解
**陷阺**：无兼容无障碍。
**正解**：@media(prefers-reduced-motion:reduce) 降级；JS 动效 matchMedia 守卡。

## 规则
CSS 与 JS 双降级。
