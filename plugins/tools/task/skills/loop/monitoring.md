# Loop 监控和可观测性

本文档包含 MindFlow Loop 的监控指标、进度报告和可观测性实践。

## 实时监控

### 任务级监控

**任务状态**：
- `pending` - 待执行（依赖未满足）
- `ready` - 就绪（可以开始执行）
- `in_progress` - 执行中
- `completed` - 已完成
- `failed` - 失败

**任务进度**：
- 百分比：0% - 100%
- 阶段：初始化 → 执行 → 验证 → 完成
- 时间戳：开始时间、结束时间

**执行时间**：
- 计划时间：预估执行时间
- 实际时间：真实执行时间
- 时间偏差：实际 - 计划

**资源使用**：
- CPU 使用率
- 内存占用
- 磁盘 I/O
- 网络流量

### 系统级监控

**迭代次数**：
- 当前迭代：iteration
- 总迭代次数：total_iterations
- 平均迭代时间：avg_iteration_time

**停滞检测**：
- 停滞次数：stalled_count
- 停滞模式：error_signature
- 最后停滞时间：last_stall_time

**用户指导次数**：
- 总指导次数：guidance_count
- 指导原因：guidance_reasons
- 用户响应时间：user_response_time

**整体进度**：
- 完成任务数：completed_tasks
- 总任务数：total_tasks
- 完成百分比：(completed / total) * 100%
- 剩余任务数：remaining_tasks

## 进度报告格式

### 状态前缀格式

所有进行中的操作必须包含状态前缀：

```
[MindFlow·${任务内容}·${当前步骤}/${迭代轮数}·${状态}]
```

**示例**：
```
[MindFlow·添加用户认证·计划设计/1·进行中]
[MindFlow·添加用户认证·任务执行/2·进行中]
[MindFlow·添加用户认证·结果验证/2·passed]
[MindFlow·添加用户认证·completed]
```

### 任务进度表

```
[MindFlow·添加用户认证·任务执行/2·进行中]
任务进度：
T1: 实现 JWT 工具 ········ ✅ 已完成 ············· coder（开发者）
T2: 认证中间件 ·········· 🔄 进行中 ············· coder（开发者）
T3: 编写测试 ············ ⏸️ 等待前置任务(T2) ···· tester（测试员）

完成：1/3  进行中：1/3  等待中：1/3
```

### 迭代总结

```
## 迭代 #2 总结

状态：✓ 成功
任务完成：3/3
测试覆盖：92%
执行时间：8 分钟

任务详情：
- T1: 实现 JWT 工具 ✓ (2 分钟)
- T2: 认证中间件 ✓ (3 分钟)
- T3: 编写测试 ✓ (3 分钟)
```

## 监控指标

### 关键性能指标 (KPI)

**效率指标**：
- 平均任务完成时间
- 并行度利用率
- 资源利用率

**质量指标**：
- 测试覆盖率
- 代码质量分数
- 验收标准通过率

**可靠性指标**：
- 任务失败率
- 停滞发生率
- 补偿执行率

**用户体验指标**：
- 迭代完成时间
- 用户干预次数
- 反馈响应时间

### 监控数据收集（集成可观测性技能）

**注意**：Loop 监控已集成 `task:observability` 技能，提供完整的成本、效率、质量和稳定性指标。

```python
# 使用可观测性技能替代基础 MonitoringCollector
from observability import MetricsCollector

# 初始化（Loop 启动时）
collector = MetricsCollector()
config = load_observability_config()  # 从 .claude/task.local.md 加载
collector.set_budget_limit(config.get("budget_limit_usd", None))

print(f"[可观测性] 已初始化（预算上限：${config.get('budget_limit_usd', '无限制')}）")
```

**迭代监控集成**：

```python
# 迭代开始
collector.record_iteration_start(iteration)

# Agent/Skill 调用（自动埋点）
@auto_track_metrics(collector)
def execute_agent(agent_name: str, prompt: str):
    return Agent(agent=agent_name, prompt=prompt)

# 任务执行
task_context = collector.record_task_start(task_id="T1")
result = execute_task(task)
collector.record_task_end(task_context, status="completed")

# 迭代结束（聚合并输出）
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

**最终报告生成**：

```python
# Loop 完成时
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
    for rec in final_report['recommendations'][:3]:
        print(f"• {rec['suggestion']}")

# 持久化
if config.get("persist_metrics", True):
    save_path = ".claude/plans/{task_hash}/metrics.json".format(task_hash=task_hash)
    save_cost_report(final_report, save_path)
    print(f"\n指标已保存：{save_path}")
```

**详细文档**：
- [metrics-collector.md](../observability/metrics-collector.md) - 指标体系定义
- [cost-report.md](../observability/cost-report.md) - 成本报告生成
- [observability/SKILL.md](../observability/SKILL.md) - 可观测性主技能

## 日志记录

### 日志级别

- **DEBUG**：详细的调试信息
- **INFO**：常规操作信息
- **WARNING**：警告信息（非致命）
- **ERROR**：错误信息（可恢复）
- **CRITICAL**：严重错误（不可恢复）

### 结构化日志

```python
import json
from datetime import datetime

def log_structured(level, event, **kwargs):
    """记录结构化日志"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "level": level,
        "event": event,
        **kwargs
    }
    print(json.dumps(log_entry))

# 使用示例
log_structured("INFO", "task_started", task_id="T1", agent="coder")
log_structured("ERROR", "task_failed", task_id="T2", reason="timeout")
```

### 关键事件日志

**任务生命周期**：
- 任务创建
- 任务开始
- 任务完成/失败
- 任务重试

**状态转换**：
- 阶段切换
- 状态变更
- 决策点

**错误和异常**：
- 错误发生
- 异常捕获
- 补偿执行

## 可观测性最佳实践

### 可追踪性

**关联 ID**：
- 为每个迭代分配唯一 ID
- 任务继承迭代 ID
- 日志包含关联 ID

**调用链跟踪**：
- 记录 agent 调用关系
- 追踪任务依赖链
- 可视化执行路径

### 可调试性

**上下文信息**：
- 记录完整的输入参数
- 保存中间状态
- 输出详细的错误信息

**重现能力**：
- 记录所有决策点
- 保存随机种子
- 可重放执行过程

### 可理解性

**清晰的命名**：
- 使用语义化的名称
- 避免缩写和简写
- 保持命名一致性

**文档化**：
- 记录关键决策
- 说明设计意图
- 提供使用示例
