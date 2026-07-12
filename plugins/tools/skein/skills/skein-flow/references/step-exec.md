# exec — 执行编排 (agent 编排)

执行阶段 main 作调度器, 动态 DAG 为每个 subtask 选合适 agent (按任务性质挑现有 agent, 无合适的用 `skein-executor`) 各执行 1 subtask, 全部改动落 task worktree, 主工作区零改动。每个 agent 完成即回传。

调度算法 (并行只看 depends_on DAG / ready 即派 / 并发上限 2 / 完成即派 / dispatch prompt 6 字段携带执行纪律与递归护栏) 见 [scheduling-algorithm.md](scheduling-algorithm.md)。

**异步等待 MUST 输出任务清单**: 派出异步任务后、结束本回合前, 输出全景表 (4 列: id/状态/摘要/进度%, 状态枚举 进行中/等待中/阻塞), 格式见 [progress-reporting.md](progress-reporting.md)。

**exec 阶段禁问用户顺序**: 顺序归 planning (调度图 + depends_on DAG)。exec 只跑动态调度循环 — ready 即派、完成即派、并发 2。PRD 缺调度图 → 退回 planning 补, 不在 exec 问。
