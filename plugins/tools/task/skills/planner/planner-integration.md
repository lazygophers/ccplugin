# Planner 集成示例

本文档包含在不同场景下集成和使用 Planner 的示例代码。

## Loop 命令中的使用

### 基础集成

在 Loop 命令的计划设计阶段调用 Planner：

```python
def planning_phase(task_description, iteration):
    """Loop 命令计划设计（Planning / Plan）阶段"""

    # 调用 planner agent
    planner_result = Agent(
        agent="task:planner",
        prompt=f"""设计执行计划：

任务目标：{task_description}

当前迭代：第 {iteration + 1} 轮

要求：
1. 分析项目结构和技术栈
2. 收集目标、依赖、现状、边界
3. 分解为原子子任务（MECE）
4. 建立依赖关系（DAG）
5. 分配 Agent 和 Skills
6. 定义可量化验收标准
7. 返回简短报告（≤200字）

如果功能已存在，返回空 tasks 数组。
"""
    )

    # 处理疑问
    if "questions" in planner_result and planner_result["questions"]:
        for question in planner_result["questions"]:
            answer = AskUserQuestion(question)
            # 补充信息后重新生成计划
            planner_result = Agent(
                agent="task:planner",
                prompt=f"补充信息：{answer}\n继续设计计划..."
            )

    # 验证计划
    validate_plan(planner_result)

    # 特殊情况：无需执行
    if not planner_result["tasks"]:
        print(f"[MindFlow·{task_description}·{iteration + 1}/1·completed]")
        print(f"✓ {planner_result['report']}")
        return None  # 结束 loop

    # 输出计划
    print(f"[MindFlow·{task_description}·计划设计/{iteration + 1}·completed]")
    print(f"✓ 计划设计完成：{planner_result['report']}")

    return planner_result
```

---

## 验证函数实现

### 完整验证函数

```python
def validate_plan(plan):
    """验证计划的合理性

    Args:
        plan: Planner 返回的计划结果

    Raises:
        Exception: 验证失败时抛出异常
    """

    # 检查依赖关系是否存在循环
    if has_circular_dependency(plan["dependencies"]):
        raise Exception("发现循环依赖，请修正计划")

    # 检查并行度
    for group in plan["parallel_groups"]:
        if len(group) > 2:
            raise Exception(f"并行任务数超过限制（最多2个）：{group}")

    # 检查 Agent/Skills 格式
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

    print("✓ 计划验证通过")
```

### 循环依赖检测

```python
def has_circular_dependency(dependencies):
    """检测是否存在循环依赖

    Args:
        dependencies: 依赖关系字典 {"T2": ["T1"], "T3": ["T2"]}

    Returns:
        bool: True 表示存在循环依赖
    """
    # 构建图
    graph = defaultdict(list)
    for task, deps in dependencies.items():
        for dep in deps:
            graph[dep].append(task)

    # DFS 检测循环
    visited = set()
    rec_stack = set()

    def dfs(node):
        visited.add(node)
        rec_stack.add(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True  # 发现循环

        rec_stack.remove(node)
        return False

    # 检查所有节点
    all_tasks = set(dependencies.keys()) | set(
        dep for deps in dependencies.values() for dep in deps
    )

    for task in all_tasks:
        if task not in visited:
            if dfs(task):
                return True

    return False
```

---

## 处理 Planner 结果

### 完整处理流程

```python
def handle_planner_result(planner_result, task_description):
    """处理 Planner 返回结果

    Args:
        planner_result: Planner agent 的返回结果
        task_description: 任务描述

    Returns:
        dict: 处理后的计划，或 None（如果无需执行）
    """

    # 1. 检查状态
    if planner_result["status"] != "completed":
        raise Exception(f"计划设计失败：{planner_result.get('error', 'Unknown error')}")

    # 2. 检查是否有疑问需要用户确认
    if "questions" in planner_result and planner_result["questions"]:
        # 通过 AskUserQuestion 向用户确认
        user_response = AskUserQuestion(planner_result["questions"][0])

        # 重新调用 planner，补充用户回答
        planner_result = Agent(
            agent="task:planner",
            prompt=f"补充信息：{user_response}\n继续设计计划..."
        )

    # 3. 特殊情况：无需执行任务
    if not planner_result["tasks"] or len(planner_result["tasks"]) == 0:
        print(f"✓ {planner_result['report']}")
        return None  # 直接结束，无需执行

    # 4. 验证计划质量
    validate_plan(planner_result)

    # 5. 输出计划摘要
    print(f"✓ 计划设计完成：{planner_result['report']}")
    print(f"\n任务总数：{len(planner_result['tasks'])}")
    print(f"并行组数：{len(planner_result['parallel_groups'])}")
    print(f"迭代目标：{planner_result['iteration_goal']}")

    return planner_result
```

---

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
