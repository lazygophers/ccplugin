<!-- STATIC_CONTENT: Phase 4流程文档，可缓存 -->

# Phase 4: Planning & Confirmation

## 概述

计划设计与确认阶段负责创建结构化的执行计划，并获得用户批准。

## 目标

- MECE任务分解
- 依赖关系建模（DAG）
- Agents/Skills分配
- Plan Mode确认（首次+用户重新设计）
- 自动批准（adjuster/verifier触发）

## 智能路径选择

根据触发来源决定是否使用 plan 模式：

| 场景 | `iteration` | `replan_trigger` | 流程 |
|------|-------------|------------------|------|
| 首次规划 | 1 | None | ✓ Plan 模式 |
| 用户主动重新设计 | >1 | "user" | ✓ Plan 模式 |
| Adjuster 自动重新规划 | >1 | "adjuster" | ✗ 直接生成并自动批准 |
| Verifier 建议优化 | >1 | "verifier" | ✗ 直接生成并自动批准 |

## 路径 A：自动重规划（跳过 Plan 模式）

```python
from pathlib import Path
import re
import json

iteration += 1  # 从 0 变为 1（首次）或递增
print(f"[MindFlow·{user_task}·计划设计/{iteration}·启动]")

replan_trigger = context.get("replan_trigger", None)

# 智能路径选择逻辑：
# - iteration=1（首次规划）：必须进入 Plan 模式
# - iteration>1 且 replan_trigger="adjuster"/"verifier"（自动优化）：跳过 Plan 模式
# - iteration>1 且 replan_trigger="user"（用户重新设计）：必须进入 Plan 模式
# - iteration>1 且 replan_trigger=None（新任务，异常状态）：必须进入 Plan 模式
if iteration > 1 and replan_trigger in ["adjuster", "verifier"]:
    print(f"[MindFlow] 自动重新规划（触发来源：{replan_trigger}），跳过 Plan 模式")

    # 直接调用 planner
    planner_result = Agent(
        subagent_type="task:planner",
        description="设计任务执行计划",
        prompt=f"""设计执行计划：

任务目标：{user_task}
迭代编号：{iteration}

要求：
1. 分析项目结构（优先中等深度）
2. 收集目标、依赖、现状、边界
3. 分解为原子子任务（MECE）
4. 建立依赖关系（DAG）
5. 分配 Agent 和 Skills（带中文注释）
6. 定义可量化验收标准
7. 返回简短报告（≤200字）

如果功能已存在，返回空 tasks 数组。
"""
    )

    # 处理 planner 的问题
    if "questions" in planner_result and planner_result["questions"]:
        for question in planner_result["questions"]:
            user_answer = AskUserQuestion(question)
            planner_result = Agent(
                subagent_type="task:planner",
                prompt=f"补充信息：{user_answer}\n继续设计计划..."
            )

    # 无需执行情况
    if not planner_result["tasks"] or len(planner_result["tasks"]) == 0:
        print(f"[MindFlow·{user_task}·计划设计/{iteration}·completed]")
        print(f"{planner_result['report']}")
        goto("全部完成")

    # 生成计划文档
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

    # 格式化文档并直接写入文件（减少 context 消耗）
    formatter_result = Agent(
        agent="task:plan-formatter",
        description="格式化计划为标准 Markdown 并写入文件",
        prompt=f"""将以下 JSON 转换为标准 Markdown 计划文档：

{json.dumps(planner_result, ensure_ascii=False, indent=2)}

YAML Frontmatter（必须放在文档开头）：
{frontmatter}

要求：
1. 严格遵循 template.md 格式
2. Mermaid 图单行文本，无 \\n
3. 包含完整的任务清单表格

文件路径：{str(plan_md_path)}
请直接写入文件并返回元数据。
"""
    )

    print(f"[MindFlow·{user_task}·计划设计/{iteration}·completed]")
    print(planner_result["report"])
    print(f"[MindFlow] 计划已生成：{formatter_result['file_path']}")
    print(f"[MindFlow] {formatter_result['summary']}")

    # 自动批准
    print(f"[MindFlow·{user_task}·计划确认/{iteration}·auto_approved]")
    print(f"[MindFlow]   原因：已在{'调整阶段' if replan_trigger == 'adjuster' else '验证阶段'}告知用户")
    context["replan_trigger"] = None
    context["plan_md_path"] = formatter_result["file_path"]

    # 【检查点保存】
    save_checkpoint(
        user_task=user_task,
        iteration=iteration,
        phase="confirmation",
        context=context,
        plan_md_path=str(plan_md_path)
    )

    goto("任务执行")
```

## 路径 B：Plan 模式（首次 / 用户重新设计）

```python
else:
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
2. 收集目标、依赖、现状、边界
3. 分解为原子子任务（MECE）
4. 建立依赖关系（DAG）
5. 分配 Agent 和 Skills（带中文注释）
6. 定义可量化验收标准
7. 返回简短报告（≤200字）

如果功能已存在，返回空 tasks 数组。
"""

    planner_result = Agent(
        subagent_type="task:planner",  # 使用 task planner agent
        description="设计任务执行计划",
        prompt=planner_prompt
    )

    # 处理 planner 的问题
    if "questions" in planner_result and planner_result["questions"]:
        for question in planner_result["questions"]:
            user_answer = AskUserQuestion(question)
            planner_result = Agent(
                subagent_type="task:planner",
                prompt=f"补充信息：{user_answer}\n继续设计计划..."
            )

    # 无需执行情况
    if not planner_result["tasks"] or len(planner_result["tasks"]) == 0:
        print(f"[MindFlow·{user_task}·计划设计/{iteration}·completed]")
        print(f"{planner_result['report']}")
        # 退出 plan 模式
        ExitPlanMode()
        goto("全部完成")

    # Phase 3: 格式化计划文档
    print(f"[MindFlow] 正在格式化计划文档...")

    # 从系统消息或环境变量获取计划文件路径
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

    # Phase 4: 格式化文档并直接写入文件（减少 context 消耗）
    formatter_result = Agent(
        agent="task:plan-formatter",
        description="格式化计划为标准 Markdown 并写入文件",
        prompt=f"""将以下 JSON 转换为标准 Markdown 计划文档：

{json.dumps(planner_result, ensure_ascii=False, indent=2)}

YAML Frontmatter（必须放在文档开头）：
{frontmatter}

要求：
1. 严格遵循 template.md 格式
2. Mermaid 图单行文本，无 \\n
3. 包含完整的任务清单表格

文件路径：{plan_file_path}
请直接写入文件并返回元数据。
"""
    )

    print(f"[MindFlow·{user_task}·计划设计/{iteration}·completed]")
    print(planner_result["report"])
    print(f"[MindFlow] 计划已生成：{formatter_result['file_path']}")
    print(f"[MindFlow] {formatter_result['summary']}")

    # Phase 5: 退出 plan 模式并请求用户批准
    print(f"[MindFlow·{user_task}·计划确认/{iteration}·等待确认]")

    exit_result = ExitPlanMode()

    # 处理用户决策
    if exit_result.get("approved", False):
        # 用户批准
        print(f"[MindFlow] ✓ 用户批准计划，准备执行")
        context["replan_trigger"] = None
        context["plan_md_path"] = formatter_result["file_path"]

        # 保存检查点
        save_checkpoint(
            user_task=user_task,
            iteration=iteration,
            phase="confirmation",
            context=context,
            plan_md_path=plan_file_path
        )

        goto("任务执行")
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

        goto("计划设计")


def extract_user_feedback(plan_content: str) -> str:
    """从计划文件中提取用户标注的反馈"""
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

    # 提取删除线标记
    strikethrough = re.findall(r'~~(.+?)~~\s*(.+?)(?:\n|$)', plan_content)
    if strikethrough:
        feedback_parts.extend([f"删除 '{old}' 改为 '{new}'" for old, new in strikethrough])

    if feedback_parts:
        return "\n".join(feedback_parts)
    else:
        return ""
```

## 输出

- 结构化计划文档（JSON + Markdown）
- 执行流程图（Mermaid）
- 验收标准清单

## 状态转换

- **路径 A（自动重规划）**：生成计划 → 自动批准 → 任务执行（Phase 5）
- **路径 B（Plan 模式）**：EnterPlanMode → 设计 → 格式化 → ExitPlanMode
  - 用户批准 → 任务执行（Phase 5）
  - 用户拒绝 → 提取反馈 → 重新设计（Phase 4）
- **无需执行**：退出 Plan 模式 → 全部完成（Phase 8）

<!-- /STATIC_CONTENT -->
