# Metrics Collector - 指标收集规范

## 指标体系

### 成本指标
token_input/output/cached(int,Agent/Skill调用时) | estimated_cost_usd(float,迭代结束) | cache_hit_rate(float 0-1,迭代结束)

定价(2026.03 MTok)：Opus $15/$75/$18.75/$1.50(in/out/cache_w/cache_r) | Sonnet $3/$15/$3.75/$0.30 | Haiku $0.80/$4/$1.00/$0.08

公式：`cost = input×p_in + output×p_out + cache_write×p_cw + cache_read×p_cr`

### 效率指标
task_duration_ms | iteration_duration_ms | total_duration_ms | parallel_utilization(理想耗时/实际耗时)

### 质量指标
task_success/failure_count | task_success_rate | iteration_count | first_pass_rate

### 稳定性指标
failure_count | stall_count | retry_count | user_intervention_count | timeout_count

## 采集点

1. Agent/Skill调用前后(类型/名称/prompt长度/耗时/token/模型/状态)
2. 任务执行前后(task_id/状态/耗时)
3. 迭代开始结束(编号/状态/耗时)
4. 并行度采样(运行数/最大并行/等待数/利用率)

## 聚合

- **迭代级**：成本(total tokens + cost_usd + cache_hit_rate) + 效率(duration/avg/count) + 质量(success/failure/rate)
- **Loop级**：所有迭代汇总 + per_iteration明细

## 输出

迭代摘要：`[迭代N指标] 成本$X 效率N任务Xmin 质量X%`
最终报告：总迭代/任务/耗时/成本/tokens/缓存/成功率 + 每迭代详情

存储：内存events[]+iteration_metrics[]，完成后持久化`.claude/tasks/{task_id}/metrics.json`
