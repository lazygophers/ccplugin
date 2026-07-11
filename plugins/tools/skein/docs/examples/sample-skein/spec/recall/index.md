# SKEIN recall 规则索引

类目: arch(1), test(1)

| file | category | title | keywords | summary |
|---|---|---|---|---|
| arch/order-create-api-00.md | arch | 订单幂等 + 库存原子扣减 | 幂等,库存,redis,decrby,订单 | 幂等键 = `order:idem:{userId}:{bizNo}`, 唯一索引落库层兜底; 库存扣减用 Redis … |
| test/order-pay-01.md | test | 订单状态机测试覆盖要求 | 状态机,测试,订单,table-driven | 订单状态机测试必覆盖: 待支付→已支付→已发货→已完成, 及各态非法跳转拒绝 (table-driven test)。 |
