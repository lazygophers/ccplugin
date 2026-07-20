# 跨 task subtask 并行调度 — PRD

## 目标
调度从单 task 内 claim 升级为全局跨 task claim: 所有 active task 的 ready subtask 竞争同一全局并发池 (size=max_parallel), 按拓扑深度+task优先级取 top-N。新增 `skein claim` (无 tid) 全局认领命令。

当前: `subtask claim <tid>` 单 task 级, 每 task 各占 max_parallel 槽 → 2 active task = 合计 4 并行 subagent。
目标: 全局单池, 2 active task 共享 max_parallel=2 槽, 跨 task 按权重竞争。

## 边界
- 范围内: skein.py 加 `_global_ready()` + 顶层 `claim` 命令; SKILL.md/scheduling-algorithm.md 调度段更新
- 范围外: max_active 逻辑 (仍限 active task 数); worktree 隔离; subtask done/fail 单 task 操作; `_ready()` 单 task 兼容保留
- 约束: 全局并发 ≤ max_parallel (非 max_active * max_parallel); 用户确认全局单池 + 拓扑深度+task优先级 + 新增全局 claim

## 排序键 (全局池)
```
key = (-拓扑深度, task优先级, task登记序, subtask登记序)
```
- 拓扑深度: `_crit_weight` 已退化 (每步 1 + 最长下游链)
- task 优先级: active=0 > 就绪 pending=1 > 阻塞=2
- task 登记序: task.json 创建顺序
- subtask 登记序: subtask add 顺序

## 命令
| 命令 | 作用 |
|---|---|
| `skein claim` (无 tid) | 全局跨 task: 所有 active task ready subtask 池按拓扑深度+task优先级取 top-N (N=max_parallel-全局running), 整批标 running, 返回 task/sid 对 |
| `skein subtask claim <tid>` (兼容) | 单 task: 该 task 内 ready subtask 按拓扑深度截到单 task 槽 |

## 验收标准
- [ ] `skein claim` (无 tid) 工作, 返回跨 task 就绪批 (task/sid 对)
- [ ] 全局并发 ≤ max_parallel (非每 task 各占)
- [ ] 排序 = 拓扑深度降序 + task 优先级 + 登记序
- [ ] `subtask claim <tid>` 单 task 兼容不破
- [ ] ast.parse 过
- [ ] SKILL.md/scheduling-algorithm.md 更新全局池模型
- [ ] 多 task 场景验证: 2 active task 共 ≥3 ready subtask, max_parallel=2 → 只派 2 (跨 task 竞争)

## 索引
- 任务/子任务/调度: task.json (`skein subtask list cross-task-parallel-sched`)
