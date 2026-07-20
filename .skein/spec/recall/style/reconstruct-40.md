---
title: glass 令牌派生 + backdrop-filter
layer: recall
category: style
keywords: [style,glass,effect,css]
source: reconstruct
authored-by: skein-spec
created: 1784346092
status: active
related: []
updated: 1784346092
---

## 触发场景
玻璃质感面板。

## 陷阳-正解
**陷阺**：硬编码 glass 样式。
**正解**：glass 令牌派生 (--glass-bg/brd/shadow 等)；配 backdrop-filter blur+saturate。

## 规则
仅 webapp 专属（board 无 glass 层）。
