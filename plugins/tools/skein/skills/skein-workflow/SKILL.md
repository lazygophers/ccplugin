---
name: skein-workflow
description: SKEIN 流程规则单一真值源。task/subtask 状态机、状态先行铁律、DAG 调度、subtask 操作、worktree 约定、回退协议、优先级打分制 — 所有流程相关的全局规则都在这里，其他 skill 按需引用，不重复写
user-invocable: false
---

# SKEIN 流程规则 — 单一真值源 (Single Source of Truth)

**本 skill 是 skein 体系所有流程规则的唯一标准。其他 skill (flow/plan/exec/check/finish 等) 涉及流程规则时，只引用本 skill 的对应 reference，不自行定义，避免同一套规则在多处写很多次导致漂移。**

## 索引：按主题取规则

需要哪块规则就读哪块 reference，不用全量加载。

| 主题 | reference 文件 | 何时需要读 |
|------|---------------|-----------|
| **Task 状态机** | [references/task-state-machine.md](references/task-state-machine.md) | 涉及 task 状态流转、状态合法性判断、状态切换命令 |
| **Subtask 状态机** | [references/subtask-state-machine.md](references/subtask-state-machine.md) | 涉及 subtask 状态、claim/start/done/fail 操作 |
| **状态先行铁律** | [references/state-before-action.md](references/state-before-action.md) | 任何对 task/subtask 执行操作前 (硬门·STOP) |
| **DAG 调度算法** | [references/dag-scheduling.md](references/dag-scheduling.md) | 任务调度、依赖解析、并发控制、就绪判定 |
| **Subtask 操作规范** | [references/subtask-operations.md](references/subtask-operations.md) | 新增/自愈/修复/并入 subtask |
| **Worktree 约定** | [references/worktree-convention.md](references/worktree-convention.md) | 工作目录定位、worktree vs 原地模式、切换 |
| **回退协议** | [references/rollback-protocol.md](references/rollback-protocol.md) | 失败/冲突时回 planning 重确认的标准流程 |
| **优先级打分制** | [references/priority-scale.md](references/priority-scale.md) | 优先级 0-10 打分规则、等级映射、排序逻辑 |

## 使用方式

其他 skill 在 SKILL.md 中声明本 skill 为依赖，在需要对应规则的章节用一句「参见 skein-workflow/references/xxx.md」即可，不再重复定义。

**原则：流程规则只在本 skill 写一次，其他地方只引用。改规则只改本 skill。**
