---
title: 视口外暂停动画（IntersectionObserver 门控）
layer: recall
category: style
keywords: [animation,performance,viewport,observer]
source: reconstruct
authored-by: skein-spec
created: 1784346092
status: active
related: []
updated: 1784346092
---

## 触发场景
卡片/进度条离开视口。

## 陷阳-正解
**陷阺**：视外还在跑动画，浪费 GPU。
**正解**：IntersectionObserver 门控，离开视口加 .paused / .voff 停 animation。

## 规则
webapp 用 .paused (60px margin)；board 用 .voff (120px margin)。
