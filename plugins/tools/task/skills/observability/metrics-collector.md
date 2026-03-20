# Metrics Collector - 指标收集规范

## 概述

指标收集器（Metrics Collector）负责在 task:loop 执行过程中实时收集性能指标、成本指标、质量指标和稳定性指标，为成本控制、性能优化和问题诊断提供数据支撑。

**核心目标**：
- ✅ **成本透明**：实时显示 token 消耗和预估成本，避免超支
- ✅ **性能监控**：追踪任务耗时和并行利用率，识别瓶颈
- ✅ **质量评估**：统计成功率和失败率，衡量执行质量
- ✅ **异常检测**：及时发现停滞、超时、资源耗尽等问题

---

## 指标体系

### 1. 成本指标（Cost Metrics）

| 指标名称 | 数据类型 | 单位 | 采集点 | 说明 |
|---------|---------|------|--------|------|
| `token_input` | integer | tokens | 每次 Agent/Skill 调用 | 输入 token 数量 |
| `token_output` | integer | tokens | 每次 Agent/Skill 调用 | 输出 token 数量 |
| `token_cached` | integer | tokens | 每次 Agent/Skill 调用 | 缓存命中的 token 数量 |
| `estimated_cost_usd` | float | USD | 每次迭代结束 | 预估成本（基于定价） |
| `cache_hit_rate` | float | 0-1 | 每次迭代结束 | 缓存命中率 |

**定价模型**（2026 年 3 月）：

| 模型 | 输入价格 | 输出价格 | 缓存写入价格 | 缓存读取价格 |
|------|---------|---------|------------|------------|
| Claude 4.6 Opus | $15 / MTok | $75 / MTok | $18.75 / MTok | $1.50 / MTok |
| Claude 4.6 Sonnet | $3 / MTok | $15 / MTok | $3.75 / MTok | $0.30 / MTok |
| Claude 4.5 Haiku | $0.80 / MTok | $4 / MTok | $1.00 / MTok | $0.08 / MTok |

**成本计算公式**：

```python
def calculate_cost(usage: dict, model: str) -> float:
    """
    计算单次调用成本

    Args:
        usage: {
            "input_tokens": int,
            "output_tokens": int,
            "cache_creation_tokens": int,  # 缓存写入
            "cache_read_tokens": int       # 缓存读取
        }
        model: "opus" | "sonnet" | "haiku"

    Returns:
        成本（USD）
    """
    pricing = {
        "opus": {
            "input": 15 / 1_000_000,
            "output": 75 / 1_000_000,
            "cache_write": 18.75 / 1_000_000,
            "cache_read": 1.50 / 1_000_000
        },
        "sonnet": {
            "input": 3 / 1_000_000,
            "output": 15 / 1_000_000,
            "cache_write": 3.75 / 1_000_000,
            "cache_read": 0.30 / 1_000_000
        },
        "haiku": {
            "input": 0.80 / 1_000_000,
            "output": 4 / 1_000_000,
            "cache_write": 1.00 / 1_000_000,
            "cache_read": 0.08 / 1_000_000
        }
    }

    p = pricing.get(model, pricing["sonnet"])

    cost = (
        usage["input_tokens"] * p["input"] +
        usage["output_tokens"] * p["output"] +
        usage.get("cache_creation_tokens", 0) * p["cache_write"] +
        usage.get("cache_read_tokens", 0) * p["cache_read"]
    )

    return cost
```

**示例**：

```python
usage = {
    "input_tokens": 10000,
    "output_tokens": 2000,
    "cache_creation_tokens": 5000,  # 首次调用缓存写入
    "cache_read_tokens": 0
}

cost_sonnet = calculate_cost(usage, "sonnet")
# = 10000 * 0.000003 + 2000 * 0.000015 + 5000 * 0.00000375
# = 0.03 + 0.03 + 0.01875 = $0.07875
```

---

### 2. 效率指标（Efficiency Metrics）

| 指标名称 | 数据类型 | 单位 | 采集点 | 说明 |
|---------|---------|------|--------|------|
| `task_duration_ms` | integer | milliseconds | 任务开始/结束 | 单个任务执行耗时 |
| `iteration_duration_ms` | integer | milliseconds | 迭代开始/结束 | 单次迭代耗时 |
| `total_duration_ms` | integer | milliseconds | loop 开始/结束 | 整个 loop 总耗时 |
| `parallel_utilization` | float | 0-1 | 执行阶段 | 并行度利用率 |
| `avg_task_duration_ms` | integer | milliseconds | 迭代结束 | 平均任务耗时 |

**并行度利用率计算**：

```python
def calculate_parallel_utilization(
    total_tasks: int,
    max_parallel: int,
    total_duration_ms: int,
    sum_task_duration_ms: int
) -> float:
    """
    计算并行度利用率

    并行度利用率 = 实际并行执行的时间 / 理想并行执行的时间

    Args:
        total_tasks: 任务总数
        max_parallel: 最大并行度
        total_duration_ms: 总执行时间
        sum_task_duration_ms: 所有任务耗时之和

    Returns:
        利用率（0-1）
    """
    # 理想情况：所有任务完美并行
    ideal_duration = sum_task_duration_ms / max_parallel

    # 实际耗时
    actual_duration = total_duration_ms

    # 利用率 = 理想 / 实际
    utilization = ideal_duration / actual_duration if actual_duration > 0 else 0

    return min(utilization, 1.0)  # 上限为 1.0
```

**示例**：

```python
# 场景：5 个任务，最大并行度 2，总耗时 10 秒
total_tasks = 5
max_parallel = 2
total_duration_ms = 10000
sum_task_duration_ms = 15000  # 每个任务 3 秒

utilization = calculate_parallel_utilization(
    total_tasks, max_parallel, total_duration_ms, sum_task_duration_ms
)
# = (15000 / 2) / 10000 = 7500 / 10000 = 0.75（75% 利用率）
```

---

### 3. 质量指标（Quality Metrics）

| 指标名称 | 数据类型 | 单位 | 采集点 | 说明 |
|---------|---------|------|--------|------|
| `task_success_count` | integer | - | 验证阶段 | 成功任务数量 |
| `task_failure_count` | integer | - | 验证阶段 | 失败任务数量 |
| `task_success_rate` | float | 0-1 | 验证阶段 | 任务成功率 |
| `iteration_count` | integer | - | 每次迭代 | 迭代次数 |
| `first_pass_rate` | float | 0-1 | 第一轮验证 | 首次通过率（首轮成功 / 总任务） |

**成功率计算**：

```python
def calculate_success_rate(
    success_count: int,
    failure_count: int
) -> float:
    """
    计算任务成功率

    成功率 = 成功任务数 / 总任务数
    """
    total = success_count + failure_count
    return success_count / total if total > 0 else 0.0
```

---

### 4. 稳定性指标（Stability Metrics）

| 指标名称 | 数据类型 | 单位 | 采集点 | 说明 |
|---------|---------|------|--------|------|
| `failure_count` | integer | - | 失败调整阶段 | 失败次数 |
| `stall_count` | integer | - | 停滞检测 | 停滞次数（连续相同错误） |
| `retry_count` | integer | - | 失败调整阶段 | 重试次数 |
| `user_intervention_count` | integer | - | ask_user 策略 | 用户干预次数 |
| `timeout_count` | integer | - | 超时检测 | 超时次数 |

---

## 采集点设计

### 采集点 1: Agent/Skill 调用前后

**触发时机**：每次调用 Agent 或 Skill

**采集内容**：
- 调用类型（Agent / Skill）
- 调用名称（agent 名称 / skill 名称）
- 输入 prompt 长度（字符数）
- 开始时间戳

**实现**：

```python
def before_agent_call(agent_name: str, prompt: str) -> dict:
    """Agent 调用前埋点"""
    call_id = generate_call_id()
    start_time = time.time()

    return {
        "call_id": call_id,
        "type": "agent",
        "name": agent_name,
        "prompt_length": len(prompt),
        "start_time": start_time
    }


def after_agent_call(call_context: dict, result: dict) -> dict:
    """Agent 调用后埋点"""
    end_time = time.time()
    duration_ms = int((end_time - call_context["start_time"]) * 1000)

    usage = result.get("usage", {})

    return {
        "call_id": call_context["call_id"],
        "type": "agent",
        "name": call_context["name"],
        "duration_ms": duration_ms,
        "token_input": usage.get("input_tokens", 0),
        "token_output": usage.get("output_tokens", 0),
        "token_cached_read": usage.get("cache_read_tokens", 0),
        "token_cached_write": usage.get("cache_creation_tokens", 0),
        "model": result.get("model", "sonnet"),
        "success": result.get("status") == "success"
    }
```

---

### 采集点 2: 任务执行前后

**触发时机**：每个任务开始和结束时

**采集内容**：
- 任务 ID
- 任务状态（pending / in_progress / completed / failed）
- 开始时间戳
- 结束时间戳
- 耗时

**实现**：

```python
def before_task_execution(task_id: str) -> dict:
    """任务执行前埋点"""
    return {
        "task_id": task_id,
        "status": "in_progress",
        "start_time": time.time()
    }


def after_task_execution(task_context: dict, status: str) -> dict:
    """任务执行后埋点"""
    end_time = time.time()
    duration_ms = int((end_time - task_context["start_time"]) * 1000)

    return {
        "task_id": task_context["task_id"],
        "status": status,  # completed / failed
        "duration_ms": duration_ms,
        "end_time": end_time
    }
```

---

### 采集点 3: 迭代开始和结束

**触发时机**：每次迭代开始和结束时

**采集内容**：
- 迭代编号
- 迭代状态（planning / executing / verifying / adjusting / completed）
- 开始时间戳
- 结束时间戳
- 耗时

**实现**：

```python
def before_iteration(iteration: int) -> dict:
    """迭代开始埋点"""
    return {
        "iteration": iteration,
        "start_time": time.time()
    }


def after_iteration(iteration_context: dict, status: str) -> dict:
    """迭代结束埋点"""
    end_time = time.time()
    duration_ms = int((end_time - iteration_context["start_time"]) * 1000)

    return {
        "iteration": iteration_context["iteration"],
        "status": status,
        "duration_ms": duration_ms
    }
```

---

### 采集点 4: 并行度实时监控

**触发时机**：执行阶段，每秒采样一次

**采集内容**：
- 当前并行度（正在运行的任务数）
- 最大并行度（配置值）
- 等待队列长度
- 时间戳

**实现**：

```python
def sample_parallel_utilization(
    running_tasks: int,
    max_parallel: int,
    pending_tasks: int
) -> dict:
    """并行度采样"""
    return {
        "timestamp": time.time(),
        "running_tasks": running_tasks,
        "max_parallel": max_parallel,
        "pending_tasks": pending_tasks,
        "utilization": running_tasks / max_parallel if max_parallel > 0 else 0
    }
```

---

## 指标聚合

### 迭代级别聚合

**触发时机**：每次迭代结束

**聚合内容**：

```python
def aggregate_iteration_metrics(iteration: int, events: list) -> dict:
    """
    聚合单次迭代的指标

    Args:
        iteration: 迭代编号
        events: 该迭代的所有事件列表

    Returns:
        聚合后的迭代指标
    """
    # 筛选事件
    agent_calls = [e for e in events if e["type"] == "agent_call"]
    task_executions = [e for e in events if e["type"] == "task_execution"]

    # 聚合成本
    total_input_tokens = sum(c["token_input"] for c in agent_calls)
    total_output_tokens = sum(c["token_output"] for c in agent_calls)
    total_cached_read = sum(c.get("token_cached_read", 0) for c in agent_calls)
    total_cached_write = sum(c.get("token_cached_write", 0) for c in agent_calls)

    # 计算成本
    total_cost = sum(
        calculate_cost({
            "input_tokens": c["token_input"],
            "output_tokens": c["token_output"],
            "cache_creation_tokens": c.get("token_cached_write", 0),
            "cache_read_tokens": c.get("token_cached_read", 0)
        }, c.get("model", "sonnet"))
        for c in agent_calls
    )

    # 聚合效率
    total_duration = sum(t["duration_ms"] for t in task_executions)
    avg_duration = total_duration / len(task_executions) if task_executions else 0

    # 聚合质量
    success_count = len([t for t in task_executions if t["status"] == "completed"])
    failure_count = len([t for t in task_executions if t["status"] == "failed"])
    success_rate = calculate_success_rate(success_count, failure_count)

    return {
        "iteration": iteration,
        "cost": {
            "total_input_tokens": total_input_tokens,
            "total_output_tokens": total_output_tokens,
            "total_cached_read": total_cached_read,
            "total_cached_write": total_cached_write,
            "total_cost_usd": total_cost,
            "cache_hit_rate": total_cached_read / (total_input_tokens + total_cached_read) if (total_input_tokens + total_cached_read) > 0 else 0
        },
        "efficiency": {
            "total_duration_ms": total_duration,
            "avg_task_duration_ms": avg_duration,
            "task_count": len(task_executions)
        },
        "quality": {
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": success_rate
        }
    }
```

---

### 任务级别聚合

**触发时机**：loop 完成后

**聚合内容**：

```python
def aggregate_loop_metrics(all_iterations: list) -> dict:
    """
    聚合整个 loop 的指标

    Args:
        all_iterations: 所有迭代的指标列表

    Returns:
        loop 级别的聚合指标
    """
    total_iterations = len(all_iterations)

    # 聚合成本
    total_cost = sum(i["cost"]["total_cost_usd"] for i in all_iterations)
    total_tokens = sum(
        i["cost"]["total_input_tokens"] + i["cost"]["total_output_tokens"]
        for i in all_iterations
    )
    avg_cache_hit_rate = sum(i["cost"]["cache_hit_rate"] for i in all_iterations) / total_iterations if total_iterations > 0 else 0

    # 聚合效率
    total_duration = sum(i["efficiency"]["total_duration_ms"] for i in all_iterations)
    total_tasks = sum(i["efficiency"]["task_count"] for i in all_iterations)

    # 聚合质量
    total_success = sum(i["quality"]["success_count"] for i in all_iterations)
    total_failure = sum(i["quality"]["failure_count"] for i in all_iterations)
    overall_success_rate = calculate_success_rate(total_success, total_failure)

    return {
        "summary": {
            "total_iterations": total_iterations,
            "total_tasks": total_tasks,
            "total_duration_ms": total_duration,
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
            "avg_cache_hit_rate": avg_cache_hit_rate,
            "overall_success_rate": overall_success_rate
        },
        "per_iteration": all_iterations
    }
```

---

## 输出格式

### 迭代摘要（每次迭代结束输出）

```json
{
  "iteration": 3,
  "cost": {
    "total_input_tokens": 45000,
    "total_output_tokens": 12000,
    "total_cached_read": 38000,
    "total_cached_write": 5000,
    "total_cost_usd": 0.42,
    "cache_hit_rate": 0.84
  },
  "efficiency": {
    "total_duration_ms": 125000,
    "avg_task_duration_ms": 25000,
    "task_count": 5
  },
  "quality": {
    "success_count": 4,
    "failure_count": 1,
    "success_rate": 0.8
  }
}
```

**终端输出**：

```
[迭代 3 指标摘要]
  成本：$0.42（输入 45K + 输出 12K，缓存命中率 84%）
  效率：5 个任务，总耗时 2.1 分钟，平均 25 秒/任务
  质量：成功率 80%（4/5）
```

---

### 最终报告（loop 完成后输出）

```json
{
  "summary": {
    "total_iterations": 3,
    "total_tasks": 15,
    "total_duration_ms": 480000,
    "total_tokens": 175000,
    "total_cost_usd": 1.25,
    "avg_cache_hit_rate": 0.87,
    "overall_success_rate": 0.93
  },
  "per_iteration": [
    {
      "iteration": 1,
      "cost": { "total_cost_usd": 0.55 },
      "efficiency": { "total_duration_ms": 180000 },
      "quality": { "success_rate": 0.8 }
    },
    {
      "iteration": 2,
      "cost": { "total_cost_usd": 0.28 },
      "efficiency": { "total_duration_ms": 175000 },
      "quality": { "success_rate": 1.0 }
    },
    {
      "iteration": 3,
      "cost": { "total_cost_usd": 0.42 },
      "efficiency": { "total_duration_ms": 125000 },
      "quality": { "success_rate": 0.8 }
    }
  ]
}
```

**终端输出**：

```
## 任务总结

总迭代次数：3
总任务数：15
总耗时：8.0 分钟
总成本：$1.25（175K tokens，缓存命中率 87%）
总成功率：93%（14/15）

### 每次迭代详情

迭代 1：$0.55，3.0 分钟，成功率 80%
迭代 2：$0.28，2.9 分钟，成功率 100%
迭代 3：$0.42，2.1 分钟，成功率 80%
```

---

## 存储格式

### 实时指标（内存）

在 loop 执行过程中，指标存储在内存中：

```python
class MetricsCollector:
    def __init__(self):
        self.events = []  # 所有事件
        self.current_iteration = 0
        self.iteration_metrics = []  # 每次迭代的聚合指标

    def record_event(self, event: dict):
        """记录事件"""
        event["timestamp"] = time.time()
        self.events.append(event)

    def aggregate_iteration(self):
        """聚合当前迭代"""
        iteration_events = [
            e for e in self.events
            if e.get("iteration") == self.current_iteration
        ]
        metrics = aggregate_iteration_metrics(
            self.current_iteration,
            iteration_events
        )
        self.iteration_metrics.append(metrics)

    def get_loop_summary(self) -> dict:
        """获取 loop 级别摘要"""
        return aggregate_loop_metrics(self.iteration_metrics)
```

---

### 持久化存储（可选）

Loop 完成后，可将指标持久化到文件：

```
.claude/
├── plans/
│   └── {task_hash}/
│       ├── plan.md
│       ├── approval-log.json
│       └── metrics.json  # 指标数据
```

**metrics.json 格式**：

```json
{
  "task_hash": "abc123",
  "task_description": "实现用户认证功能",
  "created_at": "2026-03-20T10:00:00Z",
  "completed_at": "2026-03-20T10:08:00Z",
  "summary": {
    "total_iterations": 3,
    "total_tasks": 15,
    "total_duration_ms": 480000,
    "total_cost_usd": 1.25,
    "overall_success_rate": 0.93
  },
  "iterations": [ /* 每次迭代的详细指标 */ ],
  "events": [ /* 所有原始事件（可选） */ ]
}
```

---

## 验收标准

- ✅ **AC1**: 定义 4 大类指标（成本、效率、质量、稳定性），共 20+ 个指标
- ✅ **AC2**: 每个指标明确数据类型、单位、采集点
- ✅ **AC3**: 成本计算公式准确，支持 3 种模型定价
- ✅ **AC4**: 并行度利用率计算公式正确
- ✅ **AC5**: 提供 4 个采集点的实现示例
- ✅ **AC6**: 支持迭代级别和 loop 级别聚合
- ✅ **AC7**: 输出格式为 JSON，字段定义清晰
