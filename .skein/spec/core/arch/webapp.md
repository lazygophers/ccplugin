---
inclusion: auto
title: webapp
layer: core
category: arch
keywords: [spa,page,router,contract,async,路由,url,query,path参数,详情页,SPA,websocket,live,refresh,reactive]
status: active
---

## SPA page 模块统一契约（render(mount, params, ctx)）

### 铁律

- MUST：每个 page（webapp/src/pages/<name>.js）导出 `async function render(mount, params, ctx)` 且 6/6 一致
- MUST：router 用 `import(\`./pages/${name}.js\`).then(mod => mod.render(...))` 动态加载
- MUST：ctx = { api, md, onLive } 为依赖容器

### 反例表

| 禁 | 改为 |
|---|---|
| 无 render export | async render(mount, params, ctx) |
| router 直接 import | import() 动态加载 |

## webapp 参数一律 query (禁 path 参数)

webapp 所有页面参数一律用 query string, 禁任何形式的 path 参数。

- 详情页形如 `/task/detail?id=<tid>`, 禁 `/task/<tid>`。
- 后端加精确 SPA route 时须声明在 StaticFiles mount 之前, 否则 `/task/detail` 被 `/task` 静态 mount 吞成 404 (见 `[arch] 精确路由声明在 StaticFiles mount 前`)。
- router `parse()` 只从 `URLSearchParams` 取参; 旧 path 形式链接就地 `replaceState` 改写成 query 形式兼容。

## onLive 软刷订阅（WS 驱动视图重挂）

### 触发场景
page 需要订阅数据变化，刷新视图。

### 陷阱-正解
**陷阱**：各 page 自己管理 WS 连接与重挂逻辑。
**正解**：ctx.onLive(remountFn) 订阅数据软刷，router 切页自动退订，page 无需清理。

### 规则
live.js:8 subscribe 返回退订；router.js:62 自动退订。

### 案例
各 page 末尾 `onLive(mountApp)`。

### 关联
frontend/soft-refresh-pattern
