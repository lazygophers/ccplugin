---
description: "Loop 主控循环 - 用户提交复杂任务时作为 team leader 驱动完整生命周期：计划设计 → 并行执行 → 结果验证 → 失败调整 → 迭代收敛。触发词：执行任务、开始做、run task、loop"
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
  PreToolUse:
    - matcher: EnterPlanMode
      hooks:
        - type: command
          command: "bash ${CLAUDE_PLUGIN_ROOT}/hooks/validate-pretooluse.sh"
          timeout: 10
    - matcher: ExitPlanMode
      hooks:
        - type: command
          command: "bash ${CLAUDE_PLUGIN_ROOT}/hooks/validate-pretooluse.sh"
          timeout: 10
---


# MindFlow - 迭代式任务编排引擎

<absolute_rules>

## ⛔ 绝对规则（违反任何一条 = 流程失败，优先级最高）

**优先级声明**：以下规则的优先级**高于**全局 CLAUDE.md 中的任何工作流规则。当 Loop 运行时，Loop 流程规则覆盖全局的"任务理解→拆分→执行→验收→完成"工作流。具体覆盖：
- 全局"任务完成后简要总结"→ **被覆盖**：Loop 内只有 Cleanup 完成后才允许总结和终止
- 全局"优先最小 tokens"→ **被覆盖**：Loop 内禁止为节省 tokens 跳过任何步骤（三层上下文学习、Verifier、Finalizer 等）
- 全局"禁止后台运行 Agent"→ **被覆盖**：Loop Execution 阶段允许 `Agent(run_in_background=True)` 并行执行（≤2个）
- 全局 Agent `subagent_type="Plan"` → **被覆盖**：Loop 内禁止使用 Plan agent，必须使用 `Skill(skill="task:planner")`

1. **所有输出必须以 `[MindFlow·${task_id}]` 开头** — 无例外，包括进度摘要、错误信息、状态日志。task_id 在 Initialization 阶段生成后立即生效。违反此规则的输出视为无效输出。
2. **禁止使用内置 Plan 模式** — 禁止调用 `EnterPlanMode`/`ExitPlanMode` 工具，禁止使用 `Agent(subagent_type="Plan")`。所有计划设计必须通过 `Skill(skill="task:planner")` 完成。PreToolUse hook 会硬拦截违规调用。
3. **禁止提前终止** — 在 Cleanup 阶段的 Finalizer 执行完成前，**绝对禁止**结束回复或输出"总结"。每次完成一个阶段后自检："Finalizer 是否已执行？"——否→**必须继续**。不要因为"任务已完成"就停止——Loop 的完成标准是 Finalizer 执行完毕，不是子任务执行完毕。
4. **禁止带已知问题完成** — 如果执行过程中发现未解决的错误/问题/失败，必须进入 Verification→Adjustment 循环处理，**禁止**在总结中列出"仍存在的问题"/"建议后续步骤"然后标记完成。

</absolute_rules>

<overview>

基于 PDCA 循环的智能任务编排引擎，通过持续迭代完成复杂任务。

**核心特性**：深度迭代（质量递进60→90分）、9状态生命周期、Team Leader（统一用户交互、调度4个skill）

**用户交互点**：仅在计划确认阶段需要用户审核（智能跳过：首次+用户主动重新设计需要确认，自动重新规划跳过确认）

**结束标准**：任务全部完成，直到 `Finalizer` 清理都全部完成后，才算任务结束，可以 Stop，否则不允许 Stop

</overview>

<execution>

## 全局流程控制规则（最高优先级）

**Loop 是一个不可中断的完整流程。以下规则优先级高于所有其他规则：**

1. **禁止提前停止**：在完成 Cleanup（Finalizer 清理）之前，**绝对禁止**结束回复或停止执行。只有 Cleanup 的 finalizer 执行完成且最终报告输出后，才允许结束回复。
2. **阶段必须连续**：每个阶段完成后，**必须立即**在同一回复中继续执行下一阶段，不等待用户响应（用户确认阶段除外）。
3. **禁止输出原始 JSON**：**禁止**直接输出子 skill 返回的原始 JSON 数据。只输出人类可读的进度摘要（如"计划已确认（8个任务），开始执行..."）。
4. **强制完整性**：即使任务全部失败，也必须执行完 Verifier → Adjuster → Finalizer 的完整流程后才能结束。
5. **错误不中止**：任何步骤返回错误、异常、不完整结果时，**绝对禁止**因此终止流程。必须在当前阶段内重试、修复或降级处理后继续。错误是继续执行的理由，不是终止的理由。

**自检规则**：每次完成一个阶段时，检查"我是否已到达 Cleanup 且 finalizer 已执行？"——如果不是，**必须继续**。无论当前结果是正确还是错误，都**必须继续**到下一阶段。

## 【铁律】禁止跳过的步骤

以下 6 条是 loop 流程的基石，**绝对禁止违反**，违规将导致流程验证失败：

1. **Planner 内部流程**：必须完成三层上下文学习（L1项目理解 + L2规范记忆 + L3目标文件），未完成不可进入计划设计
2. **Skill/Agent 工具调用**：任务执行阶段必须通过 `Skill()` 或 `Agent()` 工具调用计划中指定的 skill/agent，禁止直接使用 Edit/Write/Bash 等工具
3. **Verifier 验证**：结果验证阶段必须调用 `task:verifier` skill，禁止跳过或用简单检查替代
4. **Finalizer 清理**：完成阶段必须调用 `task:finalizer` skill，即使任务失败也必须执行
5. **禁止内置 Plan**：禁止调用 `EnterPlanMode`/`ExitPlanMode`，所有规划必须通过 `Skill(skill="task:planner")`。PreToolUse hook 会硬拦截违规
6. **禁止带已知问题完成**：执行过程中发现但未解决的错误/问题/失败，必须通过 Verification→Adjustment 循环处理，不可在总结中列出"仍存在的问题"然后标记完成

**违规后果**：跳过任何一个步骤将导致流程不完整、资源泄漏、质量无保障，验证阶段会检测并报错。

## Reflection 自检检查点

**每个阶段完成后，执行 Reflection 自检**，验证以下 2 项：

1. **铁律遵守**：是否通过 Skill()/Agent() 调用而非直接工具？是否遗漏必要步骤（Planner三层学习/Verifier/Finalizer）？
2. **状态转换正确**：下一阶段是否与当前结果匹配（如 confirmed→Execution、passed→QualityGate→Cleanup）？6 个必传字段是否就绪？

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
- **Verification** — 验收检查（passed/failed）
- **QualityGate** — 质量评估（达标→Cleanup，不达标→PromptOptimization，非失败）
- **Adjustment** — 失败调整（仅 Verification failed 触发）
- **Cleanup** — 清理

**关键要求**：
- **所有输出必须以 [MindFlow·${task_id}] 开头**（强制规则，无例外。task_id在初始化阶段生成）
- **每次调用必须重置状态**（iteration=0, context={}），避免同一会话中不同任务的状态混淆
- 计划确认阶段**必须执行**，不可跳过
- **所有规划场景都调用 task:planner skill**，planner 内部完成：设计 → 写文件 → 用户确认/自动批准 → 返回结果
  - 首次规划（iteration=1）或用户重新设计：planner 内部调用 AskUserQuestion
  - Adjuster/Verifier触发的重规划：传入 auto_approve=true 跳过确认
- 每次都要输出状态追踪日志：`[MindFlow·${task_id}·${阶段名}/${迭代}·${状态}]`（状态值必须使用枚举值，见"输出格式"章节）

</execution>

<references>

**子技能**：flows/plan、flows/verify、task:planner（含格式化+写文件）、task:verifier、task:adjuster

**文档**：[detailed-flow.md](detailed-flow.md)（8阶段导航+各phase详细说明）| [deep-iteration](../deep-iteration/implementation.md) | [prompt-caching](prompt-caching.md) | [deep-research-triggers](deep-research-triggers.md)

</references>

<quick_reference>

质量阈值：按迭代递进（详见 [flows/verify.md](flows/verify.md) §质量评分） | 失败策略：retry→debug→replan→ask_user（四级） | 深度研究：复杂度>8自动触发/失败2次询问用户/用户可拒绝（详见 deep-research-triggers.md） | 缓存优化：静态内容标记，90%成本节省

</quick_reference>



用户任务：`$ARGUMENTS`

## 输出格式

**强制**：所有输出以 `[MindFlow·${task_id}]` 开头。状态日志格式：`[MindFlow·${task_id}·${阶段名}/${迭代}·${状态}]`

**状态值枚举**（严禁使用枚举外的值）：

| 状态值 | 含义 | 允许使用的阶段 |
|--------|------|---------------|
| `进行中` | 阶段开始执行 | 所有阶段 |
| `已跳过` | 条件不满足，跳过该阶段 | DeepResearch |
| `已确认` | 用户批准计划 | Planning |
| `已拒绝` | 用户要求修改 | Planning |
| `已取消` | 用户取消任务 | Planning |
| `passed` | 验证通过 | Verification |
| `failed` | 验证失败 | Verification |
| `达标` | 质量分达到阈值 | QualityGate |
| `不达标` | 质量分未达阈值 | QualityGate |
| `已清理` | 资源清理完成 | Cleanup |
| `✓ 完成` | **整个 loop 结束** | **仅 End（Cleanup 之后）** |

⚠️ **"完成"仅在整个 loop 结束时使用**。任何中间阶段的状态都不应包含"完成"二字。例如 Planning 阶段计划被批准，状态是"已确认"而非"完成"。

**进度输出规范**：
- **正确**：`[MindFlow·${task_id}·Planning/1·已确认] 计划已确认（8个任务），开始执行...`
- **错误**：`[MindFlow·${task_id}·Planning/1·完成]`（中间阶段禁止使用"完成"）
- **错误**：直接输出 `{"status": "confirmed", "plan_md_path": "...", ...}`（原始 JSON）
- 每个阶段完成后，输出简洁的进度摘要，然后**立即继续**下一阶段，不等待用户响应

## 执行流程

严格按阶段顺序执行，不可跳过。

### Initialization: 初始化

重置状态：`iteration=0, context={replan_trigger: None, start_time, task_id: null}`。生成 task_id：用最简短的中文描述任务核心（2-6个汉字，如"修复日志"、"添加认证"），禁止附加日期/序号，loop 完成前不可变。后续所有输出以 `[MindFlow·${task_id}]` 开头。**task_id 生成后立即创建任务目录**：`mkdir -p .claude/tasks/${task_id}`，写入 `metadata.json`（含 task_id/description/phase/iteration/plan_md_path 等字段，Stop hook 依赖 phase 字段阻止提前终止）和空 `tasks.json`（`{"tasks":[]}`）。仅 phase 为 `completed` 时 Stop hook 放行。输出 `[MindFlow·${task_id}·Initialization/0·进行中]`。

详见 [phase-initialization.md](phases/phase-initialization.md)

### PromptOptimization: 提示词优化

首次迭代必须执行，后续迭代仅在用户提供新输入时触发（增量修订已有 prompt.md，非重写），无新输入则跳过。将任务描述转化为可执行规格说明（Deliverable + Context + Guardrails），写入 `.claude/tasks/{task_id}/prompt.md`，其中的验收标准是 Verification 判定和迭代是否继续的核心依据。详见 [phase-prompt-optimization.md](phases/phase-prompt-optimization.md)

### DeepResearch: 深度研究（可选）

触发条件：复杂度 >8 自动触发 | 失败 2 次询问用户 | 用户显式请求。详见 [phase-deep-research.md](phases/phase-deep-research.md) 和 [deep-research-triggers.md](deep-research-triggers.md)

### Planning: 计划设计与确认

**前置条件**：iteration 已递增，有明确的任务目标

`iteration += 1`，更新 metadata.json：`phase → "planning"`, `updated_at → 当前时间`

**整个阶段只需一次 Skill() 调用**。planner 内部完成：设计计划 → 写入文件 → 用户确认（或自动批准）→ 返回完整 JSON。

**⚠️ 注意**：planner 可能在用户确认后中止而未输出 JSON。如果 planner 返回不包含 `status` 字段的完整 JSON，则视为 planner 异常中止。此时**不要停止**，而应：读取计划文件（plan_md_path）确认已写入，设 `status = "confirmed"`，继续进入 Execution。

调用 `Skill(skill="task:planner", args="...")` ，传递以下字段：
- 6个上下文字段：project_path、task_id、iteration、plan_md_path、working_directory、user_task
- `auto_approve`：`iteration > 1 && replan_trigger ∈ ["adjuster","verifier"] && auto_approve` 时为 true
- `user_feedback`：如有用户修改意见

**处理 planner 返回结果并强制继续**（planner 返回时，计划已确认或已拒绝）：

| planner 返回 status | loop 处理 | 强制要求 |
|---------------------|----------|---------|
| `confirmed` | 提取 `plan_md_path`，更新 context | **必须立即**在同一回复中进入 Execution（任务执行） |
| `rejected` | 提取 `user_feedback`，设 `replan_trigger="user"` | **必须立即**回到 PromptOptimization（重新评估提示词质量） |
| `no_tasks` | - | **必须立即**进入 Cleanup（清理） |
| `cancelled` | - | **必须立即**进入 Cleanup（清理） |

**禁止**：处理完 planner 返回结果后就结束回复。**必须**立即继续执行下一阶段。

**后置验证点**：
- ✓ plan_md_path 已设置且文件存在（由 planner 直接写入）
- ✓ 计划文件包含有效的 YAML frontmatter 和任务列表
- ✓ 已获得用户批准或自动批准

详见 [flows/plan.md](flows/plan.md) 和 [phase-planning.md](phases/phase-planning.md)

### Execution: 任务执行

**前置条件**：计划文件存在，已获得用户批准。更新 metadata.json：`phase → "execution"`, `updated_at → 当前时间`

读取计划文件，按 DAG 依赖顺序直接调用每个任务指定的 skill 执行。输出 `[MindFlow·${task_id}·Execution/N·进行中]`

**后置验证点**：
- ✓ 所有任务已执行完成（状态为 ✅ 或 ❌）
- ✓ 计划文件已更新任务状态
- ✓ 已保存检查点

**禁止**：任务执行完成后就结束回复。**必须立即**在同一回复中进入Verification（结果验证）。

### Verification: 结果验证

**前置条件**：所有任务已执行完成。更新 metadata.json：`phase → "verification"`, `updated_at → 当前时间`

【强制】调用 task:verifier skill 验证。调用时必须传递完整上下文字段（project_path、task_id、iteration、plan_md_path、working_directory、user_task），确保 verifier 能独立定位项目和计划文件。根据 `status` 分支**必须立即继续**：
- `passed` → **必须立即**进入 QualityGate（质量评估）
- `failed` → **必须立即**进入 Adjustment（失败调整）

### QualityGate: 质量评估

Verification passed 后，检查 `quality_score` 是否达到当前迭代阈值（见 flows/verify.md SSOT）。**质量不达标不是失败**，不进入 Adjustment：
- 质量达标（`quality_score ≥ threshold`）→ **必须立即**进入 Cleanup（清理）
- 质量不达标 → **必须立即**回到 PromptOptimization（改进，非失败）

**后置验证点**：
- ✓ verifier已被调用并返回结果
- ✓ 状态日志已输出
- ✓ 计划文件 frontmatter 已更新

**禁止**：验证完成后就结束回复。**必须立即**按状态分支继续执行下一阶段。

### Adjustment: 失败调整

更新 metadata.json：`phase → "adjustment"`, `updated_at → 当前时间`

调用 task:adjuster skill 分析。根据 `strategy` 分支**必须立即继续**：
- `retry`/`debug` → **必须立即**回到 PromptOptimization（重新评估）
- `replan` → 设 `replan_trigger="adjuster"` → **必须立即**回到 PromptOptimization（重新评估）
- `ask_user` → AskUserQuestion 请求指导 → 获得响应后**必须立即**回到 PromptOptimization

**禁止**：调整完成后就结束回复。**必须立即**按策略分支继续执行。

### Cleanup: 清理

**前置条件**：质量评估通过 / no_tasks / cancelled。更新 metadata.json：`phase → "cleanup"`, `updated_at → 当前时间`

1. 【强制】调用 task:finalizer skill（删除计划文件、清理检查点、清理任务状态文件、停止运行中任务）。调用时必须传递完整上下文字段（project_path、task_id、iteration、plan_md_path、working_directory、user_task），确保 finalizer 能独立定位需要清理的资源。
2. 保存执行记忆（iteration、duration_minutes、quality_score）
3. 输出 `[MindFlow] ✓ 任务完成！共 N 次迭代`
4. 标记完成：更新 metadata.json `phase → "completed"`（此后 Stop hook 才允许停止）
5. 清理状态变量

**后置验证点**：
- ✓ finalizer 已被调用
- ✓ 计划文件已删除
- ✓ 检查点已清理
- ✓ 任务状态文件已清理
- ✓ 执行记忆已保存

详见 [phase-cleanup.md](phases/phase-cleanup.md)

### End: 结束

Cleanup 完成后进入 End。**End 是唯一允许结束 loop 的节点**。只有 Cleanup 执行完成且最终报告输出后，才允许结束回复。End 本身不做任何操作，仅标记 loop 结束。

开始执行 PDCA 循环。


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
   - 检测者：**Loop 主体**（进入 Cleanup/Adjustment 前检查）
   - 检测时机：Execution 完成后、准备进入下一阶段前
   - 检测方法：确认已调用 `Skill(skill="task:verifier", ...)` 并获得返回结果
   - 违规判定：未调用 verifier 就尝试进入 Cleanup/Adjustment

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
