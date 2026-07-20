---
title: SPA page 模块统一契约（render(mount, params, ctx)）
layer: core
category: arch
keywords: [spa,page,router,contract,async]
source: reconstruct
authored-by: skein-spec
created: 1784346922
status: active
related: []
updated: 1784346922
---

## 铁律

- MUST：每个 page（webapp/src/pages/<name>.js）导出 `async function render(mount, params, ctx)` 且 6/6 一致
- MUST：router 用 `import(\`./pages/${name}.js\`).then(mod => mod.render(...))` 动态加载
- MUST：ctx = { api, md, onLive } 为依赖容器

## 反例表

| 禁 | 改为 |
|---|---|
| 无 render export | async render(mount, params, ctx) |
| router 直接 import | import() 动态加载 |
