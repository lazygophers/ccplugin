# SKEIN 看板

> 经 `skein.py board` 渲染, 禁直接编辑。无 task 级 focus — 就绪 task 皆可并行。

| id | 名称 | 状态 | 前置 | worktree |
|---|---|---|---|---|
| t02 | 订单创建 API | 进行中 | - | .worktrees/skein-t02 |
| t03 | 订单支付 | 待处理 | t02 | - |
| t06 | 支付网关对接 | 检查中 | - | .worktrees/skein-t06 |
| t07 | 库存服务 | 进行中 | - | .worktrees/skein-t07 |
| t08 | 退款流程 | 待处理 | t03,t06 | - |
| t09 | 订单报表导出 | 待处理 | t02 | - |
| t10 | 消息通知服务 | 待处理 | t06 | - |
