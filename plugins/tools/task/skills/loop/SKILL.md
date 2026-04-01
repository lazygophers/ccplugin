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
context: conversation
user-invocable: true
hooks:
  Stop:
    - hooks:
        - type: command
          command: "bash ${CLAUDE_PLUGIN_ROOT}/hooks/validate-stop.sh"
          timeout: 10
---

<!-- STATIC_CONTENT: Cacheable (4800+ tokens) -->

# MindFlow - 迭代式任务编排引擎

<overview>

基于 PDCA 循环的智能任务编排引擎，通过持续迭代完成复杂任务。

**核心特性**：深度迭代（质量递进60→90分）、9状态生命周期、Team Leader（统一用户交互、调度4个skill）

**用户交互点**：仅在计划确认阶段需要用户审核（智能跳过：首次+用户主动重新设计需要确认，自动重新规划跳过确认）

**结束标准**：任务全部完成，直到 `Finalizer` 清理都全部完成后，才算任务结束，可以 Stop，否则不允许 Stop

</overview>

<execution>

## 全局流程控制规则（最高优先级）

**Loop 是一个不可中断的完整流程。以下规则优先级高于所有其他规则：**

1. **禁止提前停止**：在完成 Finalization（Finalizer 清理）之前，**绝对禁止**结束回复或停止执行。只有 Finalization 的 finalizer 执行完成且最终报告输出后，才允许结束回复。
2. **阶段必须连续**：每个阶段完成后，**必须立即**在同一回复中继续执行下一阶段，不等待用户响应（用户确认阶段除外）。
3. **禁止输出原始 JSON**：**禁止**直接输出子 skill 返回的原始 JSON 数据。只输出人类可读的进度摘要（如"计划已确认（8个任务），开始执行..."）。
4. **强制完整性**：即使任务全部失败，也必须执行完 Verifier → Adjuster → Finalizer 的完整流程后才能结束。

**自检规则**：每次完成一个阶段时，检查"我是否已到达 Finalization 且 finalizer 已执行？"——如果不是，**必须继续**。

## 【铁律】禁止跳过的步骤

以下 4 个步骤是 loop 流程的基石，**绝对禁止跳过**，违规将导致流程验证失败：

1. **Planner 内部流程**：必须完成三层上下文学习（L1项目理解 + L2规范记忆 + L3目标文件），未完成不可进入计划设计
2. **Skill/Agent 工具调用**：任务执行阶段必须通过 `Skill()` 或 `Agent()` 工具调用计划中指定的 skill/agent，禁止直接使用 Edit/Write/Bash 等工具
3. **Verifier 验证**：结果验证阶段必须调用 `task:verifier` skill，禁止跳过或用简单检查替代
4. **Finalizer 清理**：完成阶段必须调用 `task:finalizer` skill，即使任务失败也必须执行

**违规后果**：跳过任何一个步骤将导致流程不完整、资源泄漏、质量无保障，验证阶段会检测并报错。

## Reflection 自检检查点

**每个阶段完成后，执行 Reflection 自检**，验证以下 2 项：

1. **铁律遵守**：是否通过 Skill()/Agent() 调用而非直接工具？是否遗漏必要步骤（Planner三层学习/Verifier/Finalizer）？
2. **状态转换正确**：下一阶段是否与当前结果匹配（如 confirmed→Execution、passed→Finalization）？6 个必传字段是否就绪？

**规则**：
- 自检最多执行 1 次，不循环
- 发现问题时：在当前阶段内修复后继续（不回退）
- 发现违规时输出 `[MindFlow·${task_id}·Reflection] 检测到：{问题描述}，已修复`

## 独立上下文传递规范

**核心原则**：每次 Skill/Agent 调用都是独立任务，不依赖会话上下文。调用方必须在 args/prompt 中显式传递完整上下文。

**必传字段**：

| 字段 | 类型 | 说明 | 来源 |
|------|------|------|------|
| project_path | string | 项目根目录绝对路径 | 初始化阶段确定 |
| task_id | string | 任务唯一标识 | Initialization 阶段生成 |
| iteration | number | 当前迭代轮次 | loop状态变量 |
| plan_md_path | string | 计划文件绝对路径 | 计划设计阶段生成 |
| working_directory | string | 工作目录 | 等于project_path或子目录 |
| user_task | string | 用户原始任务描述 | 用户输入 |

**规则**：所有 `Skill()` / `Agent()` 调用的 args/prompt 必须包含以上 6 个字段，禁止依赖隐式上下文。遗漏任何字段将导致被调用方无法正确定位项目、任务或工作目录。

**调用前自检**（每次 Skill/Agent 调用前必须执行）：
- ✓ project_path 非空且为绝对路径
- ✓ task_id 非空（Initialization 阶段已生成）
- ✓ iteration ≥ 1（已递增）
- ✓ plan_md_path 非空且文件存在（Planning 阶段后）
- ✓ working_directory 非空且目录存在
- ✓ user_task 非空（用户原始输入）
- 缺失任何字段 → 停止调用，在当前阶段内补全后重试

## PDCA 流程

**Prepare**（flows/prompt-optimization）→ **Plan**（flows/plan，必须包含计划确认）→ **Do**（按计划中任务的 skill 执行）→ **Check**（flows/verify）→ **Act**（task:adjuster）

**8个阶段**（语义化命名，非严格顺序）：
- **Initialization** — 初始化
- **PromptOptimization** — 提示词优化（可选）
- **DeepResearch** — 深度研究（可选）
- **Planning** — 计划设计与确认
- **Execution** — 任务执行
- **Verification** — 结果验证
- **Adjustment** — 失败调整（条件触发）
- **Finalization** — 完成清理

**关键要求**：
- **所有输出必须以 [MindFlow·${task_id}] 开头**（强制规则，无例外。task_id在初始化阶段生成）
- **每次调用必须重置状态**（iteration=0, context={}），避免同一会话中不同任务的状态混淆
- 计划确认阶段**必须执行**，不可跳过
- **所有规划场景都调用 task:planner skill**，planner 内部完成：设计 → 写文件 → 用户确认/自动批准 → 返回结果
  - 首次规划（iteration=1）或用户重新设计：planner 内部调用 AskUserQuestion
  - Adjuster/Verifier触发的重规划：传入 auto_approve=true 跳过确认
- 每次都要输出状态追踪日志：`[MindFlow·${task_id}·${步骤}/${迭代}·${状态}]`

</execution>

<references>

**子技能**：flows/plan、flows/verify、task:planner（含格式化+写文件）、task:verifier、task:adjuster

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

**进度输出规范**：
- **正确**：`[MindFlow·${task_id}] 计划已确认（8个任务），开始执行...`（人类可读摘要）
- **错误**：直接输出 `{"status": "confirmed", "plan_md_path": "...", ...}`（原始 JSON）
- 每个阶段完成后，输出简洁的进度摘要，然后**立即继续**下一阶段，不等待用户响应

## 执行流程

严格按阶段顺序执行，不可跳过。

### Initialization: 初始化

重置状态：`iteration=0, context={replan_trigger: None, start_time, task_id: null}`。生成语义性 task_id（从用户任务提取关键词+日期，如 "loop-fix-20260328"），后续所有输出以 `[MindFlow·${task_id}]` 开头。若检测到相同 task_id，询问用户是否重新开始。输出 `[MindFlow·${task_id}·初始化/0·进行中]`。

详见 [phase-initialization.md](phases/phase-initialization.md)

### PromptOptimization: 提示词优化（可选）

仅首次迭代（iteration=0）时评估。质量 ≥8 分静默跳过，<8 分使用 5W1H 框架澄清需求。详见 [phase-prompt-optimization.md](phases/phase-prompt-optimization.md)

### DeepResearch: 深度研究（可选）

触发条件：复杂度 >8 自动触发 | 失败 2 次询问用户 | 用户显式请求。详见 [phase-deep-research.md](phases/phase-deep-research.md) 和 [deep-research-triggers.md](deep-research-triggers.md)

### Planning: 计划设计与确认

**前置条件**：iteration 已递增，有明确的任务目标

`iteration += 1`

**整个阶段只需一次 Skill() 调用**。planner 内部完成：设计计划 → 写入文件 → 用户确认（或自动批准）→ 返回结果。

调用 `Skill(skill="task:planner", args="...")` ，传递以下字段：
- 6个上下文字段：project_path、task_id、iteration、plan_md_path、working_directory、user_task
- `auto_approve`：`iteration > 1 && replan_trigger ∈ ["adjuster","verifier"] && auto_approve` 时为 true
- `user_feedback`：如有用户修改意见

**处理 planner 返回结果并强制继续**（planner 返回时，计划已确认或已拒绝）：

| planner 返回 status | loop 处理 | 强制要求 |
|---------------------|----------|---------|
| `confirmed` | 提取 `plan_md_path`，更新 context | **必须立即**在同一回复中进入 Execution（任务执行） |
| `rejected` | 提取 `user_feedback`，设 `replan_trigger="user"` | **必须立即**回到 Planning |
| `no_tasks` | - | **必须立即**跳到 Finalization（完成清理） |
| `cancelled` | - | **必须立即**跳到 Finalization（完成清理） |

**禁止**：处理完 planner 返回结果后就结束回复。**必须**立即继续执行下一阶段。

**后置验证点**：
- ✓ plan_md_path 已设置且文件存在（由 planner 直接写入）
- ✓ 计划文件包含有效的 YAML frontmatter 和任务列表
- ✓ 已获得用户批准或自动批准

详见 [flows/plan.md](flows/plan.md) 和 [phase-planning.md](phases/phase-planning.md)

### Execution: 任务执行

**前置条件**：计划文件存在，已获得用户批准

读取计划文件，按 DAG 依赖顺序直接调用每个任务指定的 skill 执行。输出 `[MindFlow·任务·任务执行/N·进行中]` → `completed`

**后置验证点**：
- ✓ 所有任务已执行完成（状态为 ✅ 或 ❌）
- ✓ 计划文件已更新任务状态
- ✓ 已保存检查点

**禁止**：任务执行完成后就结束回复。**必须立即**在同一回复中进入Verification（结果验证）。

### Verification: 结果验证

**前置条件**：所有任务已执行完成

【强制】调用 task:verifier skill 验证。调用时必须传递完整上下文字段（project_path、task_id、iteration、plan_md_path、working_directory、user_task），确保 verifier 能独立定位项目和计划文件。根据 `status` 分支**必须立即继续**：
- `passed` → **必须立即**进入 Finalization（完成清理）
- `suggestions` → 设 `replan_trigger="verifier"` → **必须立即**回到Planning（自动迭代）
- `failed` → **必须立即**进入Adjustment（失败调整）

**后置验证点**：
- ✓ verifier已被调用并返回结果
- ✓ 状态日志已输出
- ✓ 计划文件 frontmatter 已更新

**禁止**：验证完成后就结束回复。**必须立即**按状态分支继续执行下一阶段。

### Adjustment: 失败调整

调用 task:adjuster skill 分析。根据 `strategy` 分支**必须立即继续**：
- `retry`/`debug` → **必须立即**回到Execution（任务执行）
- `replan` → 设 `replan_trigger="adjuster"` → **必须立即**回到 Planning
- `ask_user` → AskUserQuestion 请求指导 → 获得响应后**必须立即**继续

**禁止**：调整完成后就结束回复。**必须立即**按策略分支继续执行。

### Finalization: 完成清理

**前置条件**：验证通过或用户确认完成

1. **【强制】更新任务状态文件**：在调用 finalizer 之前，**必须先**更新 `.claude/tasks/{task_id}/status.json`：
   - `status` → `"completed"`（验证通过）或 `"failed"`（最终失败）
   - `phase` → `"finalization"`
   - `updated_at` → 当前时间
   - `quality_score` → 验证阶段的最终评分
   - **此步骤不可跳过**，否则下次 loop 初始化会误判为"前一个任务未完成"
2. 【强制】调用 task:finalizer skill（删除计划文件、清理检查点、停止运行中任务）。调用时必须传递完整上下文字段（project_path、task_id、iteration、plan_md_path、working_directory、user_task），确保 finalizer 能独立定位需要清理的资源。
3. 保存执行记忆（iteration、duration_minutes、quality_score）
4. 输出 `[MindFlow] ✓ 任务完成！共 N 次迭代，耗时 M 分钟`
5. 清理状态变量

**后置验证点**：
- ✓ `.claude/tasks/{task_id}/status.json` status 为 `completed` 或 `failed`
- ✓ finalizer 已被调用
- ✓ 计划文件已删除
- ✓ 检查点已清理
- ✓ 执行记忆已保存

详见 [phase-finalization.md](phases/phase-finalization.md)

**Finalization 是唯一允许结束 loop 的阶段**。只有 finalizer 执行完成且最终报告输出后，才允许结束回复。

开始执行 PDCA 循环。

<!-- /DYNAMIC_CONTENT -->

<violation_handling>

## 流程违规检测与处理

### 检测机制

Loop 在关键阶段设置检查点，自动检测流程违规行为：

1. **Planner 内部流程检测**：
   - 检测者：**Planner 自检**（planner 在输出 JSON 前自行验证）
   - 检测时机：planner 返回结果前
   - 检测方法：planner 在 report 中声明已完成 L1/L2/L3（如"已读取 README.md、CLAUDE.md、目标文件"）
   - 违规判定：report 中无三层学习证据

2. **Skill/Agent 工具调用检测**：
   - 检测者：**Reflection 自检**（每个阶段完成后的 Reflection 检查点）
   - 检测时机：Execution 阶段每个任务完成后
   - 检测方法：回顾本阶段是否通过 Skill()/Agent() 调用，而非直接 Edit/Write/Bash
   - 违规判定：发现直接工具调用，输出 Reflection 违规日志

3. **Verifier 调用检测**：
   - 检测者：**Loop 主体**（进入 Finalization/Adjustment 前检查）
   - 检测时机：Execution 完成后、准备进入下一阶段前
   - 检测方法：确认已调用 `Skill(skill="task:verifier", ...)` 并获得返回结果
   - 违规判定：未调用 verifier 就尝试进入 Finalization/Adjustment

4. **Finalizer 调用检测**：
   - 检测者：**Loop 主体**（Loop 结束前检查）
   - 检测时机：准备输出最终完成消息前
   - 检测方法：确认已调用 `Skill(skill="task:finalizer", ...)` 并获得返回结果
   - 违规判定：Loop 即将结束但未调用 finalizer

### 处理策略

| 违规类型 | 严重程度 | 处理策略 |
|---------|---------|---------|
| Planner 内部流程不完整 | 高 | 强制回退到计划设计阶段，要求完成三层上下文学习 |
| 未使用 Skill/Agent 工具 | 高 | 警告并记录违规，verifier 阶段会检测并报告 |
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
