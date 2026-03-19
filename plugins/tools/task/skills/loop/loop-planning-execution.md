# Loop 规划和执行最佳实践

本文档包含 MindFlow Loop 规划和执行阶段的最佳实践。

<planning_best_practices>

## 规划阶段

充分的规划是成功执行的前提。规划阶段需要明确定义任务目标、识别关键交付物、设定可量化的成功标准。之所以强调目标明确，是因为模糊的目标会导致后续执行和验证无法判断是否完成。

任务分解使用 MECE 原则（互斥且完全穷尽），确保每个任务都是原子性的。避免过度拆分（增加管理开销）或拆分不足（单个任务过于复杂难以验证）。找到合适的粒度需要权衡：任务应足够小以便独立验证，又足够大以产生有意义的交付物。

依赖建模要求识别任务间的依赖关系，确保依赖关系形成 DAG（有向无环图），标注关键路径。循环依赖会导致死锁，因此必须在规划阶段消除。

资源分配为每个任务指定合适的 Agent 和必要的 Skills，同时考虑资源约束（最多 2 个并行）。并行数限制的原因是过多并行任务会增加协调成本并消耗过多内存。

可扩展性方面，优先使用灵活的架构，避免硬编码，支持配置驱动。任务之间应保持松耦合，使用接口而非具体实现，支持任务替换和扩展。

```python
# 不灵活（硬编码）
max_parallel = 2

# 灵活（可配置）
max_parallel = config.get("max_parallel_tasks", 2)
```

</planning_best_practices>

<execution_best_practices>

## 执行阶段

持续监控是执行阶段的关键。需要实时跟踪任务进度、记录执行时间、追踪资源使用，发现问题立即处理。监控的价值在于：越早发现问题，修复成本越低。

```python
def monitor_task_execution(task):
    """监控任务执行"""
    start_time = time.time()

    while task.is_running():
        # 检查是否超时
        if time.time() - start_time > task.timeout:
            alert("任务执行超时", task.id)

        # 检查资源使用
        if get_resource_usage(task) > threshold:
            alert("资源使用过高", task.id)

        time.sleep(5)
```

并行优化通过识别可并行的任务、优先调度 Ready 任务来最大化并行度（最多 2 个同时执行）。合理搭配 CPU 密集型和 I/O 密集型任务可以避免资源竞争、平衡负载。

```python
def schedule_tasks(tasks, max_parallel=2):
    """智能调度任务"""
    running = []
    pending = tasks.copy()

    while pending or running:
        # 补充槽位
        while len(running) < max_parallel and pending:
            # 查找就绪的任务
            ready_task = find_ready_task(pending)
            if ready_task:
                running.append(ready_task)
                pending.remove(ready_task)
                start_task(ready_task)
            else:
                break  # 没有就绪任务

        # 检查完成
        for task in running.copy():
            if task.is_completed():
                running.remove(task)
```

</execution_best_practices>

<common_pitfalls>

## 常见陷阱

过度规划表现为花费大量时间完善计划、规划时间超过执行时间、陷入分析瘫痪（analysis paralysis）。解决方案是设定规划时间上限，采用敏捷方法做刚刚好的规划，快速开始并在执行中调整。

```python
# 过度规划
planning_time = 2_hours
execution_time = 30_minutes

# 合理规划
planning_time = 20_minutes
execution_time = 2_hours
```

过早优化表现为在验证可行性前就优化性能、过度设计架构、引入不必要的复杂性。应遵循 YAGNI 原则（You Aren't Gonna Need It），先实现再优化，基于实际数据做决策。

```python
# 过早优化
def process_data(data):
    # 引入复杂的缓存、并发处理等
    # 但数据量实际很小

# 先简单实现
def process_data(data):
    # 简单直接的实现
    # 发现性能问题后再优化
```

</common_pitfalls>

<checklist>

## 检查清单

规划阶段：任务目标明确、任务分解遵循 MECE 原则、依赖关系形成 DAG（无循环）、每个任务都有明确的验收标准、Agent 和 Skills 分配合理、并行度不超过 2。

执行阶段：任务按依赖顺序执行、实时监控任务进度、记录执行日志、及时发现和处理异常、资源使用在合理范围内。

</checklist>
