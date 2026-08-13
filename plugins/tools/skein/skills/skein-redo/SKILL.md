---
name: skein-redo
description: "SKEIN 断点续跑。session 意外结束后重新调度未完成的 agent, 继续 main 尚未闭环的工作。不等同复位 — running subtask 不强制 fail, 只补派未完成的调度。"
user-invocable: true
argument-hint: "[任务ID]"
arguments: "[任务ID]"
model: sonnet
effort: medium
---

# skein-redo — 断点续跑

> 🔒 全局流程规则（状态机/调度/优先级等）以 skein-flow/references/ 为单一真值源。

## 定位

session 意外结束 (崩溃 / 手动中断 / context 满) 后恢复。不是回滚也不是复位 — 而是接上断点继续闭环：

1. 查当前有哪些 open task，状态分别卡在哪
2. 重排尚未完成的 agent 调度（running subtask 若确认已死才 fail，否则等其自然完成）
3. 继续 main 未做完的事（exec → check → finish）

## 首步

```bash
skein list --status open --json
```

拿到 open task 列表，找到目标 task 的 tid 和当前状态。

## 按起点状态续跑

| 起点状态    | redo 行为 |
| ----------- | --------- |
| `pending`   | 续 plan 到收敛，confirm 后续 exec |
| `research`  | research subtask 仍在跑则等待；全 done 则 `skein task plan` 回 pending 续 plan |
| `active`    | subtask 有 running 则核对是否真的在跑（WS / agent 状态）；已死的 fail + 重派；未派的继续 `skein flow run` 调度 |
| `check`     | 直接重派 checker（`skein flow run` 会给 check hint） |
| `finishing` | 直接重派 finisher（`skein flow run` 会给 finishing hint） |
| `done`      | 报已闭环，无事可做 |

## 核心：重排调度

不是 fail 全部 running 然后重来 — 而是跑 `skein flow run`，scheduler 会自动认领 ready subtask 并给出派发 hint：

```bash
skein flow run
```

消费 `result.exec.next[]` + `result.check.next[]`，按 hint 派 Agent。派完后继续 flow-loop 闭环骨架。

### running subtask 判定

- 确认 agent 已死（session 崩溃、进程不存在）→ `skein subtask fail <tid> <sid> --note "session 中断, agent 已死"` → 下轮 flow run 自动重派
- 不确定是否还活着 → 不动，等下一轮 flow run 自然看到状态变化
- 禁无条件 fail 全部 running — agent 可能还在正常跑

## 续跑调度骨架

复位/确认完成后，按 [skein-flow/references/flow-loop.md](../skein-flow/references/flow-loop.md) 的 exec/check/finish 骨架继续闭环。禁 sleep 轮询 — Agent 异步回传通知驱动。
