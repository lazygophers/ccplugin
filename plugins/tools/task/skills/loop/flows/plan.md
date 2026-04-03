---
description: Loop 计划设计流程 - 深度研究、计划生成、用户确认（全部由 planner 内部完成）
model: sonnet
context: fork
user-invocable: false
---

# Loop 计划设计流程

## 范围

Planning阶段：触发深度研究 → 调用 task:planner skill（planner 内部完成：设计计划 → 格式化写文件 → 用户确认/自动批准）→ 处理返回结果。

**核心设计**：整个阶段只需一次 `Skill(skill="task:planner")` 调用。planner 内部处理所有工作，包括用户确认。Loop 无需链式调用其他工具。

## 配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| auto_approve | false | 是否允许 adjuster/verifier 触发的重规划自动批准 |

## 执行流程

### PromptOptimization：提示词优化

首次迭代必须执行，后续迭代仅在用户提供新输入时触发（增量修订，非重写），无新输入则跳过。流程：调用 prompt-optimizer（TaskDecomposition → ClarificationDialog → SpecGeneration → 写入 prompt.md）→ **loop 执行 UserConfirmation**（AskUserQuestion，用户选择 A确认/B原始/C重新优化）。prompt.md 的验收标准是迭代是否继续的核心依据。

### DeepResearch：深度研究（可选）

触发条件：第1轮迭代 | 失败2次+ | 质量<阈值-10 | 高复杂度。调用 `deepresearch:deep-research` skill 研究最佳实践/技术选型/风险。

### Planning：计划设计与确认（单次调用）

调用 `Skill(skill="task:planner", args="...")`，传入必传字段：

| 字段 | 说明 |
|------|------|
| project_path | 项目根目录绝对路径 |
| task_id | 任务唯一标识 |
| iteration | 当前迭代轮次 |
| plan_md_path | 计划文件绝对路径（首次为null） |
| working_directory | 工作目录 |
| user_task | 用户原始任务描述 |
| auto_approve | 是否自动批准（根据 replan_trigger 和配置决定） |
| user_feedback | 用户修改意见（如有，来自上一轮拒绝） |

**planner 内部完成**：设计计划 → 格式化写文件 → (auto_approve ? 自动返回 : AskUserQuestion用户确认) → 返回结果。

**planner 返回后，loop 读取 metadata.json 的 `result` 字段**：

| result.status | 处理 |
|---------------|------|
| `confirmed` | 设 plan_md_path = `.claude/tasks/{task_id}/plan.md` → save_checkpoint → 进入任务执行 |
| `rejected` | 读取 result.user_feedback → replan_trigger="user" → 回到 PromptOptimization（评估提示词质量） |
| `no_tasks` | 进入完成阶段 |
| `cancelled` | 进入清理（Cleanup） |

## 用户反馈循环

当 planner 返回 `status: "rejected"` 时：

1. 提取 `user_feedback` 字段
2. 设置 `replan_trigger = "user"`
3. 回到 PromptOptimization（重新优化提示词 → 用户确认 → 复杂度评估 → Planning）
4. **循环直到 planner 返回 `confirmed` 或 `cancelled`**

## 状态转换

- confirmed → Execution(任务执行)
- rejected → PromptOptimization（重新评估提示词质量）
- no_tasks → Cleanup(完成)
- cancelled → Cleanup(清理)

## 最佳实践

**规划**：MECE分解、DAG依赖(无循环)、原子任务+可量化验收、合理Agent/Skills分配、并行≤2
**执行**：实时监控进度/超时/资源、优先调度Ready任务、混搭CPU/IO密集型
**避免**：过度规划(分析瘫痪)、过早优化(YAGNI)、过度拆分
