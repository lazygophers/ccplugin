---
title: motion
layer: recall
category: style
keywords: [animation,accessibility,motion,css,performance,viewport,observer]
status: active
---

## 动效尊重 prefers-reduced-motion（CSS+JS 降级）

### 触发场景
动画元素。

### 陷阱-正解
**陷阱**：无兼容无障碍。
**正解**：@media(prefers-reduced-motion:reduce) 降级；JS 动效 matchMedia 守卡。

### 规则
CSS 与 JS 双降级。

## 视口外暂停动画（IntersectionObserver 门控）

### 触发场景
卡片/进度条离开视口。

### 陷阱-正解
**陷阱**：视外还在跑动画，浪费 GPU。
**正解**：IntersectionObserver 门控，离开视口加 .paused / .voff 停 animation。

### 规则
webapp 用 .paused (60px margin)；board 用 .voff (120px margin)。
