---
title: 组件色一律用 var(--token)，禁硬编码
layer: recall
category: style
keywords: [style,color,token,variable,css]
source: reconstruct
authored-by: skein-spec
created: 1784345946
status: active
related: []
updated: 1784345946
---

## 触发场景
编写新组件或修改样式，需要配色。

## 陷阱-正解
**陷阱**：硬编码色值 `color: #3498db`。
**正解**：用派生令牌 `color: var(--accent)` 或语义色。

## 规则
允许唯一例外：彩底白字 `#fff` 与 body 底纹锚点。

## 关联
style/oklch-token-derivation (F-STYLE-1)
