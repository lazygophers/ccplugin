# SKEIN 文档

**独立任务管理插件** — 零 trellis / trellisx 依赖, 自带 `.skein/` 工作区。名取「线团」(skein of yarn): 任务如纱线, 编织、调度、收束。

把每个复杂请求强制织成一条闭环 task: **规划 → 执行 → 检查 → 收束** (plan → exec → check → finish), 全程 worktree 隔离主工作区、动态 DAG 调度 subagent 并行, 并把踩过的坑沉淀成两层规则记忆供后续 task 复用。

## 我该读哪篇

| 你想 | 读这篇 |
| --- | --- |
| 装好插件, 跑通第一个 task | [getting-started.md](getting-started.md) |
| 搞懂插件内部怎么运转 (流程 / 调度 / 记忆) | [workflow.md](workflow.md) |
| 不同类型的活儿分别怎么用 | [scenarios.md](scenarios.md) |
| 照着最佳实践 + 流程图干 | [best-practices.md](best-practices.md) |
| 查某条 CLI / skill / agent 干嘛的 | [reference.md](reference.md) |
| 查某个名词啥意思 | [glossary.md](glossary.md) |
| 照着一份完整样例 `.skein/` 对着看 | [examples/](examples/) |

## 一句话上手

```
/skein-exec 给用户模块加上手机号登录, 含短信验证码下发与校验
```

复杂 / 多步 / 跨文件的请求也会**自动**触发 `skein-flow` 走同一套闭环, 无需显式命令。

## 核心概念速览

| 概念 | 是什么 |
| --- | --- |
| **task** | 一条闭环任务记录, 由 `skein` 管理, 存 `.skein/task/<id>/` |
| **闭环** | plan → exec → check → finish, 不可跳步, 未 archive = 未完成 |
| **worktree 隔离** | 每 task 一个 git worktree, 所有改动落 `.worktrees/`, 主工作区零改动 |
| **双层调度** | main 作调度器, task 级 + subtask 级同构 DAG, 并行只看 `depends_on`, 并发上限 2, 完成即派 |
| **两层规则记忆** | `core` 常驻注入 + `recall` 按需召回, 按类目分子目录 (差异化核心) |
| **看板** | `.skein/task.md`, 经 `skein board` 渲染, 禁直接编辑 |
| **sediment 判定门** | 每个 task finish 前判本次 learning → core / recall / drop |
| **契约不变量** | planning 锁 `contracts` 不可回退不变量, check 阶段逐条验证 |
| **compaction 永续** | SessionStart hook (`session-context`) 把活跃 task 状态在上下文压缩后重注入 |

## 差异化: 为什么不是又一个 TODO 工具

普通任务工具只记「做什么」。SKEIN 额外强制三件事:

1. **闭环不可跳步** — 没规划就不给执行, 没过检查就不给收束, 逼你把活儿真正做完而非做到一半。
2. **执行与主工作区物理隔离** — worktree 让并行改动互不污染, finish 时才合并回来, 出错随时丢弃整条 task 而主分支干净。
3. **经验沉淀成规则** — 踩过的坑不是聊天记录里的一句话, 而是落盘成 `core`/`recall` 规则, 下一个 task 自动带上, 越用越懂你的项目。

细节见 [workflow.md](workflow.md)。
