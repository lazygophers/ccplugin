# Subtask 状态机

subtask 状态落盘值为英文；中文只用于展示。调度循环、自愈、redo 复位统一见 [flow-loop.md](flow-loop.md)。本文件只保留状态与命令语义索引。

## 状态

| 落盘值 | 展示名 | 占 `pools.work` | 含义 |
|---|---|---|---|
| `pending` | 待处理 | 否 | 已登记，等待 depends_on 全 done 和 claim/start。 |
| `running` | 运行中 | 是 | 已认领，占槽，executor 在执行。 |
| `done` | 已完成 | 否 | 执行动作完成，释放槽；正式验收归 check。 |
| `failed` | 失败 | 否 | 执行失败，释放槽，可重启或补修复 subtask。 |

## 命令语义

| 命令 | 源状态 | 目标状态 | 语义 |
|---|---|---|---|
| `skein subtask add <tid> <sid>` | 无 | `pending` | 新增 subtask，参数表见 [subtask-operations.md](subtask-operations.md)。 |
| `skein claim exec` | ready `pending` | `running` | 全局按 DAG 与槽位批量认领。 |
| `skein subtask claim <tid>` | ready `pending` | `running` | 单 task 内批量认领。 |
| `skein subtask start <tid> <sid>` | `pending` / `failed` | `running` | 单个启动或失败重启。 |
| `skein subtask done <tid> <sid>` | `running` | `done` | 标执行完成。 |
| `skein subtask fail <tid> <sid>` | `running` | `failed` | 标执行失败。 |
| `skein subtask check <tid> <sid>` | 任意 | 不变 | check 阶段标记验收项进度。 |

## 调度相关

- ready 判定、排序、池计数见 [dag-scheduling.md](dag-scheduling.md)。
- 未 claim/start 禁派 executor，见 [flow-loop.md §2](flow-loop.md#2-状态先行硬门)。
- `running` 孤儿复位口径见 [flow-loop.md §8](flow-loop.md#8-redo-断点续跑)。
