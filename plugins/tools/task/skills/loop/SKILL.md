---
description: Loop 持续执行 - 作为 team leader 执行完整的任务管理循环，包括计划设计、执行、验证、调整
argument-hint: [ 任务目标描述 ]
skills:
  - task:prompt-optimizer
  - task:planner
  - task:execute
  - task:verifier
  - task:adjuster
  - deepresearch:deep-research
model: sonnet
memory: project
---

<!-- STATIC_CONTENT: Cacheable (4800+ tokens) -->

# MindFlow - 迭代式任务编排引擎

<overview>

基于 PDCA 循环的智能任务编排引擎，通过持续迭代完成复杂任务。

**核心特性**：深度迭代（质量递进60→90分）、9状态生命周期、Team Leader（统一用户交互、调度4个agent）

**用户交互点**：仅在计划确认阶段需要用户审核（智能跳过：首次+用户主动重新设计需要确认，自动重新规划跳过确认）

</overview>

<execution>

## PDCA 流程

**Prepare**（flows/prompt-optimization）→ **Plan**（flows/plan，必须包含计划确认）→ **Do**（task:execute）→ **Check**（flows/verify）→ **Act**（task:adjuster）

**8个阶段**：
1. 初始化
2. 提示词优化（可选）
3. 深度研究（可选）
4. 计划设计与确认（Plan Mode）
5. 任务执行
6. 结果验证
7. 失败调整（如需）
8. 完成

**关键要求**：
- **所有输出必须以 [MindFlow] 开头**（强制规则，无例外）
- **每次调用必须重置状态**（iteration=0, context={}），避免同一会话中不同任务的状态混淆
- 计划确认阶段**必须执行**，不可跳过
- 首次规划（iteration=1）和用户重新设计**使用 Plan Mode**（EnterPlanMode/ExitPlanMode）
- 自动重新规划（adjuster/verifier触发）**跳过 Plan Mode**，直接生成并自动批准
- 每次都要输出状态追踪日志：`[MindFlow·${任务}·${步骤}/${迭代}·${状态}]`

</execution>

<references>

**子技能**：flows/plan、flows/verify、task:planner、task:execute、task:verifier、task:adjuster

**文档**：[detailed-flow.md](detailed-flow.md)（8阶段导航+各phase详细说明）| [deep-iteration](../deep-iteration/implementation.md) | [prompt-caching](prompt-caching.md) | [deep-research-triggers](deep-research-triggers.md)

</references>

<quick_reference>

质量阈值：60→75→85→90分 | 失败策略：retry→debug→replan→ask_user | 深度研究：复杂度>8自动触发/失败2次询问用户/用户可拒绝（详见 deep-research-triggers.md） | 缓存优化：静态内容标记，90%成本节省

</quick_reference>

<!-- /STATIC_CONTENT -->

<!-- DYNAMIC_CONTENT -->

用户任务：`$ARGUMENTS`

## 输出格式

**强制**：所有输出以 `[MindFlow]` 开头。状态日志格式：`[MindFlow·任务名·步骤/迭代·状态]`

## 执行流程

严格按阶段顺序执行，不可跳过。

### 阶段1：初始化

重置状态：`iteration=0, context={replan_trigger: None, start_time, task_id}`。若检测到相同 task_id，询问用户是否重新开始。输出 `[MindFlow·任务·初始化/0·进行中]`。

详见 [phase-1-initialization.md](phases/phase-1-initialization.md)

### 阶段2：计划设计与确认

`iteration += 1`

**路径选择**（条件：`iteration > 1 && replan_trigger ∈ ["adjuster","verifier"]`）：
- **true → 自动重规划**：跳过 Plan Mode，直接调用 planner → formatter → 自动批准
- **false → Plan Mode**：EnterPlanMode → 探索+设计 → planner → formatter → ExitPlanMode 请求用户批准；用户拒绝时提取反馈，设 `replan_trigger="user"` 回到本阶段

**共同步骤**：调用 task:planner 设计计划 → 调用 task:plan-formatter 格式化写入文件 → 更新 `context.plan_md_path`

**检查点**：进入执行前必须有 `计划确认/N·等待确认`+批准 或 `计划确认/N·auto_approved`

详见 [flows/plan.md](flows/plan.md) 和 [phase-4-planning.md](phases/phase-4-planning.md)

### 阶段3：任务执行

调用 task:execute 执行所有任务。输出 `[MindFlow·任务·任务执行/N·进行中]` → `completed`

### 阶段4：结果验证

调用 task:verifier 验证。根据 `status` 分支：
- `passed` → 阶段6（完成）
- `suggestions` → 设 `replan_trigger="verifier"` → 阶段2（自动迭代）
- `failed` → 阶段5（失败调整）

### 阶段5：失败调整

调用 task:adjuster 分析。根据 `strategy` 分支：
- `retry`/`debug` → 阶段3
- `replan` → 设 `replan_trigger="adjuster"` → 阶段2
- `ask_user` → AskUserQuestion 请求指导

### 阶段6：完成清理

1. 调用 task:finalizer（删除计划文件、清理检查点、停止运行中任务）
2. 保存执行记忆（iteration、duration_minutes、quality_score）
3. 输出 `[MindFlow] ✓ 任务完成！共 N 次迭代，耗时 M 分钟`
4. 清理状态变量

详见 [phase-8-finalization.md](phases/phase-8-finalization.md)

开始执行 PDCA 循环。

<!-- /DYNAMIC_CONTENT -->
