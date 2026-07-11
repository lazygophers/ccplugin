# SKEIN 子任务看板 — t02 订单创建 API

> 经 `skein.py subtask` 渲染, 禁直接读写; 取态用 `skein.py subtask list <id>`。

| sid | 名称 | 状态 | 依赖 | 写文件 | reason |
|---|---|---|---|---|---|
| s1 | 请求参数校验 | done | - | internal/order/validate*.go | 校验商品/数量/收货地址, 满足契约前置 |
| s2 | 库存扣减 | running | - | internal/inventory/*.go | Redis 原子 decr, 不足即拒 (契约2) |
| s3 | 订单落库 | failed | - | internal/order/repo*.go | 唯一索引冲突, 待改幂等键生成规则重试 |
| s4 | 订单创建事件 | pending | s3 | internal/event/*.go | 落单成功后发 MQ 事件, 依赖 s3 |

并发上限: 2　更新: 2026-07-11T15:08:26
