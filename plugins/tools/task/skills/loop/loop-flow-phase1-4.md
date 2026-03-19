# Loop 详细执行流程 - 阶段 1-4

<overview>

本文档包含 MindFlow Loop 前四个阶段的详细执行流程和代码示例。这些阶段覆盖了从环境初始化到任务开始执行的完整路径：初始化准备运行环境，计划设计将目标分解为可执行的子任务，计划确认让用户审核并决策，任务执行按计划并行调度。

</overview>

<phase_initialization>

## 初始化（Initialization）

初始化执行环境，准备必要的资源和状态变量。这个阶段设定了整个循环的基础参数，包括迭代计数器、停滞检测器和可用资源清单。

```python
# 初始化状态变量
status = "进行中"
iteration = 0  # 迭代次数
stalled_count = 0  # 停滞次数
guidance_count = 0  # 用户指导次数
max_stalled_attempts = 3  # 最大停滞次数
user_task = "$ARGUMENTS"  # 用户任务目标

# 列出可用资源
available_skills = ListSkills()
available_agents = ListAgents()

print(f"[MindFlow·{user_task}·初始化/0·进行中]")
print(f"初始化完成。可用 Skills：{len(available_skills)} 个，可用 Agents：{len(available_agents)} 个")
```

状态转换：成功 → 进入计划设计

</phase_initialization>

<phase_planning>

## 计划设计（Planning / Plan）

调用 planner agent 设计执行计划。planner 接收任务目标后，分析项目结构，将任务分解为原子子任务（MECE 原则），建立 DAG 依赖关系，为每个子任务分配 agent 和 skills，定义可量化验收标准。如果 planner 有疑问会通过问题列表返回，MindFlow 向用户收集答案后重新生成计划。

```python
iteration += 1  # 增加迭代计数

# 调用 planner agent
planner_result = Agent(
    agent="task:planner",
    prompt=f"""设计执行计划：

任务目标：{user_task}
当前迭代：第 {iteration} 轮

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
            agent="task:planner",
            prompt=f"补充信息：{user_answer}\n继续设计计划..."
        )

# 特殊情况：无需执行（功能已存在）
if not planner_result["tasks"] or len(planner_result["tasks"]) == 0:
    print(f"[MindFlow·{user_task}·计划设计/{iteration}·completed]")
    print(f"{planner_result['report']}")
    goto("全部完成")
```

### 生成计划确认文档

计划文件固定存放在 `.claude/plans` 目录，文件名格式为 `<任务名>-<迭代数>.md`。基于 plan-confirmation-template.md 模板格式直接生成 Markdown 文档，包含任务编排图（Mermaid stateDiagram）、任务清单表格、迭代验收标准和任务说明。

```python
from pathlib import Path

plans_dir = Path(".claude/plans")
plans_dir.mkdir(parents=True, exist_ok=True)

import re
safe_task_name = re.sub(r'[^\w\u4e00-\u9fff]+', '-', user_task)[:50]
plan_md_path = plans_dir / f"{safe_task_name}-{iteration}.md"

# 基于模板格式生成 Markdown
Write(str(plan_md_path), filled_markdown_content)

print(f"[MindFlow·{user_task}·计划设计/{iteration}·completed]")
print(planner_result["report"])
print(f"计划已生成：{plan_md_path}")
```

状态转换：成功（有任务需执行）→ 进入计划确认；无需执行（tasks 为空）→ 进入全部完成

</phase_planning>

<phase_confirmation>

## 计划确认（Plan Confirmation）

向用户展示执行计划，等待确认后再开始执行。这个阶段的存在是为了让用户在任务实际执行前有机会审核和调整计划，避免执行方向偏差导致的返工。

```python
# 将计划 MD 转换为 HTML 并在浏览器打开预览
print(f"[MindFlow·{user_task}·计划确认/{iteration}·准备预览]")
print(f"计划文件：{plan_md_path}")

Bash(
    command=f"uvx --from git+https://github.com/lazygophers/ccplugin.git@master md2html {plan_md_path}",
    description="将计划 MD 转换为 HTML 并在浏览器打开"
)
print("已在浏览器打开计划预览")

# 等待用户确认
print(f"[MindFlow·{user_task}·计划确认/{iteration}·等待确认]")

user_decision = AskUserQuestion(
    question="执行计划已准备就绪，是否开始执行？",
    options=["立即执行", "重新设计"]
)
```

状态转换：立即执行 → 进入任务执行；重新设计 → 返回计划设计

确认模板参见 [plan-confirmation-template.md](${CLAUDE_PLUGIN_ROOT}/skills/loop/plan-confirmation-template.md)

</phase_confirmation>

<phase_execution>

## 任务执行（Execution / Do）

创建 Team 并行执行任务，遵循依赖关系和并行规则。execute skill 内部管理完整的执行生命周期：按依赖顺序调度任务，最多 2 个并行，实时监控进度，更新任务状态。执行完成后立即删除团队释放资源。

```python
team_name = f"mindflow-execution-{iteration}"

print(f"[MindFlow·{user_task}·任务执行/{iteration}·进行中]")
print(f"创建执行团队：{team_name}")

execution_result = TeamCreate(
    team_name=team_name,
    description=planner_result["report"],
    skills=[Skill("task:execute")]
)

# execute skill 内部会：
# 1. 按依赖顺序调度任务
# 2. 并行执行（最多 2 个）
# 3. 实时监控进度
# 4. 更新任务状态

TeamDelete(team_name=team_name)
print(f"[MindFlow·{user_task}·任务执行/{iteration}·completed]")
print(f"执行完成，团队已清理")
```

并行执行遵循四条规则：最多 2 个任务同时执行，严格按依赖顺序调度，槽位释放时自动启动下一个 Ready 任务，实时更新任务状态。

状态转换：成功 → 进入结果验证

</phase_execution>
