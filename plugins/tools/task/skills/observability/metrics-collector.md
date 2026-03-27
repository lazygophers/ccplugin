# Metrics Collector - 指标收集规范

## 概述

在 task:loop 执行中实时收集性能/成本/质量/稳定性指标，支撑成本控制和问题诊断。

## 指标体系

### 1. 成本指标

| 指标 | 类型 | 采集点 | 说明 |
|------|------|--------|------|
| `token_input` | int(tokens) | Agent/Skill调用 | 输入token |
| `token_output` | int(tokens) | Agent/Skill调用 | 输出token |
| `token_cached` | int(tokens) | Agent/Skill调用 | 缓存命中token |
| `estimated_cost_usd` | float(USD) | 迭代结束 | 预估成本 |
| `cache_hit_rate` | float(0-1) | 迭代结束 | 缓存命中率 |

**定价（2026.03）**：Opus: $15/$75/$18.75/$1.50 MTok (in/out/cache_w/cache_r)；Sonnet: $3/$15/$3.75/$0.30；Haiku: $0.80/$4/$1.00/$0.08。

**成本公式**：`cost = input×p_in + output×p_out + cache_write×p_cw + cache_read×p_cr`

### 2. 效率指标

| 指标 | 类型 | 采集点 | 说明 |
|------|------|--------|------|
| `task_duration_ms` | int(ms) | 任务前后 | 单任务耗时 |
| `iteration_duration_ms` | int(ms) | 迭代前后 | 迭代耗时 |
| `total_duration_ms` | int(ms) | loop前后 | 总耗时 |
| `parallel_utilization` | float(0-1) | 执行阶段 | 并行利用率=理想耗时/实际耗时 |

### 3. 质量指标

| 指标 | 类型 | 采集点 | 说明 |
|------|------|--------|------|
| `task_success_count/failure_count` | int | 验证阶段 | 成功/失败数 |
| `task_success_rate` | float(0-1) | 验证阶段 | 成功率 |
| `iteration_count` | int | 每次迭代 | 迭代次数 |
| `first_pass_rate` | float(0-1) | 首轮验证 | 首次通过率 |

### 4. 稳定性指标

| 指标 | 类型 | 采集点 | 说明 |
|------|------|--------|------|
| `failure_count` | int | 调整阶段 | 失败次数 |
| `stall_count` | int | 停滞检测 | 连续相同错误次数 |
| `retry_count` | int | 调整阶段 | 重试次数 |
| `user_intervention_count` | int | ask_user | 用户干预次数 |
| `timeout_count` | int | 超时检测 | 超时次数 |

## 采集点

4个采集点：1) Agent/Skill调用前后（类型/名称/prompt长度/耗时/token用量/模型/成功状态）2) 任务执行前后（task_id/状态/耗时）3) 迭代开始结束（编号/状态/耗时）4) 并行度采样（运行数/最大并行/等待数/利用率）

## 指标聚合

- **迭代级**：聚合成本（total_input/output/cached tokens + cost_usd + cache_hit_rate）、效率（duration/avg_task_duration/count）、质量（success/failure/rate）
- **Loop级**：聚合所有迭代的成本/效率/质量，含per_iteration明细

## 输出格式

迭代摘要：`[迭代N指标] 成本：$X（输入Xk+输出Xk，缓存命中X%）效率：N任务，耗时Xmin 质量：成功率X%`

最终报告：总迭代/任务/耗时/成本/tokens/缓存命中率/成功率 + 每迭代详情

## 存储

内存中维护events[]和iteration_metrics[]。Loop完成后可持久化到`.claude/plans/{task_hash}/metrics.json`。
