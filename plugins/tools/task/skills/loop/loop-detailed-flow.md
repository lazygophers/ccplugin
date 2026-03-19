# Loop 详细执行流程

<overview>
本文档包含 MindFlow Loop 所有7个阶段的详细执行流程，覆盖完整的 PDCA 循环。
</overview>

<phase_initialization>

## 初始化（Initialization）

```python
status = "进行中"
iteration = 0
stalled_count = 0
guidance_count = 0
max_stalled_attempts = 3
user_task = "$ARGUMENTS"

available_skills = ListSkills()
available_agents = ListAgents()

print(f"[MindFlow·{user_task}·初始化/0·进行中]")
print(f"初始化完成。可用 Skills：{len(available_skills)} 个，可用 Agents：{len(available_agents)} 个")
```

状态转换：成功 → 计划设计

</phase_initialization>

<phase_planning>

## 计划设计（Planning / Plan）

```python
iteration += 1

planner_result = Agent(
    agent="task:planner",
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
    goto("全部完成")
```

```python
# 生成计划文档
from pathlib import Path
import re

plans_dir = Path(".claude/plans")
plans_dir.mkdir(parents=True, exist_ok=True)

safe_task_name = re.sub(r'[^\w\u4e00-\u9fff]+', '-', user_task)[:50]
plan_md_path = plans_dir / f"{safe_task_name}-{iteration}.md"

Write(str(plan_md_path), filled_markdown_content)

print(f"[MindFlow·{user_task}·计划设计/{iteration}·completed]")
print(planner_result["report"])
print(f"计划已生成：{plan_md_path}")
```

状态转换：有任务 → 计划确认；无任务 → 全部完成

</phase_planning>

<phase_confirmation>

## 计划确认（Plan Confirmation）

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
```

状态转换：立即执行 → 任务执行；重新设计 → 计划设计

</phase_confirmation>

<phase_execution>

## 任务执行（Execution / Do）

```python
team_name = f"mindflow-execution-{iteration}"

print(f"[MindFlow·{user_task}·任务执行/{iteration}·进行中]")

execution_result = TeamCreate(
    team_name=team_name,
    description=planner_result["report"],
    skills=[Skill("task:execute")]
)

TeamDelete(team_name=team_name)
print(f"[MindFlow·{user_task}·任务执行/{iteration}·completed]")
```

状态转换：成功 → 结果验证

</phase_execution>

<phase_verification>

## 结果验证（Verification / Check）

```python
verification_result = Agent(
    agent="task:verifier",
    prompt=f"""执行结果验证：

任务目标：{user_task}
迭代编号：{iteration}

要求：
1. 获取所有任务的状态和验收标准
2. 系统性验证每个任务
3. 检查回归测试
4. 生成验收报告（≤100字）
5. 决定验收状态
"""
)

print(f"[MindFlow·{user_task}·结果验证/{iteration}·{verification_result['status']}]")
print(f"验收报告：{verification_result['report']}")
```

```python
# 状态转换
status = verification_result["status"]

if status == "passed":
    goto("全部完成")

elif status == "suggestions":
    user_response = AskUserQuestion(
        f"{verification_result['report']}\n\n建议：\n" +
        "\n".join(f"- {s['suggestion']}" for s in verification_result['suggestions']) +
        "\n\n这些优化是否属于当前任务范围？(是/否)"
    )

    if user_response.strip().lower() in ["是", "yes", "y"]:
        goto("计划设计")
    else:
        goto("全部完成")

elif status == "failed":
    goto("失败调整")
```

</phase_verification>

<phase_adjustment>

## 失败调整（Adjustment / Act）

```python
adjustment_result = Agent(
    agent="task:adjuster",
    prompt=f"""执行失败调整：

任务目标：{user_task}
迭代编号：{iteration}

要求：
1. 获取所有失败任务的详细信息
2. 分析失败原因
3. 检测停滞模式
4. 应用分级升级策略
5. 生成调整报告（≤100字）
"""
)

print(f"[MindFlow·{user_task}·失败调整/{iteration}·{adjustment_result['strategy']}]")
print(f"调整报告：{adjustment_result['report']}")

# 指数退避
if "retry_config" in adjustment_result:
    backoff_seconds = adjustment_result["retry_config"]["backoff_seconds"]
    if backoff_seconds > 0:
        print(f"应用指数退避：等待 {backoff_seconds} 秒...")
        time.sleep(backoff_seconds)
```

```python
# 状态转换
strategy = adjustment_result["strategy"]

if strategy == "retry":
    apply_adjustments(adjustment_result["adjustments"])
    goto("任务执行")

elif strategy == "debug":
    debug_result = Agent(
        agent="debug",
        prompt=f"深度分析失败原因：{adjustment_result['debug_plan']}"
    )
    apply_debug_fixes(debug_result)
    goto("任务执行")

elif strategy == "replan":
    goto("计划设计")

elif strategy == "ask_user":
    stalled_count += 1
    guidance_count += 1

    user_guidance = AskUserQuestion(adjustment_result["question"])
    apply_user_guidance(user_guidance)

    if stalled_count >= max_stalled_attempts:
        print(f"[MindFlow·{user_task}·失败调整/{iteration}·stopped]")
        print(f"检测到持续停滞（{stalled_count} 次），建议人工介入")
        goto("全部完成")
    else:
        goto("任务执行")
```

</phase_adjustment>

<phase_completion>

## 全部完成（Completion / Finalization）

```python
status = "completed"

finalizer_result = Agent(
    agent="task:finalizer",
    prompt="""执行 loop 完成后的收尾清理工作：

要求：
1. 停止所有运行中的任务
2. 删除所有计划文件
3. 清理临时文件和缓存
4. 生成清理报告
"""
)

print(f"[MindFlow·{user_task}·completed]")

# 总结报告
changed_files = get_changed_files()

print("\n## 任务总结")
print(f"状态：成功（所有验收标准通过）")
print(f"总迭代次数：{iteration}")
print(f"停滞次数：{stalled_count}")
print(f"用户指导次数：{guidance_count}")

print("\n## 变更文件")
for file in changed_files:
    print(f"  - {file}")

print("\n任务完成")
```

状态转换：完成 → 结束

</phase_completion>
