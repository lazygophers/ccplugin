# Task 状态机

task 状态落盘值为英文；中文只用于展示。执行过程、状态推进、失败后怎么继续，统一见 [flow-loop.md](flow-loop.md)。本文件只保留状态与命令语义索引。

## 状态

| 落盘值 | 展示名 | 含义 |
|---|---|---|
| `pending` | 待处理 | 已创建，planning 工件尚未全部收敛或尚未过人审门。 |
| `research` | 调研中 | research subtask 在跑或待收敛回 plan。 |
| `active` | 进行中 | 已 confirm，subtask 可经 claim/start 派发。 |
| `check` | 检查中 | 全 subtask done 后进入质量门。 |
| `finishing` | 收尾中 | check 全绿后进入收尾门。 |
| `done` | 已完成 | finish 成功，闭环结束。 |

`pending` / `research` 可往返；`active` 后不退回 `pending`。check 失败是追加修复 subtask 前进式修补，不是状态回滚。

## 命令语义

| 命令 | 源状态 | 目标状态 | 语义 |
|---|---|---|---|
| `skein create <id>` | 无 | `pending` | 建 task 工件。 |
| `skein research <id>` | `pending` | `research` | 发起只读调研。 |
| `skein plan <id>` | `research` | `pending` | 调研全 done 后收敛回 planning。 |
| `skein confirm <id>` | `pending` | `active` | 用户确认后建工作目录并进入执行。 |
| `skein check <id>` | `active` | `check` | 进入质量门。 |
| `skein finishing <id>` | `check` | `finishing` | 占 gate 槽，准备收尾。 |
| `skein finish <id>` | `finishing` | `done` | 合并/销 worktree/标记完成。 |
| `skein archive <id>` | `done` | 归档 | 移入 archive。 |

## 并发池

- `pools.work` 计数 running subtask，不计 task 本身。
- `pools.gate` 计数 `check` / `finishing` task。
- DAG 调度算法见 [dag-scheduling.md](dag-scheduling.md)。
- 状态硬门见 [flow-loop.md §2](flow-loop.md#2-状态先行硬门)。
