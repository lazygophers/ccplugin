# Loop 迭代策略和要求 - 高级

本文档包含迭代终止条件、迭代优化技巧和持续改进。

## 迭代终止条件

### 正常终止

**所有验收标准通过**：
- 功能完整
- 测试通过
- 质量达标
- 无遗留问题

**示例**：
```
验收标准检查清单：
✓ 所有任务完成
✓ 测试覆盖率 ≥ 90%
✓ 所有测试通过
✓ Lint 检查 0 错误
✓ 性能满足要求
✓ 文档完整

→ 正常终止迭代
```

### 提前终止

**功能已存在**：
- Planner 发现功能已实现
- 返回空 tasks 数组
- 直接跳转到完成阶段

**用户请求终止**：
- 用户明确要求停止
- 记录当前进度
- 生成终止报告

### 异常终止

**超过最大停滞次数**：
- stalled_count >= max_stalled_attempts
- 建议人工介入
- 输出停滞分析报告

**不可恢复的错误**：
- 系统级别错误
- 无法修复的配置问题
- 资源完全不可用

## 迭代优化技巧

### 任务粒度控制

**合适的任务粒度**：
- 单个任务执行时间：10-30 分钟
- 太大：难以并行，风险高
- 太小：管理成本高，效率低

**拆分过大的任务**：
```python
# 原任务（太大）
task = "实现完整的用户管理模块"

# 拆分后（合适）
tasks = [
    "实现用户模型和数据库操作",
    "实现用户 CRUD API",
    "实现用户认证逻辑",
    "编写用户模块测试"
]
```

### 并行度优化

**最大化并行度**：
- 识别无依赖的任务
- 优先并行执行
- 最多 2 个任务并行

**减少等待时间**：
```python
# 顺序执行（慢）
execute(T1)  # 10 分钟
execute(T2)  # 10 分钟
# 总时间：20 分钟

# 并行执行（快）
parallel_execute([T1, T2])  # max(10, 10) = 10 分钟
# 总时间：10 分钟
```

### 依赖关系优化

**最小化依赖**：
- 减少不必要的依赖
- 打破循环依赖
- 使用接口隔离

**并行友好的依赖**：
```
❌ 不好的依赖设计：
T1 → T2 → T3 → T4 → T5
（完全串行，无法并行）

✓ 好的依赖设计：
     ┌─ T2
T1 ─┤
     └─ T3 ─┬─ T4
            └─ T5
（部分并行，效率更高）
```

### 任务优先级

**定义优先级**：
```python
task_priorities = {
    "critical": 4,  # 关键任务，必须立即执行
    "high": 3,      # 高优先级任务
    "medium": 2,    # 中等优先级任务
    "low": 1        # 低优先级任务
}
```

**优先级调度**：
```python
def schedule_tasks(tasks):
    """按优先级调度任务"""
    # 按优先级排序
    sorted_tasks = sorted(
        tasks,
        key=lambda t: task_priorities.get(t.priority, 2),
        reverse=True
    )

    # 优先执行高优先级任务
    for task in sorted_tasks:
        if can_execute(task):
            execute(task)
```

### 资源管理

**合理分配资源**：
```python
resource_allocation = {
    "cpu_intensive": {"cpu": 2, "memory": "2GB"},
    "io_intensive": {"cpu": 1, "memory": "1GB"},
    "memory_intensive": {"cpu": 1, "memory": "4GB"}
}

def allocate_resources(task):
    """为任务分配资源"""
    task_type = classify_task(task)
    return resource_allocation.get(task_type)
```

**避免资源竞争**：
```python
def check_resource_conflict(task1, task2):
    """检查任务间是否有资源冲突"""
    # 检查文件冲突
    if set(task1.files) & set(task2.files):
        return True

    # 检查 Agent 冲突
    if task1.agent == task2.agent and not supports_parallel(task1.agent):
        return True

    return False
```

## 持续改进

### 迭代回顾

**每次迭代后的回顾**：
1. 什么做得好？
2. 什么可以改进？
3. 下次如何做得更好？

**记录改进点**：
```python
iteration_retrospective = {
    "what_went_well": [
        "并行执行节省了时间",
        "测试覆盖率达到 95%"
    ],
    "what_to_improve": [
        "任务粒度太大，下次拆分更细",
        "依赖关系可以进一步优化"
    ],
    "action_items": [
        "创建任务拆分检查清单",
        "建立依赖关系审查流程"
    ]
}
```

### 度量和分析

**关键指标**：
- 迭代完成时间
- 任务返工率
- 并行度利用率
- 测试覆盖率

**趋势分析**：
```python
def analyze_iteration_trend(iterations):
    """分析迭代趋势"""
    metrics = {
        "avg_time": average([i.duration for i in iterations]),
        "success_rate": sum([i.success for i in iterations]) / len(iterations),
        "improvement": calculate_improvement(iterations)
    }
    return metrics
```

### 学习和知识积累

**记录最佳实践**：
```python
def record_best_practice(iteration):
    """记录迭代中的最佳实践"""
    best_practices = {
        "task_decomposition": extract_decomposition_pattern(iteration),
        "dependency_design": extract_dependency_pattern(iteration),
        "testing_strategy": extract_testing_pattern(iteration)
    }

    # 保存到知识库
    save_to_knowledge_base(best_practices)
```

**知识复用**：
```python
def apply_learned_patterns(task):
    """应用已学习的模式"""
    # 查找相似任务的模式
    similar_patterns = find_similar_patterns(task)

    # 应用最佳实践
    for pattern in similar_patterns:
        if pattern.applicable(task):
            apply_pattern(task, pattern)
```

### 质量提升

**质量目标递进**：
```python
quality_targets = {
    1: {"test_coverage": 80, "code_quality": 70},
    2: {"test_coverage": 90, "code_quality": 80},
    3: {"test_coverage": 95, "code_quality": 90}
}

def get_quality_target(iteration):
    """获取当前迭代的质量目标"""
    return quality_targets.get(iteration, quality_targets[3])
```

**质量检查**：
```python
def quality_gate_check(iteration, results):
    """质量门控检查"""
    target = get_quality_target(iteration)

    # 检查测试覆盖率
    if results["test_coverage"] < target["test_coverage"]:
        return False, f"测试覆盖率不达标：{results['test_coverage']}% < {target['test_coverage']}%"

    # 检查代码质量
    if results["code_quality"] < target["code_quality"]:
        return False, f"代码质量不达标：{results['code_quality']} < {target['code_quality']}"

    return True, "质量门控通过"
```
