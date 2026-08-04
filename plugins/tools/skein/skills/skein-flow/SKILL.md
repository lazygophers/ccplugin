---
name: skein-flow
description: SKEIN task 闭环编排器。$1 路由阶段；执行过程唯一真值源在 references/flow-loop.md。
user-invocable: true
argument-hint: "[flow|plan|exec|check|finish|redo] [任务描述/ID] [--plan] (全空=清空全部未完成 task)"
arguments: ["flow|plan|exec|check|finish|redo", "任务描述/ID"]
model: sonnet
effort: medium
---

如果需要以 flow 模式运行（默认模式），参考 [references/flow-loop.md](references/flow-loop.md)，里面有详细的任务执行各阶段的说明，并确保以此为准推进
如果只需要 plan 模式运行，参考 [references/plan.md](references/plan.md)，里面有 plan 相关的内容
如果是 redo 模式运行，参考 [references/for-reloopdo.md](references/for-loop.md) ，重新调度正在执行的任务
