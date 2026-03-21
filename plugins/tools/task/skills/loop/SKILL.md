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
4. 计划设计
5. **计划确认**（必须执行，首次必须用户确认）
6. 任务执行
7. 结果验证
8. 失败调整（如需）
9. 完成

**关键要求**：
- **所有输出必须以 [MindFlow] 开头**（强制规则，无例外）
- 计划确认阶段**必须执行**，不可跳过
- 首次规划（iteration=1）**必须**通过 AskUserQuestion 获取用户确认
- 自动重新规划（adjuster/verifier触发）可跳过确认，但必须输出日志说明
- 每次都要输出状态追踪日志：`[MindFlow·${任务}·${步骤}/${迭代}·${状态}]`

</execution>

<references>

## 子技能与文档

**子技能**：flows/plan（计划流程，含必须的计划确认）、flows/verify（验证流程）、task:planner、task:execute、task:verifier、task:adjuster

**详细文档**：
- [detailed-flow.md](detailed-flow.md) - 完整流程说明（含计划确认要求）
- [deep-iteration实现](../deep-iteration/implementation.md) - 深度迭代机制
- [prompt-caching.md](prompt-caching.md) - 缓存优化

</references>

<quick_reference>

质量阈值：60→75→85→90分 | 失败策略：retry→debug→replan→ask_user | 深度研究：第1轮/失败2次/质量不达标/复杂任务 | 缓存优化：静态内容标记，90%成本节省

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
```python
# 输出初始化信息（必须以 [MindFlow] 开头）
print("[MindFlow] 开始初始化任务...")

iteration = 0
context = {"replan_trigger": None}

print(f"[MindFlow·{user_task}·初始化/0·进行中]")
print("[MindFlow] 初始化完成")
```

### 阶段2：计划设计 + 计划确认

**所有输出必须以 [MindFlow] 开头。**

```python
print("[MindFlow] 开始计划设计...")

iteration += 1

# 调用 task:planner 生成计划
print(f"[MindFlow] 正在调用 planner 生成执行计划...")
planner_result = Agent(agent="task:planner", ...)

# 生成计划文档
print(f"[MindFlow] 正在生成计划文档...")
# ... 生成文档代码 ...

print(f"[MindFlow·{user_task}·计划设计/{iteration}·completed]")
print(f"[MindFlow] 计划已生成：{plan_md_path}")

# 计划确认（必须执行）
print(f"[MindFlow·{user_task}·计划确认/{iteration}·准备预览]")
print(f"[MindFlow] 计划文件：{plan_md_path}")

replan_trigger = context.get("replan_trigger", None)

if iteration > 1 and replan_trigger in ["adjuster", "verifier"]:
    print(f"[MindFlow] ✓ 自动重新规划（触发来源：{replan_trigger}），跳过用户确认")
    print(f"[MindFlow]   原因：已在{'调整阶段' if replan_trigger == 'adjuster' else '验证阶段'}告知用户")
    print(f"[MindFlow·{user_task}·计划确认/{iteration}·auto_approved]")
    context["replan_trigger"] = None
else:
    # 打开浏览器预览
    print(f"[MindFlow] 正在打开浏览器预览计划...")
    Bash("md2html ...")
    print(f"[MindFlow] 已在浏览器打开计划预览")

    # 必须询问用户
    print(f"[MindFlow·{user_task}·计划确认/{iteration}·等待确认]")
    user_decision = AskUserQuestion(
        question="执行计划已准备就绪，是否开始执行？",
        options=["立即执行", "重新设计"]
    )

    if user_decision == "重新设计":
        print(f"[MindFlow] 用户选择重新设计计划")
        context["replan_trigger"] = "user"
        # 回到计划设计
    else:
        print(f"[MindFlow] 用户批准计划，准备执行")
        context["replan_trigger"] = None
        # 继续下一阶段
```

**检查点**：在进入任务执行前，必须看到以下日志之一：
- `[MindFlow·xxx·计划确认/N·等待确认]` + 用户做出选择
- `[MindFlow·xxx·计划确认/N·auto_approved]` (仅 iteration > 1)

**如果看不到这些日志，说明计划确认环节被跳过，必须修正！**

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

**重要提醒**：执行过程中的每一条输出都必须以 `[MindFlow]` 开头，包括：
- 普通日志：`[MindFlow] xxx`
- 状态追踪：`[MindFlow·任务名·阶段/迭代·状态]`
- 错误信息：`[MindFlow] ⚠️ xxx`
- 成功提示：`[MindFlow] ✓ xxx`

开始执行 PDCA 循环。

<!-- /DYNAMIC_CONTENT -->
