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

plans_dir = Path(".claude/plans")
plans_dir.mkdir(parents=True, exist_ok=True)

# 强制保留用户语言字符（中文：\u4e00-\u9fff）
safe_task_name = re.sub(r'[^\w\u4e00-\u9fff]+', '-', user_task)[:50]
plan_md_path = plans_dir / f"{safe_task_name}-{iteration}.md"

# YAML frontmatter + 必须使用 plan-confirmation-template.md 模板
frontmatter = f"""---
status: pending
created_at: {datetime.now().isoformat()}
iteration: {iteration}
task_count: {len(planner_result['tasks'])}
completed_count: 0
---
"""

# 基于 plan-confirmation-template.md 填充内容
filled_content = fill_plan_template(planner_result, frontmatter)
Write(str(plan_md_path), filled_content)

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
- [loop-deep-iteration.md](../loop/loop-deep-iteration.md#计划设计阶段融合研究结果)
- [plan-confirmation-template.md](../loop/plan-confirmation-template.md)
- Skills(task:planner)

</references>
