# for-redo — redo 操作边界

redo 的起点分流、孤儿复位、`--plan` 行为、复位清单、续跑规则统一见 [flow-loop.md §8](flow-loop.md#8-redo-断点续跑)。本文件只说明 redo 的语义边界。

## 语义

- redo 解的是 session 意外结束后的状态卡死，不是回滚。
- redo 只改 subtask 状态，不删除、不撤销上一轮已产出的文件改动。
- redo 不新增引擎命令；复位用现有 `skein subtask fail` + `skein subtask start` 拼法。
- redo 期间禁止有 agent 在跑；否则可能把活 subtask 当孤儿复位。

## main 保留职责

- 动手前告知孤儿口径和代价。
- 按 [flow-loop.md §8](flow-loop.md#8-redo-断点续跑) 分流 task 当前状态。
- 复位后回传被复位清单，或说明无 running subtask 需复位。
- 分流后移交对应阶段，不在本文件重复 plan/exec/check/finish 流程。

## 状态依据

- task 状态与 redo 起点：[flow-loop.md §1.1](flow-loop.md#11-task-状态)
- subtask 状态与 running 口径：[flow-loop.md §1.2](flow-loop.md#12-subtask-状态)
- active 起点固定复位拼法：[flow-loop.md §8](flow-loop.md#8-redo-断点续跑)
