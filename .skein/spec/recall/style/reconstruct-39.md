---
title: 主题双轨：两套 CSS + data-theme 切换 + localStorage
layer: recall
category: style
keywords: [theme,dark,mode,css,localStorage]
source: reconstruct
authored-by: skein-spec
created: 1784346092
status: active
related: []
updated: 1784346092
---

## 触发场景
支持浅/暗主题切换。

## 陷阳-正解
**陷阺**：仅一套 CSS，用 JS 改色。
**正解**：两套 CSS 同加载（data-theme 选择器），仅改 data-theme + localStorage 切换。

## 规则
后端同时 link skein.css + skein-dark.css；前端 data-theme + localStorage 持久化；优先级 localStorage > prefers-color-scheme。
