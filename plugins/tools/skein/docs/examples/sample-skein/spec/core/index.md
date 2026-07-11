# SKEIN core 规则索引

类目: domain(1), git(1)

| file | category | title | keywords | summary |
|---|---|---|---|---|
| domain/order-create-api-01.md | domain | 金额一律整数分 | money,金额,精度,订单 | 所有金额字段用整数分 (int64), 禁 float。展示层才除 100, 防浮点误差。 |
| git/order-query-00.md | git | finish 前本地测试全绿 | test,commit,finish | commit 前必跑 `go test ./...`, 全绿才 finish。CI 无二次门, 本地是唯一关卡。 |
