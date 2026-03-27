---
description: Loop 计划设计流程 - 深度研究、计划生成、计划确认
model: sonnet
context: fork
user-invocable: false
---

# Loop 计划设计流程

## 范围

Planning阶段：触发深度研究→调用task:planner→格式化计划文档→Plan Mode控制审查流程。adjuster/verifier触发的重规划自动批准。

## 执行流程

### 阶段0：提示词优化（仅iteration=0）

调用 `task:prompt-optimizer` 评估质量(清晰度/完整性/可执行性)。≥8分静默跳过，<8分识别缺失5W1H并提问，<6分触发WebSearch。优化后更新user_task。

### 阶段1：深度研究（可选）

触发条件：第1轮迭代 | 失败2次+ | 质量<阈值-10 | 高复杂度。调用 `deepresearch:deep-research` 研究最佳实践/技术选型/风险。

### 阶段2-4：计划设计与确认

**智能路径选择**：

| 场景 | 条件 | 流程 |
|------|------|------|
| 首次规划 | iteration=1 | Plan模式 |
| 用户重新设计 | replan_trigger="user" | Plan模式 |
| Adjuster自动重规划 | iteration>1, trigger="adjuster" | 直接生成+自动批准 |
| Verifier建议优化 | iteration>1, trigger="verifier" | 直接生成+自动批准 |

**路径A（自动重规划）**：
1. 直接调用 task:planner（含user_feedback如有）
2. 处理planner的问题（AskUserQuestion）
3. 空tasks→skip_execution
4. 调用 task:plan-formatter 格式化并写入文件
5. 自动批准，设置plan_md_path

**路径B（Plan模式）**：
1. EnterPlanMode()
2. 深度研究（如需）
3. 调用 task:planner
4. 处理planner的问题
5. 空tasks→ExitPlanMode→skip_execution
6. 调用 task:plan-formatter 写入文件
7. ExitPlanMode() 请求用户批准
8. 批准→execute | 拒绝→提取反馈(HTML注释/[反馈]/删除线标记)→replan_trigger="user"

**Planner调用参数**：任务目标 + 迭代编号 + user_feedback(如有) + 要求(项目分析/MECE分解/DAG依赖/Agent+Skills分配/可量化验收/≤200字报告)

## 状态转换

- 路径A：生成计划→自动批准→执行 | 空tasks→完成
- 路径B：Plan模式→设计→格式化→用户批准→执行 | 拒绝→提取反馈→重新设计

## 最佳实践

**规划**：MECE分解、DAG依赖(无循环)、原子任务+可量化验收、合理Agent/Skills分配、并行≤2
**执行**：实时监控进度/超时/资源、优先调度Ready任务、混搭CPU/IO密集型
**避免**：过度规划(分析瘫痪)、过早优化(YAGNI)、过度拆分
