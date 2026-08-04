---
name: skein-flow
description: SKEIN task 闭环编排器。$1 路由阶段；执行过程唯一真值源在 references/flow-loop.md。
user-invocable: true
argument-hint: "[flow|plan|exec|check|finish|redo] [任务描述/ID] [--plan] (全空=清空全部未完成 task)"
arguments: ["flow|plan|exec|check|finish|redo", "任务描述/ID"]
model: sonnet
effort: medium
---

args: $1

```
switch $args
case plan:
    use [references/plan.md](references/plan.md)
case redo:
    use [references/redo.md](references/redo.md)
case flow/exec/check/finish/default:
    use [references/flow-loop.md](references/flow-loop.md)
```

`!skein config | jq -r 'if ."worktree.enabled"==true then "以 worktree 的方式执行任务，"+."worktree.root" else "直接在当前 repo 执行任务" end'`
