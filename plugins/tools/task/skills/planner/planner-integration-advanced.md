# Planner 高级集成

本文档包含 Planner 的自定义场景集成、高级用法和调试测试。

## 自定义场景集成

### 场景 1: 单次任务规划

```python
def plan_single_task(description):
    """为单次任务创建执行计划

    Args:
        description: 任务描述

    Returns:
        dict: 执行计划
    """
    planner_result = Agent(
        agent="task:planner",
        prompt=f"""设计执行计划：

任务目标：{description}

要求：
1. 分析项目结构（中等深度）
2. 分解为原子子任务
3. 建立依赖关系
4. 分配 Agent 和 Skills（带中文注释）
5. 定义验收标准

如果功能已存在，返回空 tasks 数组。
"""
    )

    return handle_planner_result(planner_result, description)
```

### 场景 2: 增量规划

```python
def plan_incremental(description, previous_plan, completed_tasks):
    """基于之前的计划进行增量规划

    Args:
        description: 新的任务描述
        previous_plan: 之前的执行计划
        completed_tasks: 已完成的任务列表

    Returns:
        dict: 增量执行计划
    """
    planner_result = Agent(
        agent="task:planner",
        prompt=f"""设计增量执行计划：

新任务目标：{description}

之前的计划：
{json.dumps(previous_plan, indent=2, ensure_ascii=False)}

已完成任务：
{json.dumps(completed_tasks, indent=2, ensure_ascii=False)}

要求：
1. 基于已完成的任务进行规划
2. 避免重复已完成的工作
3. 确保与之前计划兼容
4. 返回增量任务列表
"""
    )

    return handle_planner_result(planner_result, description)
```

### 场景 3: 重新规划

```python
def replan_after_failure(description, failed_tasks, failure_reasons):
    """失败后重新规划

    Args:
        description: 原任务描述
        failed_tasks: 失败的任务列表
        failure_reasons: 失败原因

    Returns:
        dict: 重新规划的执行计划
    """
    planner_result = Agent(
        agent="task:planner",
        prompt=f"""重新设计执行计划：

任务目标：{description}

失败任务：
{json.dumps(failed_tasks, indent=2, ensure_ascii=False)}

失败原因：
{json.dumps(failure_reasons, indent=2, ensure_ascii=False)}

要求：
1. 分析失败原因
2. 调整任务分解策略
3. 避免重复相同错误
4. 返回新的执行计划
"""
    )

    return handle_planner_result(planner_result, description)
```

---

## 高级用法

### 条件规划

```python
def conditional_planning(description, conditions):
    """基于条件进行规划

    Args:
        description: 任务描述
        conditions: 条件字典（如技术栈、环境等）

    Returns:
        dict: 执行计划
    """
    planner_result = Agent(
        agent="task:planner",
        prompt=f"""设计执行计划：

任务目标：{description}

条件约束：
{json.dumps(conditions, indent=2, ensure_ascii=False)}

要求：
1. 考虑条件约束
2. 选择合适的技术方案
3. 分配合适的 Agent 和 Skills
4. 定义验收标准
"""
    )

    return handle_planner_result(planner_result, description)
```

### 分阶段规划

```python
def phased_planning(description, phase):
    """分阶段规划

    Args:
        description: 任务描述
        phase: 当前阶段（foundation / enhancement / refinement）

    Returns:
        dict: 执行计划
    """
    phase_goals = {
        "foundation": "完成核心功能，建立基础架构",
        "enhancement": "完善功能细节，添加测试",
        "refinement": "优化和重构，补充文档"
    }

    planner_result = Agent(
        agent="task:planner",
        prompt=f"""设计执行计划（{phase} 阶段）：

任务目标：{description}

当前阶段目标：{phase_goals[phase]}

要求：
1. 专注于当前阶段目标
2. 分解为阶段性任务
3. 定义阶段验收标准
4. 返回阶段计划
"""
    )

    return handle_planner_result(planner_result, description)
```

---

## 调试和测试

### 调试模式

```python
def plan_with_debug(description, debug=True):
    """带调试信息的规划

    Args:
        description: 任务描述
        debug: 是否开启调试模式

    Returns:
        dict: 执行计划
    """
    planner_result = Agent(
        agent="task:planner",
        prompt=f"设计执行计划：{description}"
    )

    if debug:
        print("\n=== Planner Debug Info ===")
        print(f"Status: {planner_result['status']}")
        print(f"Tasks: {len(planner_result.get('tasks', []))}")
        print(f"Dependencies: {planner_result.get('dependencies', {})}")
        print(f"Parallel Groups: {planner_result.get('parallel_groups', [])}")
        print("========================\n")

    return handle_planner_result(planner_result, description)
```

### 模拟测试

```python
def test_planner():
    """测试 Planner 功能"""

    # 测试用例 1: 正常规划
    plan1 = plan_single_task("实现用户认证功能")
    assert plan1 is not None
    assert len(plan1["tasks"]) > 0

    # 测试用例 2: 功能已存在
    plan2 = plan_single_task("实现已存在的功能")
    assert plan2 is None  # 应该返回 None

    # 测试用例 3: 验证依赖关系
    plan3 = plan_single_task("复杂的多任务项目")
    assert not has_circular_dependency(plan3["dependencies"])

    print("✓ 所有测试通过")
```
