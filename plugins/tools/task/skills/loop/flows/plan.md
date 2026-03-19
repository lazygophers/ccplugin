---
description: Loop 计划设计流程 - 深度研究、计划生成、计划确认
model: sonnet
context: fork
user-invocable: false
---

# Loop 计划设计流程

<scope>
在 Loop 的 Planning 阶段使用，负责：
1. 触发深度研究（第1轮、失败2次、质量不达标、复杂任务）
2. 调用 task:planner 生成执行计划
3. 基于 plan-confirmation-template.md 生成计划文档
4. 通过 AskUserQuestion 获取用户确认
</scope>

<execution_flow>

## 阶段0：提示词优化（Prompt Optimization）

仅在第一轮（iteration=0）执行，确保用户输入清晰可执行。

触发条件：
- loop 命令启动后的第一轮
- 用户原始输入已获取

```python
# 仅在第一轮执行
if iteration == 0:
    optimizer_result = Agent(
        agent="task:prompt-optimizer",
        prompt=f"""优化用户提示词：

原始输入：{user_task}

要求：
1. 评估质量（清晰度、完整性、可执行性，0-10分）
2. 综合得分 = (清晰度 + 完整性 + 可执行性) / 3
3. 质量 ≥ 8分：返回 status="no_optimization_needed"，静默跳过
4. 质量 < 8分：识别缺失的5W1H维度，通过SendMessage(@main)提问
5. 质量 < 6分：使用WebSearch搜索"prompt engineering best practices 2025"
6. 生成优化后的结构化提示词（Markdown格式）
7. 返回优化报告（≤100字）

提问不限次数，确保信息完整。
"""
    )

    # 质量高：静默跳过
    if optimizer_result["status"] == "no_optimization_needed":
        # 完全不输出任何信息，直接继续
        pass
    # 质量低：显示优化结果
    else:
        print(f"[MindFlow·{user_task}·提示词优化/0·completed]")
        print(f"优化报告：{optimizer_result['report']}")

        # 更新任务描述
        user_task = optimizer_result["optimized_prompt"]
        print(f"✓ 提示词已优化（质量：{optimizer_result['quality_score']['overall']:.1f}分）")
```

状态转换：
- 优化完成 → 深度研究（如需）或 计划设计
- 静默跳过 → 深度研究（如需）或 计划设计

## 阶段1：深度研究（可选）

触发条件：
- 第 1 轮迭代（了解最佳方案）
- 失败 2 次以上（根本原因分析）
- 质量不达标（分数 < 阈值 - 10）
- 复杂任务（planner 识别为高复杂度）

```python
if should_trigger_deep_research(iteration, failure_count, quality_score):
    research_result = Skill(
        skill="deepresearch:deep-research",
        args=f"研究任务：{user_task}\n重点：最佳实践、技术选型、潜在风险"
    )
    # 融合研究结果到 planner prompt
```

## 阶段2：计划生成

```python
iteration += 1

planner_result = Agent(
    agent="task:planner",
    prompt=f"""设计执行计划：

任务目标：{user_task}
迭代编号：{iteration}

要求：
1. 分析项目结构（优先中等深度）
2. 收集：目标、依赖、现状、边界
3. 分解为原子子任务（MECE）
4. 建立依赖关系（DAG）
5. 分配 Agent 和 Skills（带中文注释）
6. 定义可量化验收标准
7. 返回简短报告（≤200字）

如果功能已存在，返回空 tasks 数组。
"""
)

# 处理问题
if "questions" in planner_result and planner_result["questions"]:
    for question in planner_result["questions"]:
        user_answer = AskUserQuestion(question)
        planner_result = Agent(
            agent="task:planner",
            prompt=f"补充信息：{user_answer}\n继续设计计划..."
        )

# 无需执行情况
if not planner_result["tasks"] or len(planner_result["tasks"]) == 0:
    print(f"[MindFlow·{user_task}·计划设计/{iteration}·completed]")
    print(f"{planner_result['report']}")
    return "skip_execution"
```

## 阶段3：生成计划文档

```python
from pathlib import Path
import re
import json

plans_dir = Path(".claude/plans")
plans_dir.mkdir(parents=True, exist_ok=True)

# 强制保留用户语言字符（中文：\u4e00-\u9fff）
safe_task_name = re.sub(r'[^\w\u4e00-\u9fff]+', '-', user_task)[:50]
plan_md_path = plans_dir / f"{safe_task_name}-{iteration}.md"

# YAML frontmatter
frontmatter = f"""---
status: pending
created_at: {datetime.now().isoformat()}
iteration: {iteration}
task_count: {len(planner_result['tasks'])}
completed_count: 0
---
"""

# 调用 task:plan-formatter 格式化计划文档
formatted_plan = Agent(
    agent="task:plan-formatter",
    prompt=f"""将以下 JSON 转换为标准 Markdown 计划文档：

{json.dumps(planner_result, ensure_ascii=False, indent=2)}

YAML Frontmatter（必须放在文档开头）：
{frontmatter}

要求：
1. 严格遵循 template.md 格式
2. Mermaid 图单行文本，无 \\n
3. 包含完整的任务清单表格
"""
)

Write(str(plan_md_path), formatted_plan)

print(f"[MindFlow·{user_task}·计划设计/{iteration}·completed]")
print(planner_result["report"])
print(f"计划已生成：{plan_md_path}")
```

## 阶段4：计划确认

```python
print(f"[MindFlow·{user_task}·计划确认/{iteration}·准备预览]")
print(f"计划文件：{plan_md_path}")

Bash(
    command=f"uvx --from git+https://github.com/lazygophers/ccplugin.git@master md2html {plan_md_path}",
    description="将计划 MD 转换为 HTML 并在浏览器打开"
)

print("已在浏览器打开计划预览")
print(f"[MindFlow·{user_task}·计划确认/{iteration}·等待确认]")

user_decision = AskUserQuestion(
    question="执行计划已准备就绪，是否开始执行？",
    options=["立即执行", "重新设计"]
)

if user_decision == "重新设计":
    return "replan"
else:
    return "execute"
```

</execution_flow>

<state_transitions>

**状态转换**：
- 成功生成计划 → 计划确认
- 无需执行（空tasks） → 全部完成
- 用户选择"立即执行" → 任务执行
- 用户选择"重新设计" → 计划设计

</state_transitions>

<references>

详细实现参见：
- [loop-deep-iteration.md](../../deep-iteration/implementation.md#计划设计阶段融合研究结果)
- [plan-confirmation-template.md](../../plan-formatter/template.md)
- Skills(task:planner)

</references>
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
