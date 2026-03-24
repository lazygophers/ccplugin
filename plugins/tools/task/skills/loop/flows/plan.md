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
4. 通过 EnterPlanMode/ExitPlanMode 控制计划审查流程（首次和用户重新设计）
5. 智能跳过：adjuster/verifier 触发的重规划自动批准，无需用户确认
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

## 阶段2-4：计划设计与确认（Plan Mode）

**智能路径选择**：根据 `replan_trigger` 决定是使用 Plan 模式还是直接生成。

| 场景 | `iteration` | `replan_trigger` | 流程 |
|------|-------------|------------------|------|
| 首次规划 | 1 | None | ✓ Plan 模式 |
| 用户主动重新设计 | >1 | "user" | ✓ Plan 模式 |
| Adjuster 自动重新规划 | >1 | "adjuster" | ✗ 直接生成并自动批准 |
| Verifier 建议优化 | >1 | "verifier" | ✗ 直接生成并自动批准 |

```python
from pathlib import Path
import re
import json

iteration += 1
print(f"[MindFlow·{user_task}·计划设计/{iteration}·启动]")

# 检查智能跳过条件
replan_trigger = context.get("replan_trigger", None)

if iteration > 1 and replan_trigger in ["adjuster", "verifier"]:
    # === 路径 A：自动重规划（跳过 Plan 模式）===
    print(f"[MindFlow] 自动重新规划（触发来源：{replan_trigger}），跳过 Plan 模式")

    # 直接调用 planner（非 plan 模式）
    user_feedback = context.get("user_feedback", "")
    planner_prompt = f"""设计执行计划：

任务目标：{user_task}
迭代编号：{iteration}
"""

    if user_feedback:
        planner_prompt += f"""
用户反馈（上一轮）：{user_feedback}
请根据用户反馈调整计划。
"""
        del context["user_feedback"]

    planner_prompt += """
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

    planner_result = Agent(
        agent="task:planner",
        description="设计任务执行计划",
        prompt=planner_prompt
    )

    # 处理 planner 的问题
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

    # 生成计划文档（自动重规划也需要更新计划文件）
    plans_dir = Path(".claude/plans")
    plans_dir.mkdir(parents=True, exist_ok=True)

    safe_task_name = re.sub(r'[^\w\u4e00-\u9fff]+', '-', user_task)[:50]
    plan_md_path = plans_dir / f"{safe_task_name}-{iteration}.md"

    frontmatter = f"""---
status: pending
created_at: {datetime.now().isoformat()}
iteration: {iteration}
task_count: {len(planner_result['tasks'])}
completed_count: 0
---
"""

    formatted_plan = Agent(
        agent="task:plan-formatter",
        description="格式化计划为标准 Markdown",
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
    print(f"[MindFlow] 计划已生成：{plan_md_path}")

    # 自动批准
    print(f"[MindFlow·{user_task}·计划确认/{iteration}·auto_approved]")
    print(f"[MindFlow]   原因：已在{'调整阶段' if replan_trigger == 'adjuster' else '验证阶段'}告知用户")
    context["replan_trigger"] = None
    context["plan_md_path"] = str(plan_md_path)

    return "execute"

else:
    # === 路径 B：Plan 模式（首次或用户重新设计）===
    print(f"[MindFlow] 进入 Plan 模式进行计划设计...")

    # 进入 plan 模式
    EnterPlanMode()

    # Phase 1: 深度研究（可选）
    if should_trigger_deep_research(iteration, failure_count, quality_score):
        print(f"[MindFlow] 执行深度研究...")
        research_result = Agent(
            subagent_type="Explore",
            description="深度研究最佳实践",
            prompt=f"研究任务：{user_task}\n重点：最佳实践、技术选型、潜在风险"
        )

    # Phase 2: 设计计划
    print(f"[MindFlow] 正在设计执行计划...")

    user_feedback = context.get("user_feedback", "")
    planner_prompt = f"""设计执行计划：

任务目标：{user_task}
迭代编号：{iteration}
"""

    if user_feedback:
        planner_prompt += f"""
用户反馈（上一轮）：{user_feedback}
请根据用户反馈调整计划。
"""
        del context["user_feedback"]

    planner_prompt += """
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

    planner_result = Agent(
        subagent_type="Plan",  # 使用 Plan agent 类型
        agent="task:planner",
        description="设计任务执行计划",
        prompt=planner_prompt
    )

    # 处理 planner 的问题
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
        # 退出 plan 模式（无需执行）
        ExitPlanMode()
        return "skip_execution"

    # Phase 3: 格式化计划文档
    print(f"[MindFlow] 正在格式化计划文档...")

    # 从系统消息获取计划文件路径
    # plan_file_path 应该从 plan 模式系统消息中获取
    # 如果无法获取，使用默认路径
    import os
    plan_file_path = os.getenv("PLAN_FILE_PATH")
    if not plan_file_path:
        # 降级：使用自定义路径
        plans_dir = Path(".claude/plans")
        plans_dir.mkdir(parents=True, exist_ok=True)
        safe_task_name = re.sub(r'[^\w\u4e00-\u9fff]+', '-', user_task)[:50]
        plan_file_path = str(plans_dir / f"{safe_task_name}-{iteration}.md")

    frontmatter = f"""---
status: pending
created_at: {datetime.now().isoformat()}
iteration: {iteration}
task_count: {len(planner_result['tasks'])}
completed_count: 0
---
"""

    formatted_plan = Agent(
        agent="task:plan-formatter",
        description="格式化计划为标准 Markdown",
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

    # Phase 4: 写入计划文件
    Write(plan_file_path, formatted_plan)

    print(f"[MindFlow·{user_task}·计划设计/{iteration}·completed]")
    print(planner_result["report"])
    print(f"[MindFlow] 计划已生成：{plan_file_path}")

    # Phase 5: 退出 plan 模式并请求用户批准
    print(f"[MindFlow·{user_task}·计划确认/{iteration}·等待确认]")

    exit_result = ExitPlanMode()

    # 处理用户决策
    if exit_result.get("approved", False):
        # 用户批准
        print(f"[MindFlow] ✓ 用户批准计划，准备执行")
        context["replan_trigger"] = None
        context["plan_md_path"] = plan_file_path

        # 保存检查点
        save_checkpoint(
            user_task=user_task,
            iteration=iteration,
            phase="confirmation",
            context=context,
            plan_md_path=plan_file_path
        )

        return "execute"
    else:
        # 用户拒绝
        print(f"[MindFlow] 用户选择重新设计计划")

        # 尝试从计划文件提取用户标注/反馈
        plan_content = Read(plan_file_path)
        user_feedback = extract_user_feedback(plan_content)

        if user_feedback:
            print(f"[MindFlow] 检测到用户反馈：{user_feedback[:100]}...")
            context["user_feedback"] = user_feedback

        # 标记为用户触发的重新规划
        context["replan_trigger"] = "user"

        return "replan"


def extract_user_feedback(plan_content: str) -> str:
    """
    从计划文件中提取用户标注的反馈

    用户可能的标注方式：
    1. Markdown 注释：<!-- 用户反馈：... -->
    2. 特殊标记：[反馈] ... 或 [TODO] ...
    3. 删除线标记：~~原方案~~ 改为 新方案
    """
    import re

    feedback_parts = []

    # 提取 HTML 注释
    html_comments = re.findall(r'<!--\s*(.*?)\s*-->', plan_content, re.DOTALL)
    if html_comments:
        feedback_parts.extend(html_comments)

    # 提取 [反馈] 或 [TODO] 标记
    feedback_markers = re.findall(r'\[(反馈|TODO|FIXME|NOTE)\]\s*(.+?)(?:\n|$)', plan_content)
    if feedback_markers:
        feedback_parts.extend([f"{marker}: {text}" for marker, text in feedback_markers])

    # 提取删除线标记（GitHub Markdown）
    strikethrough = re.findall(r'~~(.+?)~~\s*(.+?)(?:\n|$)', plan_content)
    if strikethrough:
        feedback_parts.extend([f"删除 '{old}' 改为 '{new}'" for old, new in strikethrough])

    if feedback_parts:
        return "\n".join(feedback_parts)
    else:
        return ""
```

</execution_flow>

<state_transitions>

**状态转换**：

**路径 A（自动重规划）**：
- 成功生成计划 → 自动批准 → 任务执行
- 无需执行（空tasks） → 全部完成

**路径 B（Plan 模式）**：
- 进入 Plan 模式 → 设计计划 → 格式化文档 → 请求用户批准
- 用户批准 → 任务执行
- 用户拒绝 → 提取反馈 → 重新设计（标记 replan_trigger="user"）
- 无需执行（空tasks） → 退出 Plan 模式 → 全部完成

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
