# Observability Implementation Guide

## 采集流程

| 阶段 | 时机 | 操作 |
|------|------|------|
| 初始化 | Loop启动 | 创建MetricsCollector，加载预算配置 |
| 迭代开始 | Planning开始 | record_iteration_start(iteration) |
| 调用前后 | Agent/Skill调用 | record_call_start/end（可用装饰器自动化） |
| 任务前后 | Execution阶段 | record_task_start/end(task_id, status) |
| 迭代结束 | Verification完成 | aggregate_iteration → 输出摘要 → 预算检查(>80%预警，超支询问用户) |
| Loop完成 | Finalization | generate_cost_report → 输出报告 → 持久化到metrics.json |

## 配置

`.claude/task.local.md` YAML 配置：

| 项 | 默认值 | 说明 |
|----|--------|------|
| enabled | true | 启用可观测性 |
| budget_limit_usd | null | 预算上限(USD) |
| budget_warning_threshold | 0.80 | 预警阈值 |
| budget_exceed_behavior | ask_user | 超支行为(ask_user/continue/abort) |
| persist_metrics | true | 持久化指标 |
| metrics_path | .claude/plans/{task_hash}/metrics.json | 存储路径 |

## MetricsCollector API

| 方法 | 参数 | 说明 |
|------|------|------|
| set_budget_limit | limit_usd | 设置预算 |
| record_iteration_start | iteration | 记录迭代开始 |
| record_call_start | type,name,prompt → context | Agent/Skill调用开始 |
| record_call_end | call_context,result | 调用结束(提取usage tokens) |
| record_task_start | task_id → context | 任务开始 |
| record_task_end | task_context,status | 任务结束 |
| aggregate_iteration | iteration → metrics | 聚合迭代指标 |
| get_cumulative_cost | → float | 累计成本 |
| generate_cost_report | → dict | 生成报告(参见cost-report.md) |

## 集成点

4个集成点：初始化阶段(创建collector+设预算) → 计划设计开始(record_iteration_start) → 验证完成(aggregate+预算检查) → 完成阶段(generate_cost_report+持久化)
