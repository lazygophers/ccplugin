---
title: innerHTML 软刷新保滚动位（三层替换 + 居中）
layer: recall
category: frontend
keywords: [scroll,dom,refresh,state]
source: reconstruct
authored-by: skein-spec
created: 1784346093
status: active
related: []
updated: 1784346093
---

## 触发场景
软刷新 (innerHTML swap)。

## 陷阳-正解
**陷阺**：滚动位置丢。
**正解**：记录 scrollTop/Left + pageYOffset，换 DOM 后复原；首屏无存位则居中活跃节点。

## 规则
board/board-render.js:376-401；webapp 沿用。
