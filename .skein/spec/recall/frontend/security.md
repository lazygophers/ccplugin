---
title: security
layer: recall
category: frontend
keywords: [xss,markdown,sanitize,security,html,escape,innerhtml]
status: active
---

## Markdown 渲染必须 sanitize（防 XSS）

### 铁律

- MUST：定义 `sanitize(html)` 函数，删除 `<script>` 标签与 `on*` 属性
- MUST：v-html / innerHTML 指令前必须先 sanitize
- MUST：提供 `renderSafe(md)` 包装，自动 sanitize 结果
- MUST：两处实现一致 webapp/src/lib/md.js + board/doc.js

### 反例表

| 禁 | 改为 |
|---|---|
| `innerHTML = md.render(text)` 直接渲染 | `innerHTML = renderSafe(text)` |
| 用户 md 内容无 sanitize | sanitize 去 script/on* |
| `<img onerror="alert()">` 被执行 | sanitize 剥 onerror |

## innerHTML 拼接必须 esc() 转义（防 XSS）

### 铁律

- MUST：定义本地 `function esc(str)` 转义 `& < >` 为 HTML entity
- MUST：任何 innerHTML 拼接必须先 `esc(userText)` 再拼
- MUST：公式 `html += \`<div>${esc(data)}</div>\`` （非 `${data}`）
- MUST：6 文件一致 board-render.js / dag.js / config-modal.js / pages/* / app.js

### 反例表

| 禁 | 改为 |
|---|---|
| `html += \`<p>${userInput}</p>\`` | `html += \`<p>${esc(userInput)}</p>\`` |
| 用户名直接插 innerHTML | esc(userName) |
| 缺 esc 函数 | 定义 esc 转义 &<> |
