---
title: localStorage key 统一 skein- 前缀
layer: recall
category: style
keywords: [localstorage,persistence,naming,key]
source: reconstruct
authored-by: skein-spec
created: 1784345975
status: active
related: []
updated: 1784345975
---

## 触发场景
需要持久化用户偏好（主题切换、面板打开状态等）。

## 陷阱-正解
**陷阱**：localStorage key 命名混乱 (theme / userData / config)。
**正解**：所有 key 一律 `skein-` 前缀 (skein-theme / skein-dagview)。

## 规则
app.js:102,118 / board/switcher.js:19,22 一致应用。

## 关联
frontend/naming-conventions
