---
agent: task:planner
description: 计划设计规范 - 收集项目信息、任务分解、依赖建模、agents/skills 分配的执行规范
model: opus
context: fork
user-invocable: false
---

# Skills(task:planner) - 计划设计规范

<scope>

当你需要为复杂任务设计执行计划时使用此 skill。适用于深入分析项目结构和技术栈、将复杂任务分解为可执行的子任务、建立任务依赖关系和并行执行策略、为每个任务分配合适的 Agent 和 Skills，以及 Loop 命令的计划设计（Planning / Plan）阶段。

</scope>

<core_principles>

MECE 分解原则要求子任务之间相互独立（Mutually Exclusive，无文件冲突，可独立执行）且完全穷尽（Collectively Exhaustive，覆盖所有必要工作，无遗漏）。

质量标准包括三个方面：可交付原子化（每个任务必须产生可验证的交付物）、可量化可验证（每个任务必须有明确的、可量化的验收标准）、依赖闭环（任务之间的依赖关系必须形成有向无环图 DAG）。

</core_principles>

<invocation>

调用 planner agent：

```python
# 基础调用
planner_result = Agent(
    agent="task:planner",
    prompt=f"""设计执行计划：

任务目标：{task_description}

要求：
1. 分析项目结构（优先中等深度，必要时深入）
2. 收集：目标、依赖、现状、边界
3. 分解为原子子任务（遵循 MECE 原则）
4. 建立依赖关系（DAG，无循环）
5. 分配 Agent 和 Skills（带中文注释）
6. 定义可量化的验收标准
7. 返回简短报告（≤200字）

如果功能已存在且满足需求，返回空 tasks 数组。
"""
)
```

处理 planner 结果：

```python
# 检查状态
if planner_result["status"] != "completed":
    raise Exception("计划设计失败")

# 检查是否有疑问需要用户确认
if "questions" in planner_result and planner_result["questions"]:
    user_response = AskUserQuestion(planner_result["questions"][0])
    planner_result = Agent(
        agent="task:planner",
        prompt=f"补充信息：{user_response}\n继续设计计划..."
    )

# 特殊情况：无需执行任务
if not planner_result["tasks"] or len(planner_result["tasks"]) == 0:
    print(f"✓ {planner_result['report']}")
    return  # 直接结束，无需执行

# 验证计划质量
validate_plan(planner_result)
```

验证计划质量：

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
```

</invocation>

<output_format>

标准输出（有任务需执行）：

```json
{
  "status": "completed",
  "report": "计划：3个子任务。T1：JWT 工具（coder）→ T2：认证中间件（coder）→ T3：测试覆盖（tester）。依赖：T2→T3。预计完成时间：2小时。",
  "tasks": [
    {
      "id": "T1",
      "description": "实现 JWT 工具函数",
      "agent": "coder（开发者）",
      "skills": ["golang:core（核心功能）"],
      "files": ["internal/auth/jwt.go"],
      "acceptance_criteria": [
        "生成和验证 Token 功能完整",
        "单元测试覆盖率 ≥ 90%"
      ],
      "dependencies": []
    }
  ],
  "dependencies": {"T2": ["T1"], "T3": ["T2"]},
  "parallel_groups": [["T1"], ["T2"], ["T3"]],
  "iteration_goal": "完成用户认证功能的实现和测试",
  "acceptance_criteria": ["所有子任务完成", "整体测试通过", "代码质量达标"]
}
```

特殊输出（无需执行任务）：当功能已存在且满足需求、没有找到需要改动的地方、或用户要求已被满足时，返回空 tasks 数组：

```json
{
  "status": "completed",
  "report": "分析结果：用户认证功能已在 internal/auth 模块完整实现。无需额外开发。",
  "tasks": [],
  "dependencies": {},
  "parallel_groups": [],
  "iteration_goal": "确认现有实现满足需求",
  "acceptance_criteria": ["确认功能完整性"]
}
```

</output_format>

<field_reference>

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| `status` | string | 执行状态：`completed` 或 `questions` | 是 |
| `report` | string | 简短报告（≤200字） | 是 |
| `tasks` | array | 任务列表（可为空数组） | 是 |
| `dependencies` | object | 依赖关系映射 | 是 |
| `parallel_groups` | array | 并行执行分组 | 是 |
| `iteration_goal` | string | 迭代目标 | 是 |
| `acceptance_criteria` | array | 整体验收标准 | 是 |
| `questions` | array | 需要用户确认的问题 | 否 |

Task 对象字段：

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `id` | string | 任务唯一标识 | `"T1"` |
| `description` | string | 任务描述 | `"实现 JWT 工具函数"` |
| `agent` | string | 执行 Agent（含中文注释） | `"coder（开发者）"` |
| `skills` | array | 所需 Skills（含中文注释） | `["golang:core（核心功能）"]` |
| `files` | array | 涉及的文件 | `["internal/auth/jwt.go"]` |
| `acceptance_criteria` | array | 验收标准（支持字符串或结构化对象） | 见 [结构化验收标准](planner-structured-criteria.md) |
| `dependencies` | array | 前置任务 ID 列表 | `["T1"]` |

结构化验收标准详见 [planner-structured-criteria.md](planner-structured-criteria.md)。

</field_reference>

<references>

- [结构化验收标准](planner-structured-criteria.md) - 精确匹配、量化阈值评估、字段定义、使用示例
- [上下文学习指南](planner-context-learning.md) - 三层上下文学习、项目理解、记忆系统、规范驱动计划
- [Agent/Skills 选择参考](planner-reference.md) - Agent 和 Skills 的选择指南、使用示例
- [避坑指南](planner-pitfalls.md) - 常见错误、最佳实践、验证检查清单
- [集成示例](planner-integration.md) - Loop 集成、验证函数、高级用法

</references>

<guidelines>

始终使用 `Agent(agent="task:planner", ...)` 调用，检查 `status` 字段确认执行状态，处理 `questions` 字段中的用户确认请求。验证依赖关系无循环（使用拓扑排序），验证并行度不超过 2，验证 Agent/Skills 带中文注释，处理空 tasks 数组的特殊情况。

不要跳过计划验证步骤，不要忽略 planner 返回的问题，不要修改 planner 返回的 JSON 结构。常见陷阱包括：过度拆分任务（应合并为原子任务）、验收标准模糊（应可量化）、缺少中文注释、循环依赖、并行度超限。

</guidelines>
