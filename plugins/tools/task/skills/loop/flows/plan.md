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

### 阶段0：提示词优化（仅iteration=0）

调用 `task:prompt-optimizer` skill 评估质量(清晰度/完整性/可执行性)。≥8分静默跳过，<8分识别缺失5W1H并提问，<6分触发WebSearch。优化完成后展示原始提示词 vs 优化后提示词对比，由用户选择：A(使用原始)、B(使用优化)、C(重新优化)。根据用户选择更新user_task。

### 阶段1：深度研究（可选）

触发条件：第1轮迭代 | 失败2次+ | 质量<阈值-10 | 高复杂度。调用 `deepresearch:deep-research` skill 研究最佳实践/技术选型/风险。

### 阶段2：计划设计与确认（单次调用）

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

**处理 planner 返回结果**：

| status | 处理 |
|--------|------|
| `confirmed` | 提取 plan_md_path → save_checkpoint → 进入任务执行 |
| `rejected` | 提取 user_feedback → replan_trigger="user" → iteration++ → 重新调用 planner |
| `no_tasks` | 进入完成阶段 |
| `cancelled` | 进入完成阶段 |

## 用户反馈循环

当 planner 返回 `status: "rejected"` 时：

1. 提取 `user_feedback` 字段
2. 设置 `replan_trigger = "user"`
3. `iteration++`，重新调用 `Skill(skill="task:planner")`，将 `user_feedback` 传入
4. **循环直到 planner 返回 `confirmed` 或 `cancelled`**

## 状态转换

- confirmed → Phase 5(任务执行)
- rejected → 重新调用 planner（带 user_feedback）
- no_tasks / cancelled → Phase 8(完成)

## 最佳实践

**规划**：MECE分解、DAG依赖(无循环)、原子任务+可量化验收、合理Agent/Skills分配、并行≤2
**执行**：实时监控进度/超时/资源、优先调度Ready任务、混搭CPU/IO密集型
**避免**：过度规划(分析瘫痪)、过早优化(YAGNI)、过度拆分
