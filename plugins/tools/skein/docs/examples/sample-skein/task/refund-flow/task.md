# SKEIN 子任务看板 — refund-flow 退款流程

> 经 `skein.py subtask` 渲染, 禁直接读写; 取态用 `skein.py subtask list <id>`。

| sid | 名称 | 状态 | 依赖 | 写文件 | reason |
|---|---|---|---|---|---|
| s1 | 退款单据 | 待处理 | - | internal/refund/model*.go | 退款申请落库 + 状态机 |
| s2 | 原路退款调用 | 待处理 | s1 | internal/refund/gateway*.go | 调支付网关 refund, 契约 |
| s3 | 库存回补 | 待处理 | s1 | internal/inventory/restore*.go | 退款成功回补库存 |

并发上限: 2
