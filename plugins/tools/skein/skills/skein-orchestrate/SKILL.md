---
name: skein-orchestrate
description: 动态 DAG 编排调度 (task 级 + subtask 级双层)。exec 阶段把 planning 拆好的 subtask 派 skein-implementer 执行、或同 session 多 task 并行时使用 — main 作调度器, 按冲突自算边 + depends_on 组成 DAG, 并发上限 2, ready 即派 / 完成即派。只管执行编排, 不做需求/方案设计。
---

# skein-orchestrate — 动态 DAG 编排调度 (双层)

**编排两层**: ① **subtask 级** (exec 阶段, 单 task 内把拆好的 subtask 派 `skein-implementer`); ② **task 级** (同 session 多 active task 并行, 见末节)。两层同构, 都是 main 作调度器跑同一套 DAG 算法。**只管执行编排** (职责划分 / 并行 / 依赖), 不碰需求 / 方案设计 (那归 `skein-planning` brainstorm)。

## 调度 DAG = 冲突自算边 ∪ 显式 depends_on

1. **静态冲突边 (自算)** — 两 subtask 的 write-files glob 相交 或 exec-scope 相交 → 串行 (不能并发)。不相交 → 可并行。
2. **显式依赖边** — subtask 的 `depends_on` (planning 定, 写进 implement.md 调度图)。被依赖者未 done, 依赖者不 ready。
3. **最终 DAG** = 两者并集。ready (所有前置 done + 无冲突占用) 的 subtask 并行派, 未就绪串行等。

## 调度循环 (动态, 完成即派)

```
就绪集 = DAG 中所有前置已 done 且无冲突占用的 subtask
while 还有未完成 subtask:
    while 并发数 < 2 且 就绪集非空:
        派 1 个就绪 subtask 给 skein-implementer (真实 Agent 调用)
    等任一 subagent 返回
    更新完成态 → 重算就绪集 → 立即派新就绪 (不空等全部)
```

- **并发上限 2** — 同时在跑 subagent ≤ 2。
- **完成即派** — 任一返回立即查新 ready 并派, 不等一批跑完。
- **禁在 subtask 间问用户顺序** — 顺序归 planning。PRD 缺调度图 → 退回 planning 补。

## worktree

- fan-out 的所有 subagent **共享 task worktree** (subtask 不绑定 worktree, 不为 subtask 单开)。
- 默认 1 task 1 worktree。多 worktree 允许但 opt-in (非自动, 不靠 subtask 触发)。

## dispatch prompt (6 字段自包含, 缺字段不派)

派给 `skein-implementer`, 6 字段:

```
目标: <这个 subtask 要产出什么>
已知: Active task <id>, worktree=<路径>, 相关文件/上文, 召回的 recall 规则
工作目录与范围: <worktree 路径>; 只改 <文件 glob>, 禁碰其他
输出格式: <改了哪些文件 + 关键决策 + 遗留>
验收标准: <可验证断言: 测试过 / lint 净 / 功能点>
失败处理: 缺信息在返回标 `需要: <问题>`; 报错读原因缩范围重试
```

- `skein-implementer` **本身即无 Agent/Task 工具** (Recursion Guard), 只执行 1 subtask, 不自派。
- 它不能 `AskUserQuestion` — 缺信息标 `需要:` 由 main 转达用户。

## 异步等待清单 (强制)

派出异步任务后结束本回合前, MUST 输出全景表:

| id | 状态 | 摘要 | 进度% |
|---|---|---|---|
| st1 | 进行中 | 改 auth 中间件 | 60 |
| st2 | 等待中 | 依赖 st1 | 0 |

状态枚举 (固定): 进行中 / 等待中 / 阻塞。同步前台阻塞 / 无在跑任务不触发。

## 多 task 并行 (同 session)

- active 集 ≤ 2 (`skein.py` max_active), start 第三个报错。
- 两 task 的 write-files / exec-scope 相交 → 串行; 不相交 → 各 worktree 各派, 合计每层并发仍 ≤ 2。
- task 级 DAG = 冲突边 ∪ task.json `deps` (`skein.py create --deps`)。

## ⛔ 反例

| 禁 | 改为 |
|---|---|
| 用本 skill 做需求/方案设计 | 只管执行编排, 设计归 `skein-planning` |
| 空等一批 subagent 全跑完再派下批 | 完成即派 (动态) |
| subagent 内再派 subagent | subtask 执行者不递归 |
| 派 agent 是叙述而非真实 Agent 调用 | 真实 tool_use |
| subtask 间停下问用户顺序 | 顺序归 planning |
