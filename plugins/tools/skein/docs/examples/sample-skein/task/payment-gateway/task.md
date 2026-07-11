# SKEIN 子任务看板 — payment-gateway 支付网关对接

> 经 `skein.py subtask` 渲染, 禁直接读写; 取态用 `skein.py subtask list <id>`。

| sid | 名称 | 状态 | 依赖 | 写文件 | reason |
|---|---|---|---|---|---|
| s1 | 网关 SDK 封装 | 已完成 | - | internal/pay/gateway*.go | 统一 charge/refund 签名 |
| s2 | 回调验签 | 已完成 | - | internal/pay/callback*.go | 验签 + 去重, 契约2 |
| s3 | 对账拉单 | 已完成 | s1 | internal/pay/recon*.go | 日终对账补偿漏单 |

并发上限: 2
