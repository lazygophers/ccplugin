---
description: 可观测性技能 - 实时收集性能指标、成本指标、质量指标，生成成本报告和优化建议
model: sonnet
context: fork
user-invocable: false
---

<!-- STATIC_CONTENT: Cacheable -->

# Skills(task:observability) - 可观测性规范

## 概述

在 task:loop 执行中实时采集和分析指标。零侵入自动采集，实时可见，提供具体优化建议。

**文档**：[implementation-guide.md](./implementation-guide.md) | [metrics-collector.md](./metrics-collector.md) | [cost-report.md](./cost-report.md)

## 指标体系

| 类别 | 关键指标 |
|------|---------|
| 成本 | token_input, token_output, estimated_cost_usd, cache_hit_rate |
| 效率 | task_duration_ms, parallel_utilization, avg_task_duration_ms |
| 质量 | task_success_rate, first_pass_rate, iteration_count |
| 稳定性 | failure_count, stall_count, retry_count, user_intervention_count |

## 采集流程

1. **初始化**：创建 MetricsCollector，设置 budget_limit
2. **迭代开始**：record_iteration_start(iteration)
3. **调用前后**：record_call_start/end 包裹每次 Agent/Skill 调用
4. **迭代结束**：aggregate_iteration → 输出成本/效率/质量摘要 → 预算检查(>80%预警)
5. **Loop完成**：generate_cost_report → 总成本+缓存节省+优化建议

## 配置

`.claude/task.local.md` YAML frontmatter: `observability: {enabled, budget_limit_usd, budget_warning_threshold(0.80), persist_metrics}`

<!-- /STATIC_CONTENT -->
