---
title: webapp 参数一律 query (禁 path 参数)
layer: core
category: arch
keywords: [路由,url,query,path参数,详情页,router,SPA]
source: user-hardrule
authored-by: skein-spec
created: 1785230805
status: active
related: []
updated: 1785230805
---

webapp 所有页面参数一律用 query string, 禁任何形式的 path 参数。

- 详情页形如 `/task/detail?id=<tid>`, 禁 `/task/<tid>`。
- 后端加精确 SPA route 时须声明在 StaticFiles mount 之前, 否则 `/task/detail` 被 `/task` 静态 mount 吞成 404 (见 `[arch] 精确路由声明在 StaticFiles mount 前`)。
- router `parse()` 只从 `URLSearchParams` 取参; 旧 path 形式链接就地 `replaceState` 改写成 query 形式兼容。
