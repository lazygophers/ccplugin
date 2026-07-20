---
title: innerHTML 拼接必须 esc() 转义（防 XSS）
layer: recall
category: frontend
keywords: [xss,html,escape,security,innerhtml]
source: reconstruct
authored-by: skein-spec
created: 1784346604
status: active
related: []
updated: 1784346604
---

## 铁律

- MUST：定义本地 `function esc(str)` 转义 `& < >` 为 HTML entity
- MUST：任何 innerHTML 拼接必须先 `esc(userText)` 再拼
- MUST：公式 `html += \`<div>${esc(data)}</div>\`` （非 `${data}`）
- MUST：6 文件一致 board-render.js / dag.js / config-modal.js / pages/* / app.js

## 反例表

| 禁 | 改为 |
|---|---|
| `html += \`<p>${userInput}</p>\`` | `html += \`<p>${esc(userInput)}</p>\`` |
| 用户名直接插 innerHTML | esc(userName) |
| 缺 esc 函数 | 定义 esc 转义 &<> |
