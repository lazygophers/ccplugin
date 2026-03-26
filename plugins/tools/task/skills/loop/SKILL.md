---
description: Loop 持续执行 - 作为 team leader 执行完整的任务管理循环，包括计划设计、执行、验证、调整
argument-hint: [ 任务目标描述 ]
skills:
  - task:prompt-optimizer
  - task:planner
  - task:execute
  - task:verifier
  - task:adjuster
  - deepresearch:deep-research
model: sonnet
memory: project
---

<!-- STATIC_CONTENT: Cacheable (4800+ tokens) -->

# MindFlow - 迭代式任务编排引擎

<overview>

基于 PDCA 循环的智能任务编排引擎，通过持续迭代完成复杂任务。

**核心特性**：深度迭代（质量递进60→90分）、9状态生命周期、Team Leader（统一用户交互、调度4个agent）

**用户交互点**：仅在计划确认阶段需要用户审核（智能跳过：首次+用户主动重新设计需要确认，自动重新规划跳过确认）

</overview>

<execution>

## PDCA 流程

**Prepare**（flows/prompt-optimization）→ **Plan**（flows/plan，必须包含计划确认）→ **Do**（task:execute）→ **Check**（flows/verify）→ **Act**（task:adjuster）

**8个阶段**：
1. 初始化
2. 提示词优化（可选）
3. 深度研究（可选）
4. 计划设计与确认（Plan Mode）
5. 任务执行
6. 结果验证
7. 失败调整（如需）
8. 完成

**关键要求**：
- **所有输出必须以 [MindFlow] 开头**（强制规则，无例外）
- **每次调用必须重置状态**（iteration=0, context={}），避免同一会话中不同任务的状态混淆
- 计划确认阶段**必须执行**，不可跳过
- 首次规划（iteration=1）和用户重新设计**使用 Plan Mode**（EnterPlanMode/ExitPlanMode）
- 自动重新规划（adjuster/verifier触发）**跳过 Plan Mode**，直接生成并自动批准
- 每次都要输出状态追踪日志：`[MindFlow·${任务}·${步骤}/${迭代}·${状态}]`

</execution>

<references>

## 子技能与文档

**子技能**：flows/plan（计划流程，含必须的计划确认）、flows/verify（验证流程）、task:planner、task:execute、task:verifier、task:adjuster

**详细文档**：
- [detailed-flow.md](detailed-flow.md) - 8阶段流程导航索引（含各phase详细说明）
  - [Phase 1: Initialization](phases/phase-1-initialization.md) - 初始化和记忆加载
  - [Phase 2: Prompt Optimization](phases/phase-2-prompt-optimization.md) - 提示词优化（仅首次）
  - [Phase 3: Deep Research](phases/phase-3-deep-research.md) - 深度研究（可选）
  - [Phase 4: Planning](phases/phase-4-planning.md) - 计划设计与确认
  - [Phase 5: Execution](phases/phase-5-execution.md) - 智能并行执行
  - [Phase 6: Verification](phases/phase-6-verification.md) - 结果验证
  - [Phase 7: Adjustment](phases/phase-7-adjustment.md) - 失败调整
  - [Phase 8: Finalization](phases/phase-8-finalization.md) - 完成清理
- [deep-iteration实现](../deep-iteration/implementation.md) - 深度迭代机制
- [prompt-caching.md](prompt-caching.md) - 缓存优化
- [deep-research-triggers.md](deep-research-triggers.md) - 深度研究触发决策

</references>

<quick_reference>

质量阈值：60→75→85→90分 | 失败策略：retry→debug→replan→ask_user | 深度研究：复杂度>8自动触发/失败2次询问用户/用户可拒绝（详见 deep-research-triggers.md） | 缓存优化：静态内容标记，90%成本节省

</quick_reference>

<!-- /STATIC_CONTENT -->

<!-- DYNAMIC_CONTENT -->

用户任务：`$ARGUMENTS`

## 输出格式要求

**强制规则**：从现在开始，你的所有回复内容必须以 `[MindFlow]` 开头。

正确示例：
```
[MindFlow] 开始执行任务...
[MindFlow] 正在生成执行计划...
[MindFlow·任务名·计划设计/1·completed]
```

错误示例（禁止）：
```
开始执行任务...  ← 缺少 [MindFlow] 前缀
正在生成计划...  ← 缺少 [MindFlow] 前缀
```

## 执行要求

**重要**：严格按照以下流程执行，不可跳过任何阶段。

### 阶段1：初始化

**状态隔离要求**：每次调用 loop 时，必须重置所有状态变量，避免不同任务之间的状态混淆。

```python
# 输出初始化信息（必须以 [MindFlow] 开头）
print("[MindFlow] 开始初始化任务...")

# 强制重置状态（即使在同一会话中）
iteration = 0
context = {
    "replan_trigger": None,
    "start_time": datetime.now(),
    "task_id": hashlib.md5(user_task.encode()).hexdigest()[:8]
}

# 检查是否为新任务（避免状态混淆）
if "previous_task_id" in globals() and previous_task_id == context["task_id"]:
    print("[MindFlow] ⚠️ 检测到相同任务，这可能是错误调用")
    # 询问用户是否继续
    response = AskUserQuestion("检测到相同的任务目标，是否要重新开始？")
    if response != "是":
        print("[MindFlow] 用户取消执行")
        exit()

previous_task_id = context["task_id"]

print(f"[MindFlow·{user_task}·初始化/0·进行中]")
print(f"[MindFlow] 任务ID: {context['task_id']}")
print("[MindFlow] 初始化完成")
```

### 阶段2：计划设计与确认（Plan Mode）

**使用 Plan Mode 统一设计和确认流程**：

**智能路径选择**：
- **首次规划 / 用户重新设计**：使用 EnterPlanMode/ExitPlanMode
  - 进入 plan 模式
  - 探索代码（可选深度研究）
  - 设计计划（调用 task:planner）
  - 格式化文档（调用 task:plan-formatter）
  - 写入计划文件
  - 请求用户批准
  - 用户可在文件中标注反馈

- **自动重规划（adjuster/verifier）**：跳过 plan 模式
  - 直接调用 planner 生成计划
  - 格式化并写入文档
  - 自动批准并继续执行
  - 避免重复确认

**所有输出必须以 [MindFlow] 开头。**

```python
print("[MindFlow] 开始计划设计...")

iteration += 1  # 从 0 变为 1（首次）或递增
replan_trigger = context.get("replan_trigger", None)

# 智能路径选择逻辑：
# - 自动优化（verifier/adjuster 触发 + iteration > 1）：跳过 Plan 模式
# - 其他所有情况（首次/用户重新设计/新任务）：必须进入 Plan 模式
if iteration > 1 and replan_trigger in ["adjuster", "verifier"]:
    # 路径 A：自动重规划（跳过 Plan 模式）
    print(f"[MindFlow] 自动重新规划（触发来源：{replan_trigger}），跳过 Plan 模式")

    # 直接生成计划
    planner_result = Agent(agent="task:planner", ...)

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

文件路径：{plan_md_path}
请直接写入文件并返回元数据。
"""
    )

    print(f"[MindFlow·{user_task}·计划设计/{iteration}·completed]")
    print(f"[MindFlow] 计划已生成：{formatter_result['file_path']}")
    print(f"[MindFlow] {formatter_result['summary']}")
    print(f"[MindFlow·{user_task}·计划确认/{iteration}·auto_approved]")
    context["replan_trigger"] = None
    context["plan_md_path"] = formatter_result["file_path"]
else:
    # Plan 模式：首次或用户重新设计
    print(f"[MindFlow] 进入 Plan 模式进行计划设计...")

    EnterPlanMode()

    # 设计计划
    planner_result = Agent(subagent_type="Plan", agent="task:planner", ...)

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

文件路径：{plan_file_path}
请直接写入文件并返回元数据。
"""
    )

    print(f"[MindFlow·{user_task}·计划设计/{iteration}·completed]")
    print(f"[MindFlow] 计划已生成：{formatter_result['file_path']}")
    print(f"[MindFlow] {formatter_result['summary']}")
    print(f"[MindFlow·{user_task}·计划确认/{iteration}·等待确认]")

    # 请求用户批准
    exit_result = ExitPlanMode()

    if exit_result.get("approved"):
        print(f"[MindFlow] ✓ 用户批准计划，准备执行")
        context["replan_trigger"] = None
        context["plan_md_path"] = formatter_result["file_path"]
        # 继续下一阶段
    else:
        print(f"[MindFlow] 用户选择重新设计计划")
        # 提取用户反馈
        user_feedback = extract_user_feedback(Read(plan_file_path))
        if user_feedback:
            context["user_feedback"] = user_feedback
        context["replan_trigger"] = "user"
        # 回到计划设计
```

**检查点**：在进入任务执行前，必须看到以下日志之一：
- `[MindFlow·xxx·计划确认/N·等待确认]` + ExitPlanMode 批准
- `[MindFlow·xxx·计划确认/N·auto_approved]` (自动重规划)

**详细实现**：参见 [flows/plan.md](flows/plan.md)

### 阶段3：任务执行

**所有输出必须以 [MindFlow] 开头。**

```python
print(f"[MindFlow·{user_task}·任务执行/{iteration}·进行中]")
print(f"[MindFlow] 开始执行所有任务...")

# 调用 task:execute
result = Agent(agent="task:execute", ...)

print(f"[MindFlow·{user_task}·任务执行/{iteration}·completed]")
print(f"[MindFlow] 任务执行完成")
```

### 阶段4：结果验证

**所有输出必须以 [MindFlow] 开头。**

```python
print(f"[MindFlow] 开始验证执行结果...")

verification_result = Agent(agent="task:verifier", ...)

status = verification_result["status"]
print(f"[MindFlow·{user_task}·结果验证/{iteration}·{status}]")
print(f"[MindFlow] 验收报告：{verification_result['report']}")

if status == "passed":
    print(f"[MindFlow] 所有验收标准通过，任务完成")
    goto("完成")
elif status == "suggestions":
    print(f"[MindFlow] 检测到优化建议，自动继续下一轮迭代...")
    for s in verification_result['suggestions']:
        print(f"[MindFlow]   - {s['suggestion']}")
    context["replan_trigger"] = "verifier"
    goto("阶段2")  # 自动继续优化
elif status == "failed":
    print(f"[MindFlow] 验收失败，进入失败调整阶段")
    goto("阶段5")  # 失败调整
```

### 阶段5：失败调整

**所有输出必须以 [MindFlow] 开头。**

```python
print(f"[MindFlow] 开始分析失败原因...")

adjustment_result = Agent(agent="task:adjuster", ...)

strategy = adjustment_result["strategy"]
print(f"[MindFlow·{user_task}·失败调整/{iteration}·{strategy}]")
print(f"[MindFlow] 调整报告：{adjustment_result['report']}")

if strategy == "retry":
    print(f"[MindFlow] 应用修正后重新执行任务")
    goto("阶段3")
elif strategy == "debug":
    print(f"[MindFlow] 执行深度诊断后重新执行")
    goto("阶段3")
elif strategy == "replan":
    print(f"[MindFlow] 重新设计执行计划")
    context["replan_trigger"] = "adjuster"
    goto("阶段2")
elif strategy == "ask_user":
    print(f"[MindFlow] 需要用户指导")
    # 询问用户...
```

### 阶段6：完成清理

**所有输出必须以 [MindFlow] 开头。**

```python
print(f"[MindFlow·{user_task}·完成清理/final·进行中]")

# 从 context 获取 plan_md_path
plan_md_path = context.get("plan_md_path", "")

if plan_md_path:
    print(f"[MindFlow] 正在清理资源...")

    # 调用 finalizer 清理计划文件和临时资源
    finalizer_result = Agent(
        agent="task:finalizer",
        description="清理 loop 资源",
        prompt=f"""执行 loop 完成后的收尾清理：
计划文件：{plan_md_path}
要求：
1. 停止所有运行中的任务
2. 删除计划文件（含 .html 文件）
3. 清理临时文件
4. 生成清理报告
"""
    )

    print(f"[MindFlow] 清理完成：{finalizer_result.get('report', '无报告')}")
else:
    print(f"[MindFlow] ⚠️ 未找到计划文件路径，跳过清理")

# 清理检查点
print(f"[MindFlow] 清理检查点...")
cleanup_checkpoint(user_task)

# 保存任务执行记忆
print(f"[MindFlow] 保存任务执行记忆...")
end_time = datetime.now()
duration_minutes = int((end_time - context.get("start_time", end_time)).total_seconds() / 60)

save_episode_memory(
    task_type="loop",
    user_task=user_task,
    iteration=iteration,
    success=True,
    duration_minutes=duration_minutes,
    planner_result=context.get("planner_result", {}),
    execution_summary=context.get("execution_summary", ""),
    quality_score=context.get("quality_score", 0)
)

# 生成最终报告
print(f"[MindFlow·{user_task}·完成清理/final·completed]")
print(f"[MindFlow] ✓ 任务完成！共 {iteration} 次迭代，耗时 {duration_minutes} 分钟")

# 清理本次任务的状态变量（保留 previous_task_id 用于下次检测）
del iteration
del context
print(f"[MindFlow] 状态已清理，准备接受新任务")
```

**重要提醒**：执行过程中的每一条输出都必须以 `[MindFlow]` 开头，包括：
- 普通日志：`[MindFlow] xxx`
- 状态追踪：`[MindFlow·任务名·阶段/迭代·状态]`
- 错误信息：`[MindFlow] ⚠️ xxx`
- 成功提示：`[MindFlow] ✓ xxx`

开始执行 PDCA 循环。

<!-- /DYNAMIC_CONTENT -->
