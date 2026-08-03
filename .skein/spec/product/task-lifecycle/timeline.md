---
title: timeline
category: task-lifecycle
keywords: [timeline,lifecycle,state,状态迁移,append-only,rollback]
status: active
inclusion: auto
anchors: plugins/tools/skein/scripts/skeinlib/task/timeline.py
---

## Task 生命周期时间线

## Task 生命周期时间线

task.json 独立维护 `timeline` 数组，记录 task 和 subtask 的所有状态迁移事件。

### 时间线事件结构

每条事件包含：
- `kind`: "task" | "subtask" —— 事件类型
- `status`: TaskStatus | SubtaskStatus —— 状态值
- `at`: timestamp —— 事件发生时刻 (UTC, 秒级)
- `sid`: string | null —— subtask id (仅 kind=subtask 时有效)
- `note`: string —— 可选备注 (用于人工标注回滚原因等)
- `rollback`: boolean —— 是否为回滚 (新状态序号 ≤ 旧状态序号)

### 序号定义

**Task 生命周期序号** (单调递增代表前进)：
- PENDING: 0 (默认创建状态)
- RESEARCH: 1 (调研阶段)
- ACTIVE: 2 (执行中)
- CHECK: 3 (检查中)
- FINISHING: 4 (收尾中)
- DONE: 5 (最终完成)

**Subtask 序号** (只有三态，隐含一个回退路径)：
- RUNNING: 0 (进行中，唯一的"中间态")
- DONE: 1 (完成)
- FAILED: 1 (失败，与 DONE 同级，唯一的回退是 failed→running 定点重派)

### 记录时机

- `create` 后初始化为 `[PENDING]`
- Task 每次状态迁移时追加事件 (7 处：create/research/plan/confirm/check/finishing/done)
- Subtask 每次状态迁移时追加事件 (3 处：claim/done/fail)
- 追加为纯 append-only，**不改写**历史事件

### 展示用途

1. **时间线展示** —— 详情页按 timeline 渲染六段骨架 (duration/timestamp/status/note)
2. **回滚可视化** —— `rollback=true` 的事件在 UI 高亮显示
3. **状态溯源** —— 调试/审计时追踪状态变化链
4. **预规划阶段** —— 展示时叠加 pre-planning 虚拟阶段 (从 create 到第一个 research/confirm 前的时长)

### 兼容性

- 历史 task (无 timeline 字段) 首次操作时自动 append 当前状态
- 幂等：重复追加同一状态不产生重复事件 (通过 kind + status + sid 唯一性判定)
- 老数据容错：序号未知的状态视为 0，不影响回滚检测
