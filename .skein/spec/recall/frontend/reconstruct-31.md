---
title: Markdown 渲染必须 sanitize（防 XSS）
layer: recall
category: frontend
keywords: [xss,markdown,sanitize,security,html]
source: reconstruct
authored-by: skein-spec
created: 1784346539
status: active
related: []
updated: 1784346539
---

## 铁律

- MUST：定义 `sanitize(html)` 函数，删除 `<script>` 标签与 `on*` 属性
- MUST：v-html / innerHTML 指令前必须先 sanitize
- MUST：提供 `renderSafe(md)` 包装，自动 sanitize 结果
- MUST：两处实现一致 webapp/src/lib/md.js + board/doc.js

## 反例表

| 禁 | 改为 |
|---|---|
| `innerHTML = md.render(text)` 直接渲染 | `innerHTML = renderSafe(text)` |
| 用户 md 内容无 sanitize | sanitize 去 script/on* |
| `<img onerror="alert()">` 被执行 | sanitize 剥 onerror |
