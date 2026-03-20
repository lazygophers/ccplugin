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

**核心能力**：
- ✅ **指标收集**：自动采集 token 消耗、任务耗时、成功率等 20+ 指标
- ✅ **实时监控**：每次迭代结束输出指标摘要，及时发现异常
- ✅ **成本报告**：任务完成后生成详细成本报告，包含优化建议
- ✅ **预算控制**：支持设置预算上限，超支预警

**设计原则**：
1. **零侵入**：通过埋点自动采集，不影响任务执行
2. **实时性**：指标立即可见，不等到任务结束
3. **可操作性**：提供具体优化建议，而非仅展示数据
4. **成本意识**：优先展示成本相关指标，帮助控制开支

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

## 采集流程

### 1. 初始化（Loop 启动时）

```python
from observability import MetricsCollector

# 创建指标收集器
collector = MetricsCollector()

# 加载配置
config = load_observability_config()  # 从 .claude/task.local.md 加载
collector.set_budget_limit(config.get("budget_limit_usd", None))

print(f"[可观测性] 已初始化（预算上限：${config.get('budget_limit_usd', '无限制')}）")
```

---

### 2. 迭代开始（Planning 阶段开始）

```python
# 记录迭代开始
collector.record_iteration_start(iteration)
```

---

### 3. Agent/Skill 调用前后（执行过程中）

```python
# 调用前
call_context = collector.record_call_start(
    type="agent",
    name="task:planner",
    prompt=prompt
)

# 执行 Agent
result = Agent(agent="task:planner", prompt=prompt)

# 调用后
collector.record_call_end(
    call_context=call_context,
    result=result
)
```

**自动化集成**：

可以通过装饰器或中间件自动埋点，避免手动调用：

```python
@auto_track_metrics(collector)
def execute_agent(agent_name: str, prompt: str):
    """自动追踪 Agent 调用"""
    return Agent(agent=agent_name, prompt=prompt)
```

---

### 4. 任务执行前后（Execution 阶段）

```python
# 任务开始
task_context = collector.record_task_start(task_id="T1")

# 执行任务
result = execute_task(task)

# 任务结束
collector.record_task_end(
    task_context=task_context,
    status="completed" if result["success"] else "failed"
)
```

---

### 5. 迭代结束（Verification 阶段完成）

```python
# 聚合迭代指标
iteration_metrics = collector.aggregate_iteration(iteration)

# 输出迭代摘要
print(f"\n[迭代 {iteration} 指标摘要]")
print(f"  成本：${iteration_metrics['cost']['total_cost_usd']:.2f}（缓存命中率 {iteration_metrics['cost']['cache_hit_rate']*100:.0f}%）")
print(f"  效率：{iteration_metrics['efficiency']['task_count']} 个任务，总耗时 {iteration_metrics['efficiency']['total_duration_ms']/60000:.1f} 分钟")
print(f"  质量：成功率 {iteration_metrics['quality']['success_rate']*100:.0f}%（{iteration_metrics['quality']['success_count']}/{iteration_metrics['quality']['success_count'] + iteration_metrics['quality']['failure_count']}）")

# 预算检查
if collector.budget_limit_usd:
    cumulative_cost = collector.get_cumulative_cost()
    budget_usage = cumulative_cost / collector.budget_limit_usd * 100

    if budget_usage > 80:
        print(f"\n⚠️ 预算预警：已使用 {budget_usage:.0f}%（${cumulative_cost:.2f} / ${collector.budget_limit_usd:.2f}）")

    if cumulative_cost > collector.budget_limit_usd:
        print(f"\n🛑 预算超支：当前成本 ${cumulative_cost:.2f} 已超过预算上限 ${collector.budget_limit_usd:.2f}")
        # 可选：暂停执行并请求用户确认
        user_decision = AskUserQuestion(
            questions=[{
                "question": f"当前成本 ${cumulative_cost:.2f} 已超过预算 ${collector.budget_limit_usd:.2f}，是否继续？",
                "header": "预算超支",
                "multiSelect": False,
                "options": [
                    {"label": "继续执行", "description": "忽略预算限制，继续执行"},
                    {"label": "终止任务", "description": "立即停止，保留已完成工作"}
                ]
            }]
        )
        if user_decision == "终止任务":
            raise BudgetExceededException(f"用户终止：预算超支（${cumulative_cost:.2f} > ${collector.budget_limit_usd:.2f}）")
```

---

### 6. Loop 完成（Finalization 阶段）

```python
# 生成最终报告
final_report = collector.generate_cost_report()

# 输出终端友好格式
print("\n" + "="*60)
print("## 任务总结")
print("="*60)
print(f"\n总迭代次数：{final_report['summary']['total_iterations']}")
print(f"总任务数：{final_report['summary']['total_tasks']}")
print(f"总耗时：{final_report['summary']['total_duration_ms'] / 60000:.1f} 分钟")
print(f"总成本：${final_report['summary']['total_cost_usd']:.2f}（{final_report['summary']['total_tokens'] / 1000:.0f}K tokens，缓存命中率 {final_report['summary']['avg_cache_hit_rate']*100:.0f}%）")
print(f"总成功率：{final_report['summary']['overall_success_rate']*100:.0f}%（{final_report['summary']['total_success']}/{final_report['summary']['total_tasks']}）")

# 成本构成
print(f"\n### 成本构成\n")
for iteration in final_report['cost_breakdown']['by_iteration']:
    print(f"迭代 {iteration['iteration']}：${iteration['cost_usd']:.2f}（{iteration['percentage']:.0f}%）")

# 缓存节省
caching = final_report['caching_analysis']
print(f"\n### 缓存节省\n")
print(f"节省：${caching['cost_saved_usd']:.2f}（{caching['savings_percentage']:.0f}%，相比无缓存）")

# 优化建议
if final_report['recommendations']:
    print(f"\n### 优化建议\n")
    priority_emoji = {"high": "🔴", "medium": "🟡", "low": "⚪"}
    for rec in final_report['recommendations']:
        print(f"{priority_emoji[rec['priority']]} {rec['suggestion']}")
        print(f"   潜在节省：${rec['potential_savings_usd']:.2f}\n")

# 持久化报告（可选）
save_cost_report(final_report, f".claude/plans/{task_hash}/metrics.json")
```

---

## 配置选项

### 全局配置（`.claude/task.local.md`）

```yaml
---
observability:
  # 是否启用可观测性
  enabled: true

  # 预算上限（USD）
  budget_limit_usd: 5.00

  # 预算预警阈值（百分比）
  budget_warning_threshold: 0.80  # 80% 时预警

  # 预算超支行为
  budget_exceed_behavior: "ask_user"  # ask_user | continue | abort

  # 是否持久化指标
  persist_metrics: true

  # 指标持久化路径
  metrics_path: ".claude/plans/{task_hash}/metrics.json"

  # 是否输出详细日志
  verbose: false

  # 实时监控刷新间隔（秒）
  monitor_interval_seconds: 5
---
```

### 运行时配置（命令行）

```bash
# 设置预算上限
/add --budget=5.00

# 启用详细日志
/add --verbose-metrics

# 禁用可观测性（不推荐）
/add --no-observability
```

---

## API 接口

### 主接口：`MetricsCollector`

```python
class MetricsCollector:
    """指标收集器"""

    def __init__(self):
        self.events = []
        self.current_iteration = 0
        self.iteration_metrics = []
        self.budget_limit_usd = None

    def set_budget_limit(self, limit_usd: float):
        """设置预算上限"""
        self.budget_limit_usd = limit_usd

    def record_iteration_start(self, iteration: int):
        """记录迭代开始"""
        self.current_iteration = iteration
        self.events.append({
            "type": "iteration_start",
            "iteration": iteration,
            "timestamp": time.time()
        })

    def record_call_start(self, type: str, name: str, prompt: str) -> dict:
        """记录 Agent/Skill 调用开始"""
        call_id = str(uuid.uuid4())
        context = {
            "call_id": call_id,
            "type": type,  # "agent" | "skill"
            "name": name,
            "prompt_length": len(prompt),
            "start_time": time.time()
        }
        self.events.append({
            "type": "call_start",
            "iteration": self.current_iteration,
            **context
        })
        return context

    def record_call_end(self, call_context: dict, result: dict):
        """记录 Agent/Skill 调用结束"""
        end_time = time.time()
        duration_ms = int((end_time - call_context["start_time"]) * 1000)

        usage = result.get("usage", {})

        self.events.append({
            "type": "call_end",
            "iteration": self.current_iteration,
            "call_id": call_context["call_id"],
            "name": call_context["name"],
            "duration_ms": duration_ms,
            "token_input": usage.get("input_tokens", 0),
            "token_output": usage.get("output_tokens", 0),
            "token_cached_read": usage.get("cache_read_tokens", 0),
            "token_cached_write": usage.get("cache_creation_tokens", 0),
            "model": result.get("model", "sonnet"),
            "success": result.get("status") == "success"
        })

    def record_task_start(self, task_id: str) -> dict:
        """记录任务开始"""
        context = {
            "task_id": task_id,
            "start_time": time.time()
        }
        self.events.append({
            "type": "task_start",
            "iteration": self.current_iteration,
            **context
        })
        return context

    def record_task_end(self, task_context: dict, status: str):
        """记录任务结束"""
        end_time = time.time()
        duration_ms = int((end_time - task_context["start_time"]) * 1000)

        self.events.append({
            "type": "task_end",
            "iteration": self.current_iteration,
            "task_id": task_context["task_id"],
            "status": status,  # "completed" | "failed"
            "duration_ms": duration_ms
        })

    def aggregate_iteration(self, iteration: int) -> dict:
        """聚合单次迭代的指标"""
        # 实现参见 metrics-collector.md
        iteration_events = [e for e in self.events if e.get("iteration") == iteration]
        metrics = aggregate_iteration_metrics(iteration, iteration_events)
        self.iteration_metrics.append(metrics)
        return metrics

    def get_cumulative_cost(self) -> float:
        """获取累计成本"""
        return sum(m["cost"]["total_cost_usd"] for m in self.iteration_metrics)

    def generate_cost_report(self) -> dict:
        """生成成本报告"""
        # 实现参见 cost-report.md
        return generate_cost_report(
            metrics=aggregate_loop_metrics(self.iteration_metrics),
            budget_limit_usd=self.budget_limit_usd
        )
```

---

## 集成点（Loop 流程）

### 集成点 1: 初始化阶段

**位置**：`skills/loop/detailed-flow.md` - 初始化阶段

**修改内容**：

```python
# 初始化阶段
status = "进行中"
iteration = 0
...

# 【可观测性集成】初始化指标收集器
from observability import MetricsCollector

collector = MetricsCollector()
config = load_observability_config()
collector.set_budget_limit(config.get("budget_limit_usd", None))

print(f"[MindFlow·{user_task}·初始化/0·进行中]")
print(f"初始化完成。可用 Skills：{len(available_skills)} 个，可用 Agents：{len(available_agents)} 个")
if collector.budget_limit_usd:
    print(f"预算上限：${collector.budget_limit_usd:.2f}")
```

---

### 集成点 2: 迭代开始

**位置**：`skills/loop/detailed-flow.md` - 计划设计阶段开始

**修改内容**：

```python
# 计划设计阶段
iteration += 1

# 【可观测性集成】记录迭代开始
collector.record_iteration_start(iteration)

planner_result = Agent(...)
```

---

### 集成点 3: 迭代结束

**位置**：`skills/loop/detailed-flow.md` - 结果验证阶段完成

**修改内容**：

```python
# 结果验证阶段
...

# 【可观测性集成】聚合并输出迭代指标
iteration_metrics = collector.aggregate_iteration(iteration)

print(f"\n[迭代 {iteration} 指标摘要]")
print(f"  成本：${iteration_metrics['cost']['total_cost_usd']:.2f}（缓存命中率 {iteration_metrics['cost']['cache_hit_rate']*100:.0f}%）")
print(f"  效率：{iteration_metrics['efficiency']['task_count']} 个任务，总耗时 {iteration_metrics['efficiency']['total_duration_ms']/60000:.1f} 分钟")
print(f"  质量：成功率 {iteration_metrics['quality']['success_rate']*100:.0f}%")

# 预算检查
if collector.budget_limit_usd:
    cumulative_cost = collector.get_cumulative_cost()
    budget_usage = cumulative_cost / collector.budget_limit_usd

    if budget_usage > 0.80:
        print(f"\n⚠️ 预算预警：已使用 {budget_usage*100:.0f}%（${cumulative_cost:.2f} / ${collector.budget_limit_usd:.2f}）")
```

---

### 集成点 4: Loop 完成

**位置**：`skills/loop/detailed-flow.md` - 全部完成阶段

**修改内容**：

```python
# 全部完成阶段
...

# 【可观测性集成】生成最终报告
final_report = collector.generate_cost_report()

print("\n" + "="*60)
print("## 成本报告")
print("="*60)
print(f"\n总成本：${final_report['summary']['total_cost_usd']:.2f}")
print(f"总耗时：{final_report['summary']['total_duration_ms'] / 60000:.1f} 分钟")
print(f"缓存节省：${final_report['caching_analysis']['cost_saved_usd']:.2f}（{final_report['caching_analysis']['savings_percentage']:.0f}%）")

# 优化建议
if final_report['recommendations']:
    print(f"\n### 优化建议\n")
    for rec in final_report['recommendations'][:3]:  # 只显示前 3 条
        print(f"• {rec['suggestion']}")

# 持久化（可选）
if config.get("persist_metrics", True):
    save_path = config.get("metrics_path", ".claude/plans/{task_hash}/metrics.json").format(task_hash=task_hash)
    save_cost_report(final_report, save_path)
    print(f"\n指标已保存：{save_path}")
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
