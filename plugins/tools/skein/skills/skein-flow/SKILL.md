---
name: skein-flow
description: SKEIN task 闭环编排器。$1 路由阶段；执行过程唯一真值源在 references/flow-loop.md。
user-invocable: true
argument-hint: "[flow|plan|exec|check|finish|redo] [任务描述/ID] [--plan] (全空=清空全部未完成 task)"
arguments: ["flow|plan|exec|check|finish|redo", "任务描述/ID"]
model: sonnet
effort: medium
---

# skein-flow — task 闭环编排器

`/skein-flow` 编排 SKEIN task 从规划到完成的闭环。**所有执行过程、状态推进、阶段续跑、redo、失败扭转、自愈、停顿/终止规则，统一见 [references/flow-loop.md](references/flow-loop.md)。本文件只做入口路由与资料索引。**

## 参数路由

| `$1` | 阶段 | 权威说明 |
|---|---|---|
| 全空 | flow · 清空模式 | [flow-loop.md §0](references/flow-loop.md#0-参数路由) |
| `flow` / 缺省 / 任务描述 | flow 默认闭环 | [flow-loop.md §3](references/flow-loop.md#3-主循环骨架) |
| `plan` | 仅规划 | [flow-loop.md §4](references/flow-loop.md#4-plan-过程) |
| `exec` | 续执行 | [flow-loop.md §5](references/flow-loop.md#5-exec-过程) |
| `check` | 质量门 | [flow-loop.md §6](references/flow-loop.md#6-check-过程) |
| `finish` | 收尾门 | [flow-loop.md §7](references/flow-loop.md#7-finish-过程) |
| `redo <tid> [--plan]` | 断点续跑 | [flow-loop.md §8](references/flow-loop.md#8-redo-断点续跑) |

## 索引

只列入口必读三份；阶段细节（DAG 拆分与调度、estimate 硬门、根因报告、sediment 判定门）由 flow-loop 和 for-plan 在用到的地方就地引用，不在这里平铺。exec / check / finish 的 agent 边界归 `plugins/tools/skein/agents/*.md`。

- [references/flow-loop.md](references/flow-loop.md) — 执行过程唯一真值源：状态模型与推进命令、状态硬门、主循环骨架与派发载体、四阶段过程、redo、失败扭转。
- [references/flow-loop.md §0.1](references/flow-loop.md#01-作用域边界) — 入口判定：何时建 task、何时 inline 豁免、何时算完成（完成判定见 [§12](references/flow-loop.md#12-终止条件)）。
- [references/for-plan.md](references/for-plan.md) — planning 四件工件（prd / design / contracts / DAG+estimate）的写法。
