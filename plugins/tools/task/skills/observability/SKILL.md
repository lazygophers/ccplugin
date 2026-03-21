---
agent: task:loop
description: 可观测性技能 - 实时收集性能指标、成本指标、质量指标，生成成本报告和优化建议
model: sonnet
context: fork
user-invocable: false
---

# Skills(task:observability) - 可观测性规范

## 技能概述

可观测性技能（Observability）负责在 task:loop 执行过程中实时收集和分析指标，提供成本控制、性能监控和问题诊断能力。

**核心能力**:
- ✅ **指标收集**: 自动采集 token 消耗、任务耗时、成功率等 20+ 指标
- ✅ **实时监控**: 每次迭代结束输出指标摘要，及时发现异常
- ✅ **成本报告**: 任务完成后生成详细成本报告，包含优化建议
- ✅ **预算控制**: 支持设置预算上限，超支预警

**设计原则**:
1. **零侵入**: 通过埋点自动采集，不影响任务执行
2. **实时性**: 指标立即可见，不等到任务结束
3. **可操作性**: 提供具体优化建议，而非仅展示数据
4. **成本意识**: 优先展示成本相关指标，帮助控制开支

**文档导航**:
- **完整实现指南** → [implementation-guide.md](./implementation-guide.md)
- **指标体系详情** → [metrics-collector.md](./metrics-collector.md)
- **成本报告规范** → [cost-report.md](./cost-report.md)

---

## 指标体系

详见 [`metrics-collector.md`](./metrics-collector.md)，包含 4 大类指标：

| 类别 | 指标数量 | 关键指标 |
|------|---------|---------|
| **成本指标** | 5 个 | token_input, token_output, estimated_cost_usd, cache_hit_rate |
| **效率指标** | 5 个 | task_duration_ms, parallel_utilization, avg_task_duration_ms |
| **质量指标** | 5 个 | task_success_rate, first_pass_rate, iteration_count |
| **稳定性指标** | 5 个 | failure_count, stall_count, retry_count, user_intervention_count |

---

## 采集流程概览

完整流程参见 [implementation-guide.md](./implementation-guide.md)

### 1. 初始化（Loop 启动时）

```python
collector = MetricsCollector()
config = load_observability_config()
collector.set_budget_limit(config.get("budget_limit_usd", None))
```

### 2. 迭代开始（Planning 阶段开始）

```python
collector.record_iteration_start(iteration)
```

### 3. Agent/Skill 调用前后（执行过程中）

```python
call_context = collector.record_call_start(type="agent", name="task:planner", prompt=prompt)
result = Agent(agent="task:planner", prompt=prompt)
collector.record_call_end(call_context=call_context, result=result)
```

### 4. 迭代结束（Verification 阶段完成）

```python
iteration_metrics = collector.aggregate_iteration(iteration)
print(f"\n[迭代 {iteration} 指标摘要]")
print(f"  成本：${iteration_metrics['cost']['total_cost_usd']:.2f}")
print(f"  效率：{iteration_metrics['efficiency']['task_count']} 个任务")
print(f"  质量：成功率 {iteration_metrics['quality']['success_rate']*100:.0f}%")

# 预算检查
if collector.budget_limit_usd:
    cumulative_cost = collector.get_cumulative_cost()
    if cumulative_cost > collector.budget_limit_usd * 0.80:
        print(f"\n⚠️ 预算预警")
```

### 5. Loop 完成（Finalization 阶段）

```python
final_report = collector.generate_cost_report()
print("## 成本报告")
print(f"总成本：${final_report['summary']['total_cost_usd']:.2f}")
print(f"缓存节省：${final_report['caching_analysis']['cost_saved_usd']:.2f}")
```

---

## 配置选项

详见 [implementation-guide.md](./implementation-guide.md#配置选项)

### 全局配置（`.claude/task.local.md`）

```yaml
---
observability:
  enabled: true
  budget_limit_usd: 5.00
  budget_warning_threshold: 0.80
  persist_metrics: true
---
```

---

## 验收标准

- ✅ **AC1**: 每次迭代结束输出结构化指标摘要（JSON 格式）
- ✅ **AC2**: 任务完成时输出总成本报告（包含 token、耗时、成功率）
- ✅ **AC3**: 并行度监控实时可查（当前/最大/平均三个维度）
- ✅ **AC4**: 指标格式为 JSON，字段定义清晰，可被外部工具解析
- ✅ **AC5**: 通过质量检查命令验证 AI 可正确理解可观测性技能
- ✅ **AC6**: 支持预算上限设置和超支预警
- ✅ **AC7**: 成本报告包含优化建议（缓存、模型、Prompt）
- ✅ **AC8**: 缓存效果分析包含节省成本和节省百分比
