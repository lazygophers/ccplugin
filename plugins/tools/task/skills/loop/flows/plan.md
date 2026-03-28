---
description: Loop 计划设计流程 - 深度研究、计划生成、计划确认
model: sonnet
context: fork
user-invocable: false
---

# Loop 计划设计流程

## 范围

Planning阶段：触发深度研究→调用task:planner skill→格式化计划文档→用户确认（AskUserQuestion）。adjuster/verifier触发的重规划自动批准。

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
| Adjuster自动重规划 | iteration>1, trigger="adjuster" | 直接生成+（auto_approve ? 自动批准 : 用户确认） |
| Verifier建议优化 | iteration>1, trigger="verifier" | 直接生成+（auto_approve ? 自动批准 : 用户确认） |

**路径A（自动重规划）**：
1. 直接调用 task:planner skill，传入6个必传上下文字段（project_path/task_id/iteration/plan_md_path/working_directory/user_task）及user_feedback(如有)
2. 处理planner的问题（AskUserQuestion）
3. 空tasks→skip_execution
4. 调用 task:plan-formatter skill 格式化并写入文件
5. if auto_approve: 自动批准；else: AskUserQuestion 请求用户批准（同路径B步骤6-7）

**路径B（用户确认）**：
1. 深度研究（如需）
2. 调用 task:planner skill，传入6个必传上下文字段（project_path/task_id/iteration/plan_md_path/working_directory/user_task）
3. 处理planner的问题
4. 空tasks→skip_execution
5. 调用 task:plan-formatter skill 写入文件
6. AskUserQuestion 展示计划摘要，请求用户批准
7. 批准→execute | 拒绝→提取反馈→replan_trigger="user"

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

- 路径A：生成计划→自动批准→执行 | 空tasks→完成
- 路径B：task:planner skill→格式化→AskUserQuestion用户批准→执行 | 拒绝→提取反馈→重新设计

## 最佳实践

**规划**：MECE分解、DAG依赖(无循环)、原子任务+可量化验收、合理Agent/Skills分配、并行≤2
**执行**：实时监控进度/超时/资源、优先调度Ready任务、混搭CPU/IO密集型
**避免**：过度规划(分析瘫痪)、过早优化(YAGNI)、过度拆分
