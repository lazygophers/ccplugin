# Planner 基础集成

本文档包含 Planner 的基础集成示例和验证函数。

<loop_integration>

## Loop 命令中的使用

在 Loop 命令的计划设计阶段调用 Planner。这是最常见的集成方式，Planner 作为 Loop 的第一步分析项目并生成执行计划。

```python
def planning_phase(task_description, iteration):
    """Loop 命令计划设计（Planning / Plan）阶段"""

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
            planner_result = Agent(
                agent="task:planner",
                prompt=f"补充信息：{answer}\n继续设计计划..."
            )

    validate_plan(planner_result)

    if not planner_result["tasks"]:
        print(f"[MindFlow·{task_description}·{iteration + 1}/1·completed]")
        print(f"✓ {planner_result['report']}")
        return None

    print(f"[MindFlow·{task_description}·计划设计/{iteration + 1}·completed]")
    print(f"✓ 计划设计完成：{planner_result['report']}")

    return planner_result
```

</loop_integration>

<validation>

## 验证函数实现

计划验证确保生成的计划满足质量要求。验证覆盖依赖关系、并行度、注释格式和验收标准四个维度，任何一个不通过都会阻止计划执行，因为错误的计划会导致后续所有步骤出错。

```python
def validate_plan(plan):
    """验证计划的合理性"""
    if has_circular_dependency(plan["dependencies"]):
        raise Exception("发现循环依赖，请修正计划")

    for group in plan["parallel_groups"]:
        if len(group) > 2:
            raise Exception(f"并行任务数超过限制（最多2个）：{group}")

    for task in plan["tasks"]:
        if "（" not in task["agent"]:
            raise Exception(f"Agent 缺少中文注释：{task['agent']}")
        for skill in task["skills"]:
            if "（" not in skill:
                raise Exception(f"Skill 缺少中文注释：{skill}")

    for task in plan["tasks"]:
        if not task["acceptance_criteria"]:
            raise Exception(f"任务 {task['id']} 缺少验收标准")
        for criterion in task["acceptance_criteria"]:
            if isinstance(criterion, dict):
                validate_structured_criterion(criterion, task['id'])

    print("✓ 计划验证通过")


def validate_structured_criterion(criterion, task_id):
    """验证结构化验收标准的字段完整性"""
    required_fields = ['id', 'type', 'description', 'priority']
    for field in required_fields:
        if field not in criterion:
            raise Exception(f"任务 {task_id} 的验收标准缺少必需字段: {field}")

    if criterion['priority'] not in ['required', 'recommended']:
        raise Exception(
            f"任务 {task_id} 验收标准 {criterion['id']} 的 priority 必须为 'required' 或 'recommended'"
        )

    criterion_type = criterion['type']
    if criterion_type == 'exact_match':
        if 'verification_method' not in criterion:
            raise Exception(
                f"任务 {task_id} 验收标准 {criterion['id']} 类型为 exact_match，缺少 verification_method 字段"
            )
    elif criterion_type == 'quantitative_threshold':
        for field in ['metric', 'operator', 'threshold']:
            if field not in criterion:
                raise Exception(
                    f"任务 {task_id} 验收标准 {criterion['id']} 类型为 quantitative_threshold，缺少 {field} 字段"
                )
        valid_operators = ['>=', '<=', '>', '<', '==']
        if criterion['operator'] not in valid_operators:
            raise Exception(
                f"任务 {task_id} 验收标准 {criterion['id']} 的 operator 必须为: {valid_operators}"
            )
    else:
        raise Exception(
            f"任务 {task_id} 验收标准 {criterion['id']} 的 type 不支持: {criterion_type}"
        )
```

循环依赖检测使用 DFS 遍历依赖图，检测是否存在回边（back edge）。这是标准的拓扑排序前置检查。

```python
def has_circular_dependency(dependencies):
    """检测是否存在循环依赖"""
    graph = defaultdict(list)
    for task, deps in dependencies.items():
        for dep in deps:
            graph[dep].append(task)

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
                return True
        rec_stack.remove(node)
        return False

    all_tasks = set(dependencies.keys()) | set(
        dep for deps in dependencies.values() for dep in deps
    )
    for task in all_tasks:
        if task not in visited:
            if dfs(task):
                return True
    return False
```

</validation>

<result_handling>

## 处理 Planner 结果

完整的结果处理流程依次检查状态、处理疑问、处理空任务列表、验证质量、输出摘要。

```python
def handle_planner_result(planner_result, task_description):
    """处理 Planner 返回结果"""
    if planner_result["status"] != "completed":
        raise Exception(f"计划设计失败：{planner_result.get('error', 'Unknown error')}")

    if "questions" in planner_result and planner_result["questions"]:
        user_response = AskUserQuestion(planner_result["questions"][0])
        planner_result = Agent(
            agent="task:planner",
            prompt=f"补充信息：{user_response}\n继续设计计划..."
        )

    if not planner_result["tasks"] or len(planner_result["tasks"]) == 0:
        print(f"✓ {planner_result['report']}")
        return None

    validate_plan(planner_result)

    print(f"✓ 计划设计完成：{planner_result['report']}")
    print(f"\n任务总数：{len(planner_result['tasks'])}")
    print(f"并行组数：{len(planner_result['parallel_groups'])}")
    print(f"迭代目标：{planner_result['iteration_goal']}")

    return planner_result
```

</result_handling>
