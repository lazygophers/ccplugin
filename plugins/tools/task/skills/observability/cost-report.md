# Cost Report - 成本报告生成规范

## 概述

成本报告（Cost Report）负责在 task:loop 完成后生成详细的成本分析报告，帮助用户了解 token 消耗分布、成本构成、缓存效果和优化建议。

**核心目标**：
- ✅ **成本透明**：清晰展示每次迭代、每个任务、每个 Agent 的成本
- ✅ **缓存分析**：评估 Prompt Caching 效果，计算节省的成本
- ✅ **优化建议**：基于成本数据提供优化方向
- ✅ **预算预警**：支持设置预算上限，超支提醒

---

## 报告结构

### 1. 执行摘要（Executive Summary）

```json
{
  "summary": {
    "task_description": "实现用户认证功能",
    "total_iterations": 3,
    "total_tasks": 15,
    "total_duration_ms": 480000,
    "total_cost_usd": 1.25,
    "budget_limit_usd": 5.00,
    "budget_usage_percentage": 25.0,
    "status": "within_budget"
  }
}
```

**终端输出**：

```
## 成本报告

任务：实现用户认证功能
总成本：$1.25 / $5.00（25% 预算使用）
总耗时：8.0 分钟（3 次迭代，15 个任务）
状态：✅ 在预算内
```

---

### 2. Token 消耗明细（Token Usage Breakdown）

```json
{
  "token_usage": {
    "total_tokens": 175000,
    "input_tokens": 125000,
    "output_tokens": 50000,
    "cache_creation_tokens": 8000,
    "cache_read_tokens": 95000,
    "cache_hit_rate": 0.87,
    "breakdown_by_type": {
      "agent_calls": {
        "count": 45,
        "input_tokens": 100000,
        "output_tokens": 45000,
        "cache_read_tokens": 85000
      },
      "skill_calls": {
        "count": 12,
        "input_tokens": 25000,
        "output_tokens": 5000,
        "cache_read_tokens": 10000
      }
    }
  }
}
```

**终端输出**：

```
### Token 消耗明细

总 tokens：175K（输入 125K + 输出 50K）
缓存写入：8K
缓存读取：95K（命中率 87%）

分类统计：
  • Agent 调用：45 次（输入 100K + 输出 45K，缓存 85K）
  • Skill 调用：12 次（输入 25K + 输出 5K，缓存 10K）
```

---

### 3. 成本构成分析（Cost Breakdown）

```json
{
  "cost_breakdown": {
    "total_cost_usd": 1.25,
    "by_type": {
      "input_cost": 0.375,
      "output_cost": 0.750,
      "cache_write_cost": 0.030,
      "cache_read_cost": 0.095
    },
    "by_model": {
      "opus": {
        "calls": 2,
        "cost_usd": 0.15
      },
      "sonnet": {
        "calls": 40,
        "cost_usd": 1.05
      },
      "haiku": {
        "calls": 15,
        "cost_usd": 0.05
      }
    },
    "by_iteration": [
      {
        "iteration": 1,
        "cost_usd": 0.55,
        "percentage": 44.0
      },
      {
        "iteration": 2,
        "cost_usd": 0.28,
        "percentage": 22.4
      },
      {
        "iteration": 3,
        "cost_usd": 0.42,
        "percentage": 33.6
      }
    ]
  }
}
```

**终端输出**：

```
### 成本构成

总成本：$1.25

按类型：
  • 输入成本：$0.38（30%）
  • 输出成本：$0.75（60%）
  • 缓存写入：$0.03（2%）
  • 缓存读取：$0.10（8%）

按模型：
  • Opus（2 次）：$0.15（12%）
  • Sonnet（40 次）：$1.05（84%）
  • Haiku（15 次）：$0.05（4%）

按迭代：
  • 迭代 1：$0.55（44%）
  • 迭代 2：$0.28（22%）
  • 迭代 3：$0.42（34%）
```

---

### 4. 缓存效果分析（Caching Analysis）

```json
{
  "caching_analysis": {
    "cache_hit_rate": 0.87,
    "cache_read_tokens": 95000,
    "cost_without_cache_usd": 2.80,
    "cost_with_cache_usd": 1.25,
    "cost_saved_usd": 1.55,
    "savings_percentage": 55.4,
    "top_cached_skills": [
      {
        "skill": "task:loop",
        "cache_read_tokens": 45000,
        "cost_saved_usd": 0.85
      },
      {
        "skill": "task:planner",
        "cache_read_tokens": 30000,
        "cost_saved_usd": 0.50
      },
      {
        "skill": "task:verifier",
        "cache_read_tokens": 20000,
        "cost_saved_usd": 0.20
      }
    ]
  }
}
```

**缓存节省计算**：

```python
def calculate_cache_savings(
    cache_read_tokens: int,
    model: str = "sonnet"
) -> dict:
    """
    计算缓存节省的成本

    如果没有缓存，这些 tokens 需要按输入价格付费
    有缓存后，按缓存读取价格付费
    """
    pricing = {
        "opus": {"input": 15 / 1_000_000, "cache_read": 1.50 / 1_000_000},
        "sonnet": {"input": 3 / 1_000_000, "cache_read": 0.30 / 1_000_000},
        "haiku": {"input": 0.80 / 1_000_000, "cache_read": 0.08 / 1_000_000}
    }

    p = pricing.get(model, pricing["sonnet"])

    cost_without_cache = cache_read_tokens * p["input"]
    cost_with_cache = cache_read_tokens * p["cache_read"]
    savings = cost_without_cache - cost_with_cache
    savings_percentage = (savings / cost_without_cache * 100) if cost_without_cache > 0 else 0

    return {
        "cost_without_cache": cost_without_cache,
        "cost_with_cache": cost_with_cache,
        "savings": savings,
        "savings_percentage": savings_percentage
    }
```

**终端输出**：

```
### 缓存效果分析

缓存命中率：87%（95K / 109K）
成本对比：
  • 无缓存：$2.80
  • 有缓存：$1.25
  • 节省：$1.55（55%）

最有效的缓存 Skills：
  1. task:loop - 节省 $0.85（45K tokens）
  2. task:planner - 节省 $0.50（30K tokens）
  3. task:verifier - 节省 $0.20（20K tokens）
```

---

### 5. Top 消费者分析（Top Spenders）

```json
{
  "top_spenders": {
    "by_agent": [
      {
        "agent": "task:planner",
        "calls": 15,
        "cost_usd": 0.45,
        "percentage": 36.0,
        "avg_cost_per_call": 0.03
      },
      {
        "agent": "task:verifier",
        "calls": 12,
        "cost_usd": 0.30,
        "percentage": 24.0,
        "avg_cost_per_call": 0.025
      },
      {
        "agent": "coder",
        "calls": 18,
        "cost_usd": 0.25,
        "percentage": 20.0,
        "avg_cost_per_call": 0.014
      }
    ],
    "by_task": [
      {
        "task_id": "T3",
        "description": "实现 API 接口",
        "cost_usd": 0.35,
        "percentage": 28.0,
        "duration_ms": 120000
      },
      {
        "task_id": "T5",
        "description": "编写测试用例",
        "cost_usd": 0.22,
        "percentage": 17.6,
        "duration_ms": 90000
      }
    ]
  }
}
```

**终端输出**：

```
### Top 消费者

按 Agent 排名：
  1. task:planner - $0.45（36%，15 次调用，平均 $0.03/次）
  2. task:verifier - $0.30（24%，12 次调用，平均 $0.025/次）
  3. coder - $0.25（20%，18 次调用，平均 $0.014/次）

按任务排名：
  1. T3（实现 API 接口）- $0.35（28%，耗时 2.0 分钟）
  2. T5（编写测试用例）- $0.22（18%，耗时 1.5 分钟）
```

---

### 6. 优化建议（Optimization Recommendations）

```json
{
  "recommendations": [
    {
      "type": "cache_optimization",
      "priority": "high",
      "suggestion": "task:planner 缓存命中率仅 72%，建议检查 STATIC_CONTENT 标记是否覆盖所有静态内容",
      "potential_savings_usd": 0.15
    },
    {
      "type": "model_optimization",
      "priority": "medium",
      "suggestion": "任务 T3 使用 Opus 模型，但复杂度评估显示 Sonnet 已足够，建议降级模型",
      "potential_savings_usd": 0.08
    },
    {
      "type": "prompt_optimization",
      "priority": "low",
      "suggestion": "verifier 的输入 token 较高（平均 8K），建议优化 prompt 长度",
      "potential_savings_usd": 0.05
    }
  ]
}
```

**优化建议生成逻辑**：

```python
def generate_recommendations(metrics: dict, cost_breakdown: dict) -> list:
    """
    基于成本数据生成优化建议

    规则：
    1. 缓存命中率 <80%：建议优化缓存策略
    2. 高成本 agent/task 使用高端模型：建议降级
    3. 输入 token 异常高：建议优化 prompt
    4. 并行度利用率 <60%：建议增加并行度
    """
    recommendations = []

    # 规则 1: 缓存优化
    if metrics.get("cache_hit_rate", 1.0) < 0.80:
        recommendations.append({
            "type": "cache_optimization",
            "priority": "high",
            "suggestion": f"缓存命中率仅 {metrics['cache_hit_rate']*100:.0f}%，建议检查 STATIC_CONTENT 标记",
            "potential_savings_usd": estimate_cache_improvement_savings(metrics)
        })

    # 规则 2: 模型降级
    for agent in cost_breakdown.get("by_agent", []):
        if agent["model"] == "opus" and agent["avg_input_tokens"] < 50000:
            recommendations.append({
                "type": "model_optimization",
                "priority": "medium",
                "suggestion": f"{agent['agent']} 使用 Opus，但输入规模较小，建议降级为 Sonnet",
                "potential_savings_usd": estimate_model_downgrade_savings(agent)
            })

    # 规则 3: Prompt 优化
    for agent in cost_breakdown.get("by_agent", []):
        if agent["avg_input_tokens"] > 10000:
            recommendations.append({
                "type": "prompt_optimization",
                "priority": "low",
                "suggestion": f"{agent['agent']} 平均输入 {agent['avg_input_tokens']/1000:.1f}K tokens，建议优化 prompt 长度",
                "potential_savings_usd": estimate_prompt_optimization_savings(agent)
            })

    return recommendations
```

**终端输出**：

```
### 优化建议

🔴 高优先级：
  • 缓存优化：task:planner 缓存命中率仅 72%，建议检查 STATIC_CONTENT 标记
    潜在节省：$0.15

🟡 中优先级：
  • 模型优化：任务 T3 使用 Opus，但复杂度评估显示 Sonnet 已足够，建议降级
    潜在节省：$0.08

⚪ 低优先级：
  • Prompt 优化：verifier 平均输入 8K tokens，建议优化 prompt 长度
    潜在节省：$0.05
```

---

### 7. 预算追踪（Budget Tracking）

```json
{
  "budget_tracking": {
    "budget_limit_usd": 5.00,
    "total_cost_usd": 1.25,
    "remaining_budget_usd": 3.75,
    "usage_percentage": 25.0,
    "status": "within_budget",
    "forecast": {
      "estimated_final_cost": 1.40,
      "confidence": 0.85,
      "will_exceed_budget": false
    },
    "history": [
      {
        "iteration": 1,
        "cumulative_cost": 0.55,
        "percentage": 11.0
      },
      {
        "iteration": 2,
        "cumulative_cost": 0.83,
        "percentage": 16.6
      },
      {
        "iteration": 3,
        "cumulative_cost": 1.25,
        "percentage": 25.0
      }
    ]
  }
}
```

**预算预测算法**：

```python
def forecast_budget(
    iterations_completed: int,
    total_cost_so_far: float,
    estimated_remaining_iterations: int
) -> dict:
    """
    预测最终成本

    基于历史趋势和剩余工作量预测
    """
    avg_cost_per_iteration = total_cost_so_far / iterations_completed if iterations_completed > 0 else 0

    # 简单线性预测
    estimated_remaining_cost = avg_cost_per_iteration * estimated_remaining_iterations
    estimated_final_cost = total_cost_so_far + estimated_remaining_cost

    # 置信度（基于历史方差）
    confidence = 0.85  # 简化版，实际需要计算方差

    return {
        "estimated_final_cost": estimated_final_cost,
        "confidence": confidence,
        "will_exceed_budget": estimated_final_cost > budget_limit
    }
```

**终端输出**：

```
### 预算追踪

预算上限：$5.00
当前成本：$1.25（25% 使用）
剩余预算：$3.75
状态：✅ 在预算内

预测：
  • 预计最终成本：$1.40（置信度 85%）
  • 预计剩余预算：$3.60
  • 超支风险：❌ 无
```

---

## 报告生成 API

```python
def generate_cost_report(
    metrics: dict,
    budget_limit_usd: float = None
) -> dict:
    """
    生成完整的成本报告

    Args:
        metrics: MetricsCollector 收集的指标数据
        budget_limit_usd: 预算上限（可选）

    Returns:
        成本报告（JSON 格式）
    """
    # 1. 执行摘要
    summary = generate_summary(metrics, budget_limit_usd)

    # 2. Token 消耗明细
    token_usage = generate_token_usage(metrics)

    # 3. 成本构成分析
    cost_breakdown = generate_cost_breakdown(metrics)

    # 4. 缓存效果分析
    caching_analysis = generate_caching_analysis(metrics)

    # 5. Top 消费者
    top_spenders = generate_top_spenders(metrics)

    # 6. 优化建议
    recommendations = generate_recommendations(metrics, cost_breakdown)

    # 7. 预算追踪（如果设置了预算）
    budget_tracking = None
    if budget_limit_usd:
        budget_tracking = generate_budget_tracking(metrics, budget_limit_usd)

    return {
        "summary": summary,
        "token_usage": token_usage,
        "cost_breakdown": cost_breakdown,
        "caching_analysis": caching_analysis,
        "top_spenders": top_spenders,
        "recommendations": recommendations,
        "budget_tracking": budget_tracking
    }
```

---

## 输出格式选择

### JSON 格式（默认）

```python
report = generate_cost_report(metrics)
print(json.dumps(report, indent=2, ensure_ascii=False))
```

### 终端友好格式

```python
def print_cost_report_terminal(report: dict):
    """终端友好的成本报告输出"""
    # 执行摘要
    print("\n## 成本报告\n")
    print(f"任务：{report['summary']['task_description']}")
    print(f"总成本：${report['summary']['total_cost_usd']:.2f}")
    print(f"总耗时：{report['summary']['total_duration_ms'] / 60000:.1f} 分钟")

    # Token 消耗
    print("\n### Token 消耗明细\n")
    usage = report['token_usage']
    print(f"总 tokens：{usage['total_tokens'] / 1000:.0f}K")
    print(f"缓存命中率：{usage['cache_hit_rate'] * 100:.0f}%")

    # 成本构成
    print("\n### 成本构成\n")
    for iteration in report['cost_breakdown']['by_iteration']:
        print(f"迭代 {iteration['iteration']}：${iteration['cost_usd']:.2f}（{iteration['percentage']:.0f}%）")

    # 缓存效果
    print("\n### 缓存节省\n")
    caching = report['caching_analysis']
    print(f"节省：${caching['cost_saved_usd']:.2f}（{caching['savings_percentage']:.0f}%）")

    # 优化建议
    if report['recommendations']:
        print("\n### 优化建议\n")
        for rec in report['recommendations']:
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "⚪"}
            print(f"{priority_emoji[rec['priority']]} {rec['suggestion']}")
            print(f"   潜在节省：${rec['potential_savings_usd']:.2f}")
```

### Markdown 格式（用于文档）

```python
def export_cost_report_markdown(report: dict, output_path: str):
    """导出成本报告为 Markdown 文件"""
    md_content = f"""# 成本报告

## 执行摘要

- 任务：{report['summary']['task_description']}
- 总成本：${report['summary']['total_cost_usd']:.2f}
- 总耗时：{report['summary']['total_duration_ms'] / 60000:.1f} 分钟
- 总迭代：{report['summary']['total_iterations']} 次

## Token 消耗

| 类型 | 数量 |
|------|------|
| 总 tokens | {report['token_usage']['total_tokens']:,} |
| 输入 | {report['token_usage']['input_tokens']:,} |
| 输出 | {report['token_usage']['output_tokens']:,} |
| 缓存读取 | {report['token_usage']['cache_read_tokens']:,} |

缓存命中率：{report['token_usage']['cache_hit_rate'] * 100:.1f}%

## 成本构成

...（省略详细内容）
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
```

---

## 验收标准

- ✅ **AC1**: 生成 7 个模块的成本报告（摘要、Token、成本、缓存、Top、建议、预算）
- ✅ **AC2**: 支持 JSON、终端、Markdown 三种输出格式
- ✅ **AC3**: 缓存节省计算准确（对比有缓存 vs 无缓存成本）
- ✅ **AC4**: 优化建议基于规则自动生成（缓存、模型、Prompt、并行度）
- ✅ **AC5**: 预算追踪支持预测最终成本和超支预警
- ✅ **AC6**: Top 消费者按成本排序，显示百分比和平均成本
- ✅ **AC7**: 成本分类明确（按类型、按模型、按迭代）
