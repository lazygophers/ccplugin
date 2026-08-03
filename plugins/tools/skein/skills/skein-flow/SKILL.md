---
name: skein-flow
description: SKEIN task 闭环编排器。$1 路由阶段；执行过程唯一真值源在 references/flow-loop.md。
user-invocable: true
argument-hint: "[flow|plan|exec|check|finish|redo] [任务描述/ID] [--plan] (全空=清空全部未完成 task)"
arguments: ["flow|plan|exec|check|finish|redo", "任务描述/ID"]
model: sonnet
effort: medium
---

如果需要以 flow 模式运行，参考 [references/flow-loop.md](references/flow-loop.md)，里面有详细的任务执行各阶段的说明，并确保以此为准推进
如果只需要 plan 模式运行，参考 [references/for-plan.md](references/for-plan.md)，里面有 plan 相关的内容

## 参数路由

| `$1`                     | 阶段            | 权威说明                                                   |
| ------------------------ | --------------- | ---------------------------------------------------------- |
| 全空                     | flow · 清空模式 | [flow-loop.md §0](references/flow-loop.md#0-参数路由)      |
| `flow` / 缺省 / 任务描述 | flow 默认闭环   | [flow-loop.md §3](references/flow-loop.md#3-主循环骨架)    |
| `plan`                   | 仅规划          | [flow-loop.md §4](references/flow-loop.md#4-plan-过程)     |
| `exec`                   | 续执行          | [flow-loop.md §5](references/flow-loop.md#5-exec-过程)     |
| `check`                  | 质量门          | [flow-loop.md §6](references/flow-loop.md#6-check-过程)    |
| `finish`                 | 收尾门          | [flow-loop.md §7](references/flow-loop.md#7-finish-过程)   |
| `redo <tid> [--plan]`    | 断点续跑        | [flow-loop.md §8](references/flow-loop.md#8-redo-断点续跑) |
