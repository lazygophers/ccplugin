---
name: skein-orchestrate
description: 动态 DAG 编排调度 (task 级 + subtask 级双层)。exec 阶段把 planning 拆好的 subtask 派 skein-implementer 执行、或同 session 多 task 并行时使用 — main 作调度器, 按冲突自算边 + depends_on 组成 DAG, 并发上限 2, ready 即派 / 完成即派。只管执行编排, 不做需求/方案设计。
---

# skein-orchestrate — 动态 DAG 编排调度 (双层)

**编排两层**: ① **subtask 级** (exec 阶段, 单 task 内把拆好的 subtask 派 `skein-implementer`); ② **task 级** (同 session 多 active task 并行, 见末节)。两层同构, 都是 main 作调度器跑同一套 DAG 算法。**只管执行编排** (职责划分 / 并行 / 依赖), 不碰需求 / 方案设计 (那归 `skein-planning` brainstorm)。

## 调度算法 (DAG / 调度循环 / 并发上限 / worktree / 多 task 并行)

调度 DAG = 冲突自算边 ∪ 显式 depends_on, 动态完成即派, 并发上限 2 — 详见 [references/scheduling-algorithm.md](references/scheduling-algorithm.md)。

## dispatch prompt (6 字段自包含, 缺字段不派)

派给 `skein-implementer`, 6 字段:

```
目标: <这个 subtask 要产出什么>
已知: Active task <id>, worktree=<路径>, 相关文件/上文, 召回的 recall 规则
工作目录与范围: <worktree 路径>; 只改下列文件 (每文件带 reason), 禁碰其他:
  - <文件路径A> — reason: <改它是为了满足哪条契约/需求>
  - <文件路径B> — reason: <...>
输出格式: <改了哪些文件 + 关键决策 + 遗留>
验收标准: <可验证断言: 测试过 / lint 净 / 功能点>
失败处理: 缺信息在返回标 `需要: <问题>`; 报错读原因缩范围重试
```

- 🔴 **per-file reason 必填** — 范围段每个目标文件后附一句 reason (为什么改它), 让 implementer 拿到就知道每个文件的改动意图, 并据此在写前复述契约 (见 `skein-implementer` 写前硬门)。reason 与该文件适用契约矛盾时 implementer 会标 `需要:` 回传, 不擅改。
- `skein-implementer` **本身即无 Agent/Task 工具** (Recursion Guard), 只执行 1 subtask, 不自派。
- 它不能 `AskUserQuestion` — 缺信息标 `需要:` 由 main 转达用户。

## 异步等待清单 (强制)

派出异步任务后结束本回合前, MUST 输出状态全景表 (状态枚举 进行中/等待中/阻塞) — 详见 [references/progress-reporting.md](references/progress-reporting.md)。

## ⛔ 反例

| 禁 | 改为 |
|---|---|
| 用本 skill 做需求/方案设计 | 只管执行编排, 设计归 `skein-planning` |
| 空等一批 subagent 全跑完再派下批 | 完成即派 (动态) |
| subagent 内再派 subagent | subtask 执行者不递归 |
| 派 agent 是叙述而非真实 Agent 调用 | 真实 tool_use |
| subtask 间停下问用户顺序 | 顺序归 planning |
