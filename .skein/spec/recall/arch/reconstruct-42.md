---
title: page 依赖注入（禁直连 API）
layer: recall
category: arch
keywords: [architecture,dependency,injection,page,spa]
source: reconstruct
authored-by: skein-spec
created: 1784346731
status: active
related: []
updated: 1784346731
---

## 铁律

- MUST：page 内部不 `import lib/api`，所有依赖通过 ctx 参数获取
- MUST：ctx 由 app.js 顶层注入，router 组装下传给 page.render()
- MUST：依赖容器包括 api、md、onLive 三个关键依赖（可扩展）

## 反例表

| 禁 | 改为 |
|---|---|
| `import { api } from '../lib/api.js'` in page | 从 ctx 解构：`const { api } = ctx` |
| page 直接创建 api 实例 | app 创建并通过 ctx 注入 |
| 依赖散落各处初始化 | 集中在 app.js |
