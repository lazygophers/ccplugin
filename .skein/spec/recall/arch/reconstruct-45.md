---
title: SPA catch-all fallback 声明在所有 mount 之后
layer: recall
category: arch
keywords: [routing,spa,fallback,mount,starlette]
source: reconstruct
authored-by: skein-spec
created: 1784346795
status: active
related: []
updated: 1784346795
---

## 铁律

- MUST：SPA fallback 中间件/路由声明在所有 mount 之后
- MUST：fallback 返回 index.html，让前端 router 处理路由
- MUST：否则 /vendor/app.css 等静态被 fallback 吞成 index.html

## 反例表

| 禁 | 改为 |
|---|---|
| fallback 在 mount 之前 | 在 mount 之后声明 |
| /vendor/x.css 返回 index.html 破坏 | 调整声明顺序 |
| SPA 前端路由全 404 | 确认 fallback 在最后 |
