# SKEIN 看板

> 经 `skein.py board` 渲染, 禁直接编辑。无 task 级 focus — 就绪 task 皆可并行。

| id | 名称 | 状态 | 前置 | worktree |
|---|---|---|---|---|
| inventory-service | 库存服务 | 进行中 | - | .worktrees/skein-inventory-service |
| notification-service | 消息通知服务 | 待处理 | payment-gateway | - |
| order-create-api | 订单创建 API | 进行中 | - | .worktrees/skein-order-create-api |
| order-pay | 订单支付 | 待处理 | order-create-api | - |
| order-report | 订单报表导出 | 待处理 | order-create-api | - |
| payment-gateway | 支付网关对接 | 检查中 | - | .worktrees/skein-payment-gateway |
| refund-flow | 退款流程 | 待处理 | order-pay,payment-gateway | - |
