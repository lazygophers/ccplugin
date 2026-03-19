# Loop 规划和执行最佳实践

本文档包含 MindFlow Loop 规划和执行阶段的最佳实践。

## 规划阶段最佳实践

### 充分规划

**目标明确**：
- 明确定义任务目标
- 识别关键交付物
- 设定可量化的成功标准

**任务分解**：
- 使用 MECE 原则（互斥且完全穷尽）
- 每个任务都是原子性的
- 避免过度拆分或拆分不足

**依赖建模**：
- 识别任务间的依赖关系
- 确保依赖关系形成 DAG（有向无环图）
- 标注关键路径

**资源分配**：
- 为每个任务分配合适的 Agent
- 指定必要的 Skills
- 考虑资源约束（最多 2 个并行）

### 可扩展性

**选择可扩展的方案**：
- 优先使用灵活的架构
- 避免硬编码
- 支持配置驱动

**支持灵活调整**：
```python
# ❌ 不灵活（硬编码）
max_parallel = 2

# ✓ 灵活（可配置）
max_parallel = config.get("max_parallel_tasks", 2)
```

**避免过度耦合**：
- 任务之间松耦合
- 使用接口而非具体实现
- 支持任务替换和扩展

---

## 执行阶段最佳实践

### 持续监控

**实时跟踪任务进度**：
- 监控任务状态变化
- 记录执行时间
- 追踪资源使用

**识别低效或失败**：
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

**及时调整策略**：
- 发现问题立即处理
- 动态调整并行度
- 必要时重新规划

### 并行优化

**最大化并行度**：
- 识别可并行的任务
- 优先调度 Ready 任务
- 最多 2 个任务同时执行

**最小化等待时间**：
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

**优化资源利用**：
- CPU 密集型和 I/O 密集型任务搭配
- 避免资源竞争
- 平衡负载

---

## 常见陷阱

### 1. 过度规划

**表现**：
- 花费大量时间完善计划
- 规划的时间超过执行时间
- 分析瘫痪（analysis paralysis）

**解决方案**：
- 设定规划时间上限
- 采用敏捷方法：刚刚好的规划
- 快速开始，在执行中调整

```python
# ❌ 过度规划
planning_time = 2_hours
execution_time = 30_minutes

# ✓ 合理规划
planning_time = 20_minutes
execution_time = 2_hours
```

### 2. 过早优化

**表现**：
- 在验证可行性前就优化性能
- 过度设计架构
- 引入不必要的复杂性

**解决方案**：
- 先实现，再优化
- 基于实际数据优化
- 遵循 YAGNI 原则（You Aren't Gonna Need It）

```python
# ❌ 过早优化
def process_data(data):
    # 引入复杂的缓存、并发处理等
    # 但数据量实际很小

# ✓ 先简单实现
def process_data(data):
    # 简单直接的实现
    # 发现性能问题后再优化
```

---

## 检查清单

### 规划阶段检查清单

- [ ] 任务目标明确
- [ ] 任务分解遵循 MECE 原则
- [ ] 依赖关系形成 DAG（无循环）
- [ ] 每个任务都有明确的验收标准
- [ ] Agent 和 Skills 分配合理
- [ ] 并行度不超过 2

### 执行阶段检查清单

- [ ] 任务按依赖顺序执行
- [ ] 实时监控任务进度
- [ ] 记录执行日志
- [ ] 及时发现和处理异常
- [ ] 资源使用在合理范围内
