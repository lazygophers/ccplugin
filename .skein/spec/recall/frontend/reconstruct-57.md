---
title: SPA page 文件名 = 路由白名单名
layer: recall
category: frontend
keywords: [spa,routing,page,filename,dynamic-import]
source: reconstruct
authored-by: skein-spec
created: 1784346818
status: active
related: []
updated: 1784346818
---

## 铁律

- MUST：pages/ 目录内文件名与路由白名单逐一对应（6 个：dashboard/board/queue/task/spec/archive）
- MUST：路由白名单在 router.js 明确列举（ROUTES 数组）
- MUST：动态 import(\`./pages/${name}.js\`) 拼接必须命中对应文件

## 反例表

| 禁 | 改为 |
|---|---|
| pages/foo-page.js 但路由名为 foo | 改文件名 pages/foo.js |
| 路由名不在白名单 | 先加入 ROUTES 再创建 page |
| 文件存在但 import 失败 | 检查文件名与拼接路由名一致 |
