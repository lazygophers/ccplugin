# SKEIN 子任务看板 — t01 订单查询接口

> 经 `skein.py subtask` 渲染, 禁直接读写; 取态用 `skein.py subtask list <id>`。

| sid | 名称 | 状态 | 依赖 | 写文件 | reason |
|---|---|---|---|---|---|
| s1 | 查询接口 + 缓存 | done | - | internal/order/query*.go | GET /orders/{id} 带 Redis 缓存 |

并发上限: 2　更新: 2026-07-11T15:08:25
