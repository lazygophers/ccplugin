# SKEIN 子任务看板 — t07 库存服务

> 经 `skein.py subtask` 渲染, 禁直接读写; 取态用 `skein.py subtask list <id>`。

| sid | 名称 | 状态 | 依赖 | 写文件 | reason |
|---|---|---|---|---|---|
| s1 | 库存模型与迁移 | 已完成 | - | internal/inventory/model*.go | stock/reserved 双字段 |
| s2 | 预占与回滚 | 运行中 | s1 | internal/inventory/reserve*.go | Lua 脚本保证原子, 契约1 |
| s3 | 超时回滚定时任务 | 待处理 | s2 | internal/inventory/sweeper*.go | 扫描过期预占并释放 |

并发上限: 2
