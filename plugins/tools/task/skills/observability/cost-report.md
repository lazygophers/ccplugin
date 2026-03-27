# Cost Report - 成本报告规范

## 概述

Loop完成后生成成本分析报告：token消耗分布、成本构成、缓存效果、优化建议、预算预警。

## 报告结构（7模块）

### 1. 执行摘要
字段：task_description/total_iterations/total_tasks/total_duration_ms/total_cost_usd/budget_limit_usd/budget_usage_percentage/status

### 2. Token消耗明细
字段：total_tokens/input_tokens/output_tokens/cache_creation_tokens/cache_read_tokens/cache_hit_rate + breakdown_by_type(agent_calls/skill_calls各含count/input/output/cache_read)

### 3. 成本构成
三维分析：按类型(input/output/cache_write/cache_read) + 按模型(opus/sonnet/haiku各含calls/cost) + 按迭代(iteration/cost/percentage)

### 4. 缓存效果
字段：cache_hit_rate/cache_read_tokens/cost_without_cache/cost_with_cache/cost_saved/savings_percentage/top_cached_skills[]

**节省计算**：saved = cache_read_tokens × (input_price - cache_read_price)

### 5. Top消费者
按Agent排名(calls/cost/percentage/avg_cost) + 按Task排名(id/description/cost/percentage/duration)

### 6. 优化建议
自动生成规则：缓存命中率<80%→优化缓存标记(高) | 高成本用Opus但输入<50K→降级模型(中) | 平均输入>10K→优化prompt(低) | 并行利用率<60%→增加并行(低)

### 7. 预算追踪
字段：budget_limit/total_cost/remaining/usage_percentage/status + forecast(estimated_final/confidence/will_exceed) + history[]

**预测**：avg_cost_per_iteration × remaining_iterations + current_cost

## 输出格式

支持JSON(默认)/终端友好/Markdown三种格式。

终端摘要示例：`成本：$X（输入X%+输出X%+缓存X%）缓存节省$X（X%）`
