---
description: Loop 计划设计流程 - 深度研究、计划生成、计划确认
model: sonnet
context: fork
user-invocable: false
---

# Loop 计划设计流程

## 范围

Planning阶段：触发深度研究→调用task:planner skill（planner自动格式化并写入计划文件）→用户确认（AskUserQuestion）。adjuster/verifier触发的重规划自动批准。

## 配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| auto_approve | false | 是否允许 adjuster/verifier 触发的重规划自动批准。false 时所有重规划都需要用户确认 |

## 执行流程

### 阶段0：提示词优化（仅iteration=0）

调用 `task:prompt-optimizer` skill 评估质量(清晰度/完整性/可执行性)。≥8分静默跳过，<8分识别缺失5W1H并提问，<6分触发WebSearch。优化完成后展示原始提示词 vs 优化后提示词对比，由用户选择：A(使用原始)、B(使用优化)、C(重新优化)。根据用户选择更新user_task。

### 阶段1：深度研究（可选）

触发条件：第1轮迭代 | 失败2次+ | 质量<阈值-10 | 高复杂度。调用 `deepresearch:deep-research` skill 研究最佳实践/技术选型/风险。

### 阶段2-4：计划设计与确认

**智能路径选择**：

| 场景 | 条件 | 流程 |
|------|------|------|
| 首次规划 | iteration=1 | task:planner + 用户确认 |
| 用户重新设计 | replan_trigger="user" | task:planner + 用户确认 |
| Adjuster自动重规划 | iteration>1, trigger="adjuster" | task:planner + (auto_approve ? 自动批准 : 用户确认) |
| Verifier建议优化 | iteration>1, trigger="verifier" | task:planner + (auto_approve ? 自动批准 : 用户确认) |

**路径A（自动重规划）**：
1. 深度研究（如需）
2. 调用 `Skill(skill="task:planner", args="...")` 设计计划，传入6个必传上下文字段（project_path/task_id/iteration/plan_md_path/working_directory/user_task）及user_feedback(如有)。**planner 会自动格式化并写入计划文件**。
3. 处理 planner 返回结果：
   - 有 questions → AskUserQuestion 询问用户
   - tasks 为空 → skip_execution
   - tasks 非空 → 提取 `plan_md_path`，更新 context
4. if auto_approve=true: 自动批准并进入任务执行；else: 调用 `AskUserQuestion(...)` 请求用户批准（按批准判定规则处理）

**路径B（用户确认）**：
1. 深度研究（如需）
2. 调用 `Skill(skill="task:planner", args="...")` 设计计划，传入6个必传上下文字段（project_path/task_id/iteration/plan_md_path/working_directory/user_task）。**planner 会自动格式化并写入计划文件**。
3. 处理 planner 返回结果：
   - 有 questions → AskUserQuestion 询问用户
   - tasks 为空 → skip_execution
   - tasks 非空 → 提取 `plan_md_path`，更新 context
4. 调用 `AskUserQuestion(...)` 展示计划摘要，请求用户批准（按批准判定规则处理）
5. 按判定结果处理：批准→execute | 修改意见→提取user_feedback→replan_trigger="user"→重新规划

**批准判定规则**：只有用户明确选择"批准执行"选项=批准。Other文本输入和其他非批准选项=修改意见，提取为user_feedback，触发replan_trigger="user"回到计划设计阶段重新规划并再次确认。

## 用户反馈循环

当用户通过AskUserQuestion的Other输入或非批准选项提供修改意见时：

1. 提取用户输入文本为 `user_feedback`
2. 设置 `replan_trigger = "user"`
3. `iteration++`，回到计划设计阶段
4. 调用 task:planner skill，将 `user_feedback` 作为附加参数传入
5. 生成新计划 → 再次 AskUserQuestion 请求用户确认
6. **循环直到用户明确选择"批准执行"选项或放弃任务**

**Planner调用参数（6个必传上下文字段）**：

| 字段 | 类型 | 说明 | 来源 |
|------|------|------|------|
| project_path | string | 项目根目录绝对路径 | 初始化阶段确定 |
| task_id | string | 任务唯一标识 | Phase 1生成 |
| iteration | number | 当前迭代轮次 | loop状态变量 |
| plan_md_path | string | 计划文件绝对路径 | 计划设计阶段生成，首次为null |
| working_directory | string | 工作目录 | 等于project_path或子目录 |
| user_task | string | 用户原始任务描述 | 用户输入 |

附加参数：user_feedback(如有) + 要求(项目分析/MECE分解/DAG依赖/Skills分配/可量化验收/≤200字报告)

## 状态转换

- 路径A：task:planner（含格式化写文件）→自动批准→执行 | 空tasks→完成
- 路径B：task:planner（含格式化写文件）→AskUserQuestion用户批准→执行 | 拒绝→提取反馈→重新设计

## 最佳实践

**规划**：MECE分解、DAG依赖(无循环)、原子任务+可量化验收、合理Agent/Skills分配、并行≤2
**执行**：实时监控进度/超时/资源、优先调度Ready任务、混搭CPU/IO密集型
**避免**：过度规划(分析瘫痪)、过早优化(YAGNI)、过度拆分
