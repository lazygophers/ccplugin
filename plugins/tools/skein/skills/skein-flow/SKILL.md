---
name: skein-flow
description: "SKEIN task 闭环编排器。$1 路由阶段；$1=plan 或含 --plan 时路由到 skein-plan skill；$1=redo 时路由到 skein-redo skill；执行过程唯一真值源在 references/flow-loop.md。"
user-invocable: true
argument-hint: "[flow|plan|exec|check|finish|redo] [任务描述/ID] [--plan] (全空=清空全部未完成 task; plan/--plan=路由 skein-plan; redo=路由 skein-redo)"
arguments: ["exec|check|finish", "任务描述/ID"]
model: sonnet
effort: medium
context: fork
---

args: $1

```
switch $args
case plan:
    路由到 skein-plan: Skill(skill='skein:skein-plan', args=<剩余参数>)
case redo:
    路由到 skein-redo: Skill(skill='skein:skein-redo', args=<剩余参数>)
case flow/exec/check/finish/default:
    use [references/flow-loop.md](references/flow-loop.md)
```

参数含 `--plan` 时同 `case plan` — 路由到 skein-plan。
