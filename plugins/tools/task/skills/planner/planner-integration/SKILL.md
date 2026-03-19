---
description: Planner 集成指南 - Loop 集成、验证函数、高级用法
model: opus
context: fork
user-invocable: false
---

# Planner 集成指南

<scope>
为 Loop 命令提供 planner 集成的详细指导，包括基础集成、高级用法和验证函数。
</scope>

<basic_integration>

## 基础集成

### 调用 Planner

```python
planner_result = Agent(
    agent="task:planner",
    prompt=f"""设计执行计划：

任务目标：{task_description}

要求：
1. 分析项目结构（优先中等深度）
2. 收集：目标、依赖、现状、边界
3. 分解为原子子任务（MECE）
4. 建立依赖关系（DAG）
5. 分配 Agent 和 Skills（带中文注释）
6. 定义可量化验收标准
7. 返回简短报告（≤200字）

如果功能已存在且满足需求，返回空 tasks 数组。
"""
)
```

### 处理结果

```python
# 检查状态
if planner_result["status"] != "completed":
    raise Exception("计划设计失败")

# 处理问题
if "questions" in planner_result and planner_result["questions"]:
    user_response = AskUserQuestion(planner_result["questions"][0])
    planner_result = Agent(
        agent="task:planner",
        prompt=f"补充信息：{user_response}\n继续设计计划..."
    )

# 无需执行情况
if not planner_result["tasks"] or len(planner_result["tasks"]) == 0:
    print(f"✓ {planner_result['report']}")
    return None  # 无需执行

return planner_result
```

</basic_integration>

<validation_functions>

## 验证函数

### 验证计划质量

```python
def validate_plan(plan):
    """验证计划的合理性"""

    # 检查循环依赖
    if has_circular_dependency(plan["dependencies"]):
        raise Exception("发现循环依赖，请修正计划")

    # 检查并行度
    for group in plan["parallel_groups"]:
        if len(group) > 2:
            raise Exception(f"并行任务数超过限制（最多2个）：{group}")

    # 检查中文注释
    for task in plan["tasks"]:
        if "（" not in task["agent"]:
            raise Exception(f"Agent 缺少中文注释：{task['agent']}")
        for skill in task["skills"]:
            if "（" not in skill:
                raise Exception(f"Skill 缺少中文注释：{skill}")

    # 检查验收标准
    for task in plan["tasks"]:
        if not task["acceptance_criteria"]:
            raise Exception(f"任务 {task['id']} 缺少验收标准")
```

### 检查循环依赖

```python
def has_circular_dependency(dependencies):
    """使用拓扑排序检测循环依赖"""
    from collections import defaultdict, deque

    graph = defaultdict(list)
    in_degree = defaultdict(int)

    # 构建图
    for task, deps in dependencies.items():
        for dep in deps:
            graph[dep].append(task)
            in_degree[task] += 1

    # 拓扑排序
    queue = deque([node for node in graph if in_degree[node] == 0])
    sorted_count = 0

    while queue:
        node = queue.popleft()
        sorted_count += 1
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # 如果排序节点数少于总节点数，说明有环
    return sorted_count < len(graph)
```

</validation_functions>

<advanced_usage>

## 高级用法

### 融合深度研究结果

```python
planner_result = Agent(
    agent="task:planner",
    prompt=f"""设计执行计划：

任务目标：{user_task}
迭代编号：{iteration}

深度研究发现：
{research_result['summary']}

推荐方案：
{research_result['recommendations']}

要求：
1. 基于研究发现优化方案选择
2. 采用推荐的最佳实践
3. 设置质量目标：{quality_threshold} 分
4. 分解为 MECE 原子任务
...
"""
)
```

### 设置质量目标

```python
# 根据迭代轮次设置质量阈值
quality_thresholds = {
    1: 60,  # Foundation
    2: 75,  # Enhancement
    3: 85,  # Refinement
    4: 90   # Excellence
}

quality_threshold = quality_thresholds.get(iteration, 90)

# 在 planner prompt 中包含质量要求
planner_result = Agent(
    agent="task:planner",
    prompt=f"""...
质量目标：{quality_threshold} 分（功能、测试、性能、可维护性、安全性）
...
"""
)
```

### 迭代式规划

```python
# 第一次规划
planner_result = call_planner(user_task, iteration=1)

# 如果验收失败，重新规划
if verification_failed:
    planner_result = Agent(
        agent="task:planner",
        prompt=f"""基于失败反馈重新设计计划：

原任务：{user_task}
失败原因：{failure_reasons}
调整建议：{adjustment_suggestions}

要求：
1. 分析失败根本原因
2. 调整任务分解策略
3. 增强验收标准
4. 优化资源分配
...
"""
    )
```

</advanced_usage>

<best_practices>

## 最佳实践

### 规划阶段

1. **充分理解项目**：先完成 Tier 1 上下文学习
2. **收集四类信息**：目标、依赖、现状、边界
3. **应用 MECE 原则**：子任务独立且穷尽
4. **建立 DAG 依赖**：确保无循环依赖
5. **定义可量化标准**：每个任务都有明确验收标准

### 集成阶段

1. **验证计划质量**：使用 `validate_plan()` 验证
2. **处理边缘情况**：空 tasks、questions、验收失败
3. **保持状态一致**：更新 plan 文件状态
4. **记录决策**：保存规划决策到 `.claude/memory/`

### 常见陷阱

- ❌ 跳过项目理解直接规划
- ❌ 过度拆分简单任务
- ❌ 验收标准模糊不可量化
- ❌ 忽略循环依赖检查
- ❌ 并行度超过 2 个任务
- ❌ Agent/Skills 缺少中文注释

</best_practices>

<references>

详细文档参见：
- [planner-integration-basic.md](../planner-integration-basic.md)
- [planner-integration-advanced.md](../planner-integration-advanced.md)
- Skills(task:planner)
- [上下文学习指南](../planner-context-learning.md)

</references>
