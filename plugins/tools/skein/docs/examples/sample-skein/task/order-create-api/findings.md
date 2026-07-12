# order-create-api — 调研收敛

> planning 工件 (skein-plan 写)。**AI 可读写**。深度调研的收敛结论 + 依据 (过程笔记存 research/, 本例无独立 research 过程)。

## 收敛结论

- **幂等实现**: 参考既有 `payment` 模块的幂等键唯一约束方案 (`idempotency_keys` 表 + 唯一索引), 复用同一套, 不另造。依据: 代码库已有成熟实现, 一致性优先。
- **库存原子扣减**: 现有 `inventory.deduct()` 已支持 `WHERE stock >= qty` 原子扣减, 直接调用。
- **MQ 事件契约**: 沿用下游发货服务已订阅的 `order.created` topic 事件结构, 不新增字段。
