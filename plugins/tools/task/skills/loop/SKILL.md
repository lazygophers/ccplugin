---
description: Loop 持续执行 - 作为 team leader 执行完整的任务管理循环，包括计划设计、执行、验证、调整
argument-hint: [ 任务目标描述 ]
skills:
  - task:prompt-optimizer
  - task:planner
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

**核心特性**：深度迭代（质量递进60→90分）、9状态生命周期、Team Leader（统一用户交互、调度4个skill）

**用户交互点**：仅在计划确认阶段需要用户审核（智能跳过：首次+用户主动重新设计需要确认，自动重新规划跳过确认）

</overview>

<execution>

## 【铁律】禁止跳过的步骤

以下 4 个步骤是 loop 流程的基石，**绝对禁止跳过**，违规将导致流程验证失败：

1. **Planner 内部流程**：必须完成三层上下文学习（L1项目理解 + L2规范记忆 + L3目标文件），未完成不可进入计划设计
2. **Skill 工具调用**：任务执行阶段必须通过 `Skill()` 工具调用计划中指定的 skill，禁止直接使用 Edit/Write/Bash 等工具
3. **Verifier 验证**：结果验证阶段必须调用 `task:verifier` skill，禁止跳过或用简单检查替代
4. **Finalizer 清理**：完成阶段必须调用 `task:finalizer` skill，即使任务失败也必须执行

**违规后果**：跳过任何一个步骤将导致流程不完整、资源泄漏、质量无保障，验证阶段会检测并报错。

## 独立上下文传递规范

**核心原则**：每次 Skill/Agent 调用都是独立任务，不依赖会话上下文。调用方必须在 args/prompt 中显式传递完整上下文。

**必传字段**：

| 字段 | 类型 | 说明 | 来源 |
|------|------|------|------|
| project_path | string | 项目根目录绝对路径 | 初始化阶段确定 |
| task_id | string | 任务唯一标识 | Phase 1生成 |
| iteration | number | 当前迭代轮次 | loop状态变量 |
| plan_md_path | string | 计划文件绝对路径 | 计划设计阶段生成 |
| working_directory | string | 工作目录 | 等于project_path或子目录 |
| user_task | string | 用户原始任务描述 | 用户输入 |

**规则**：所有 `Skill()` / `Agent()` 调用的 args/prompt 必须包含以上 6 个字段，禁止依赖隐式上下文。遗漏任何字段将导致被调用方无法正确定位项目、任务或工作目录。

## PDCA 流程

**Prepare**（flows/prompt-optimization）→ **Plan**（flows/plan，必须包含计划确认）→ **Do**（按计划中任务的 skill 执行）→ **Check**（flows/verify）→ **Act**（task:adjuster）

**8个阶段**：
1. 初始化
2. 提示词优化（可选）
3. 深度研究（可选）
4. 计划设计与确认
5. 任务执行
6. 结果验证
7. 失败调整（如需）
8. 完成

**关键要求**：
- **所有输出必须以 [MindFlow·${task_id}] 开头**（强制规则，无例外。task_id在初始化阶段生成）
- **每次调用必须重置状态**（iteration=0, context={}），避免同一会话中不同任务的状态混淆
- 计划确认阶段**必须执行**，不可跳过
- **所有规划场景都调用 task:planner skill** → 生成计划 → 根据场景确认
  - 首次规划（iteration=1）或用户重新设计：**必须** AskUserQuestion 请求用户确认
  - Adjuster/Verifier触发的重规划：if auto_approve=true 自动批准，else AskUserQuestion 请求用户确认（默认需确认）
- 每次都要输出状态追踪日志：`[MindFlow·${task_id}·${步骤}/${迭代}·${状态}]`

</execution>

<references>

**子技能**：flows/plan、flows/verify、task:planner（含计划格式化写文件）、task:verifier、task:adjuster

**文档**：[detailed-flow.md](detailed-flow.md)（8阶段导航+各phase详细说明）| [deep-iteration](../deep-iteration/implementation.md) | [prompt-caching](prompt-caching.md) | [deep-research-triggers](deep-research-triggers.md)

</references>

<quick_reference>

质量阈值：60→75→85→90分 | 失败策略：retry→debug→replan→ask_user | 深度研究：复杂度>8自动触发/失败2次询问用户/用户可拒绝（详见 deep-research-triggers.md） | 缓存优化：静态内容标记，90%成本节省

</quick_reference>

<!-- /STATIC_CONTENT -->

<!-- DYNAMIC_CONTENT -->

用户任务：`$ARGUMENTS`

## 输出格式

**强制**：所有输出以 `[MindFlow·${task_id}]` 开头。状态日志格式：`[MindFlow·${task_id}·步骤/迭代·状态]`

## 执行流程

严格按阶段顺序执行，不可跳过。

### 阶段1：初始化

重置状态：`iteration=0, context={replan_trigger: None, start_time, task_id: null}`。生成语义性 task_id（从用户任务提取关键词+日期，如 "loop-fix-20260328"），后续所有输出以 `[MindFlow·${task_id}]` 开头。若检测到相同 task_id，询问用户是否重新开始。输出 `[MindFlow·${task_id}·初始化/0·进行中]`。

详见 [phase-1-initialization.md](phases/phase-1-initialization.md)

### 阶段2：计划设计与确认

**前置条件**：iteration 已递增，有明确的任务目标

`iteration += 1`

**路径选择**（条件：`iteration > 1 && replan_trigger ∈ ["adjuster","verifier"] && auto_approve`）：
- **true → 自动重规划**：执行步骤 1-3（跳过步骤4用户确认）
- **false → 用户确认**：执行步骤 1-4

**批准判定规则**：只有用户明确选择"批准执行"选项=批准。Other文本输入和其他非批准选项=修改意见，提取为user_feedback，触发replan_trigger="user"回到计划设计阶段重新规划并再次确认。

**执行步骤**：

**步骤1**：调用 `Skill(skill="task:planner", args="...")` 设计计划并写入文件。必须传递6个上下文字段（project_path、task_id、iteration、plan_md_path、working_directory、user_task）。planner 会自动格式化计划并写入 `.claude/plans/` 目录，返回结果中包含 `plan_md_path`。

**步骤2**：处理 planner 返回结果：
- 有 questions 字段 → 调用 AskUserQuestion 询问用户
- tasks 为空 → 跳到完成阶段
- tasks 非空 → 从返回结果中提取 `plan_md_path`，更新 `context.plan_md_path`

**步骤3**：调用 `AskUserQuestion(...)` 请求用户批准计划（仅在 auto_approve=false 时执行）

**后置验证点**：
- ✓ plan_md_path 已设置且文件存在（由 planner 写入，无需额外调用 plan-formatter）
- ✓ 计划文件包含有效的 YAML frontmatter 和任务列表
- ✓ 已获得用户批准（首次/用户重新设计）或自动批准（adjuster/verifier触发）

详见 [flows/plan.md](flows/plan.md) 和 [phase-4-planning.md](phases/phase-4-planning.md)

### 阶段3：任务执行

**前置条件**：计划文件存在，已获得用户批准

读取计划文件，按 DAG 依赖顺序直接调用每个任务指定的 skill 执行。输出 `[MindFlow·任务·任务执行/N·进行中]` → `completed`

**后置验证点**：
- ✓ 所有任务已执行完成（状态为 ✅ 或 ❌）
- ✓ 计划文件已更新任务状态
- ✓ 已保存检查点

### 阶段4：结果验证

**前置条件**：所有任务已执行完成

【强制】调用 task:verifier skill 验证。调用时必须传递完整上下文字段（project_path、task_id、iteration、plan_md_path、working_directory、user_task），确保 verifier 能独立定位项目和计划文件。根据 `status` 分支：
- `passed` → 阶段6（完成）
- `suggestions` → 设 `replan_trigger="verifier"` → 阶段2（自动迭代）
- `failed` → 阶段5（失败调整）

**后置验证点**：
- ✓ verifier已被调用并返回结果
- ✓ 状态日志已输出
- ✓ 计划文件 frontmatter 已更新

### 阶段5：失败调整

调用 task:adjuster skill 分析。根据 `strategy` 分支：
- `retry`/`debug` → 阶段3
- `replan` → 设 `replan_trigger="adjuster"` → 阶段2
- `ask_user` → AskUserQuestion 请求指导

### 阶段6：完成清理

**前置条件**：验证通过或用户确认完成

1. 【强制】调用 task:finalizer skill（删除计划文件、清理检查点、停止运行中任务）。调用时必须传递完整上下文字段（project_path、task_id、iteration、plan_md_path、working_directory、user_task），确保 finalizer 能独立定位需要清理的资源。
2. 保存执行记忆（iteration、duration_minutes、quality_score）
3. 输出 `[MindFlow] ✓ 任务完成！共 N 次迭代，耗时 M 分钟`
4. 清理状态变量

**后置验证点**：
- ✓ finalizer 已被调用
- ✓ 计划文件已删除
- ✓ 检查点已清理
- ✓ 执行记忆已保存

详见 [phase-8-finalization.md](phases/phase-8-finalization.md)

开始执行 PDCA 循环。

<!-- /DYNAMIC_CONTENT -->

<violation_handling>

## 流程违规检测与处理

### 检测机制

Loop 在关键阶段设置检查点，自动检测流程违规行为：

1. **Planner 内部流程检测**：
   - 检查点：planner 输出 JSON 前
   - 检测方法：验证是否包含三层上下文学习的证据（读取的文件列表、项目理解摘要）
   - 违规判定：未读取 README/CLAUDE.md，未检查规范和记忆，未读取目标相关文件

2. **Skill 工具调用检测**：
   - 检查点：任务执行阶段，每个任务开始前
   - 检测方法：监控工具调用记录，验证是否使用 `Skill()` 工具
   - 违规判定：直接使用 Edit/Write/Bash 等工具，而非通过 Skill() 调用

3. **Verifier 调用检测**：
   - 检查点：进入阶段6（完成）或阶段7（失败调整）前
   - 检测方法：检查 task:verifier skill 是否被调用
   - 违规判定：未调用 verifier 就进入下一阶段

4. **Finalizer 调用检测**：
   - 检查点：Loop 结束前
   - 检测方法：检查 task:finalizer skill 是否被调用
   - 违规判定：Loop 即将结束但未调用 finalizer

### 处理策略

| 违规类型 | 严重程度 | 处理策略 |
|---------|---------|---------|
| Planner 内部流程不完整 | 高 | 强制回退到计划设计阶段，要求完成三层上下文学习 |
| 未使用 Skill 工具 | 高 | 警告并记录违规，verifier 阶段会检测并报告 |
| 跳过 Verifier | 严重 | 强制回退到结果验证阶段，必须调用 verifier |
| 跳过 Finalizer | 严重 | 阻止 loop 结束，强制调用 finalizer 清理资源 |

### 违规日志

所有违规行为会被记录到短期记忆 `task://sessions/{id}/violations`，包括：
- 违规类型
- 发生时间
- 违规详情
- 处理措施

Finalizer 在清理阶段会读取违规日志，如果存在高严重程度违规，会在最终报告中特别标注。

</violation_handling>
