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

## 阶段作业手册

这些文件只保留 planning 的局部边界；exec / check / finish 的 agent 边界归对应 `plugins/tools/skein/agents/*.md`，redo 全流程见 [flow-loop.md §8](references/flow-loop.md#8-redo-断点续跑)：

- [references/for-plan.md](references/for-plan.md) — planning 产物职责。

## 通用规则索引

- [references/flow-loop.md](references/flow-loop.md) — 执行过程唯一真值源：状态模型与推进命令、状态硬门、主循环骨架与派发载体、四阶段过程、redo、失败扭转。
- [references/scope-boundary.md](references/scope-boundary.md) — 何时建 task、何时 inline 豁免。
- [references/dag-scheduling.md](references/dag-scheduling.md) — subtask 怎么拆、依赖怎么挂、落盘模板；ready 判定、排序、双池、claim 命令族。
- [references/estimate-gate.md](references/estimate-gate.md) — estimate 硬门。
- [references/sediment-protocol.md](references/sediment-protocol.md) — finish 后沉淀。
- [references/root-cause-protocol.md](references/root-cause-protocol.md) — 反复失败后的根因报告格式。
