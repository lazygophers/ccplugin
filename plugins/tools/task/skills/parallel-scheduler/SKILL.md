---
description: 智能并行调度 - 基于任务复杂度动态调整并行度，优化任务执行效率
context: fork
user-invocable: false
---

<!-- STATIC_CONTENT: Cacheable -->

# Skills(parallel-scheduler) - 智能并行调度

<scope>

当你需要为任务执行阶段智能调度并行任务时使用此 skill。适用于动态评估任务复杂度、识别可并行任务、检测资源冲突、动态调整并行度（2-5 个槽位），以及 Loop 命令的任务执行（Execution / Do）阶段的智能调度。

</scope>

<core_principles>

**复杂度驱动调度**：基于任务的文件数、依赖深度、预估 token、文件冲突四个维度综合评估复杂度，动态决定并行/串行执行。

**用户约束优先**：并行度上限尊重用户配置（默认 2，最大 5），绝不超过用户指定值。

**资源冲突检测**：共享文件写入的任务必须串行执行，避免竞态条件。

</core_principles>

<complexity_evaluation>

## 复杂度评估模型

任务复杂度由四个维度加权计算，详见 [complexity-analyzer.md](complexity-analyzer.md)。

**维度权重**：

| 维度 | 权重 | 低复杂度 | 高复杂度 |
|------|------|---------|---------|
| 涉及文件数 | 30% | 1-2 个文件 | 5+ 个文件 |
| 依赖深度 | 25% | 无前置依赖 | 3+ 层依赖链 |
| 预估 token | 20% | < 10K tokens | > 50K tokens |
| 文件冲突 | 25% | 无共享文件 | 有共享文件（禁止并行） |

**复杂度分数**：0-100，< 30 为低复杂度，30-70 为中复杂度，> 70 为高复杂度。

</complexity_evaluation>

<parallel_rules>

## 并行度计算规则

| 场景 | 并行度 | 条件 |
|------|--------|------|
| 全部低复杂度 | 最大（默认 2，配置最大 5） | 无文件冲突 |
| 混合复杂度 | 2 | 高复杂度任务独占 1 槽位 |
| 存在文件冲突 | 1（串行） | 冲突任务必须串行 |
| 用户配置覆盖 | 用户指定值 | **绝不超过用户约束** |

**用户约束加载**：

```python
# 从 .claude/task.local.md 或环境变量加载
max_parallel_config = load_user_config().get("max_parallel_tasks", 2)

# 确保不超过最大限制
max_parallel = min(max_parallel_config, 5)
```

</parallel_rules>

<invocation>

## 调用方式

```python
from task.parallel_scheduler import schedule_parallel_tasks

# 获取待执行任务
ready_tasks = [task for task in all_tasks if is_ready(task)]

# 评估任务复杂度
task_complexities = {}
for task in ready_tasks:
    complexity = Agent(
        agent="task:complexity-analyzer",
        prompt=f"""评估任务复杂度：

任务 ID：{task['id']}
涉及文件：{task['files']}
依赖任务：{task['dependencies']}
Agent：{task['agent']}
Skills：{task['skills']}

要求：
1. 计算涉及文件数维度得分（30%）
2. 计算依赖深度维度得分（25%）
3. 估算 token 消耗维度得分（20%）
4. 检测文件冲突维度得分（25%）
5. 返回综合复杂度分数（0-100）
"""
    )
    task_complexities[task['id']] = complexity['score']

# 检测文件冲突
file_map = {}
for task in ready_tasks:
    for file in task['files']:
        if file not in file_map:
            file_map[file] = []
        file_map[file].append(task['id'])

conflicting_tasks = [
    tasks for tasks in file_map.values() if len(tasks) > 1
]

# 计算并行度
max_parallel = load_user_config().get("max_parallel_tasks", 2)
max_parallel = min(max_parallel, 5)  # 硬上限

if conflicting_tasks:
    # 存在文件冲突，串行执行
    parallel_degree = 1
elif all(score < 30 for score in task_complexities.values()):
    # 全部低复杂度
    parallel_degree = max_parallel
else:
    # 混合复杂度，使用默认值
    parallel_degree = 2

# 选择并行任务
parallel_batch = select_parallel_batch(
    ready_tasks,
    task_complexities,
    parallel_degree,
    file_map
)

print(f"[ParallelScheduler] 并行度：{parallel_degree}/{max_parallel}（用户约束）")
print(f"[ParallelScheduler] 本批次任务：{[t['id'] for t in parallel_batch]}")
```

**冲突检测示例**：

```python
# 场景：T1 和 T2 都修改 config.py
tasks = [
    {"id": "T1", "files": ["config.py", "utils.py"]},
    {"id": "T2", "files": ["config.py", "tests.py"]},
    {"id": "T3", "files": ["models.py"]}
]

# 检测结果：T1 和 T2 冲突 → 必须串行
# 调度方案：
# - Batch 1: T1, T3 并行（无冲突）
# - Batch 2: T2（T1 完成后）
```

</invocation>

<integration_with_loop>

## 与 Loop 执行阶段集成

在 `detailed-flow.md` 的任务执行（Execution）阶段，替换固定并行为智能调度：

**修改前**（固定并行）：

```python
# 固定最多 2 个并行
max_parallel = 2
parallel_tasks = ready_tasks[:max_parallel]
```

**修改后**（智能调度）：

```python
# 智能评估复杂度和冲突
from task.parallel_scheduler import schedule_parallel_tasks

parallel_batch = schedule_parallel_tasks(
    ready_tasks=ready_tasks,
    all_tasks=all_tasks,
    user_config=load_user_config()
)

print(f"[MindFlow·任务执行] 智能调度：{len(parallel_batch)} 个任务并行")
```

</integration_with_loop>

<output_format>

智能调度器返回格式：

```json
{
  "parallel_batch": ["T1", "T3"],
  "parallel_degree": 2,
  "user_max_parallel": 2,
  "complexity_scores": {
    "T1": 25,
    "T2": 78,
    "T3": 18
  },
  "conflicts_detected": [
    {"files": ["config.py"], "tasks": ["T1", "T2"]}
  ],
  "scheduling_reason": "T1 和 T3 低复杂度无冲突，T2 高复杂度待下批次"
}
```

</output_format>

<references>

- [complexity-analyzer.md](complexity-analyzer.md) - 任务复杂度分析器（四维度评估模型）
- [../execute/SKILL.md](../execute/SKILL.md) - 任务执行规范
- [../loop/detailed-flow.md](../loop/detailed-flow.md) - Loop 详细执行流程

</references>

<guidelines>

**必须做**：
- 始终尊重用户配置的并行度上限（默认 2，最大 5）
- 检测文件冲突的任务必须串行执行
- 优先调度低复杂度任务以提高并行效率
- 记录调度决策原因便于可观测性

**禁止做**：
- 不要超过用户配置的并行度上限
- 不要并行执行有文件冲突的任务
- 不要忽略任务复杂度直接并行
- 不要硬编码并行度（必须动态计算）

**常见陷阱**：
- 忽略用户约束导致并行度超限
- 未检测文件冲突导致竞态条件
- 高复杂度任务强行并行导致资源耗尽

</guidelines>

<!-- /STATIC_CONTENT -->
