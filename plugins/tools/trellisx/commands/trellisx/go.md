---
name: go
description: "执行所有 pending (planning 态) task。Trigger: 'go', '执行 pending', '跑规划好的 task', '把规划好的任务都执行了'。消费 /trellisx-add 攒下的 planning 态 task, 走 flow 的 start→exec→check→finish 闭环。边界: add=只规划停, flow=单请求全闭环, go=批量执行已规划的 pending task。go 禁做 planning。"
argument-hint: "[task-id...] (缺省=执行所有 pending planning 态 task)"
memory: project
---

# go — 执行所有 pending 规划态 task

消费 `/trellisx-add` 攒下的、停在 `task.py start` 之前的 **planning 态** task, 按 task 级 DAG 滚动执行到闭环。

> **边界 (禁越)**: go **只消费**, **禁做 planning** (判新旧 / brainstorm / grill / 写 prd/design/implement 全归 `/trellisx-add`)。缺规划就没 task 可跑 → 走空态提示, 不现场补规划。

## 1. 枚举 pending 集

```bash
python3 ./.trellis/scripts/task.py list --status planning
```

- 输出即 pending 集 = 已 `task.py create`、未 `task.py start` 的 task。
- 有 `[task-id...]` 参数 → 只取交集里指定的那些 task; 无参 → 全部 planning 态。

## 2. 空态 (不报错)

pending 集为空 → 输出提示并退出, **禁报错、禁现场规划**:

> 无待执行 task, 先 /trellisx-add <描述> 规划出 planning 态 task 再来 /go。

## 3. 非空 → 按 task 级 DAG 滚动执行

调度**复用既存机制, 不新写算法**:

- **冲突判定**: `trellisx-orchestrate/references/scheduling.md` §2 (write-files glob 相交 或 exec-scope 相交 → 依赖边串行; 不相交 → 可并行)。
- **task 级并行调度**: `scheduling.md` §9 + `trellisx-flow/SKILL.md`「多 task 并行调度」段 (L47-52)。
- **task 级并发上限 2 滚动** (`MAX_ACTIVE_TASKS`): 同时最多 2 个 task active, 完成一个 `finish` 后再 `start` 下一个 ready 的, 不空等全部。冲突的 task 串行, 不冲突的并行。
- **task 间顺序禁令** (scheduling.md §9): 顺序由 DAG (write-files/exec-scope 静态冲突) 决定, **禁问用户"哪个 task 先做"**; DAG 缺依赖声明 → 退回该 task 的 planning 补, 不在调度时问。

每个 ready 的 task 走 **flow 的 `start → exec → check → finish` 载体铁律** (见 `trellisx-flow/SKILL.md`「执行载体铁律」段, 不复制):

- `task.py start` / `finish` / `archive` 由 **main 同步跑** (非实质工作)。
- **exec/check 默认 subagent 编排**: main 是调度器, 派各 `trellis-implement` 各执行 1 subtask (subtask 级并发上限 2, 完成即派), 共享 task worktree; **trellis-implement 不递归**。
- **有 task 必有 worktree** (task 级隔离, 主工作区零改动)。
- 每个 agent 完成或阻塞 → **立即回传摘要** (禁批量延迟汇总)。
- 派异步任务后结束本回合前 → 输出 4 列任务清单表 (id · 状态 · 摘要 · 进度%), 见 `trellisx-orchestrate/references/progress-communication.md`。

## 4. 收尾

全部 pending task 走完闭环 (每个 `finish` 触发 `after_finish` hook 自动 commit→merge→archive→销 worktree) → 回传本轮执行的 task 清单与结果。
