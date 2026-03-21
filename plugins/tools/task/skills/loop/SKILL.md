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

## 执行要求

**重要**：严格按照以下流程执行，不可跳过任何阶段。

### 阶段1：初始化
```python
iteration = 0
context = {"replan_trigger": None}
```

### 阶段2：计划设计 + 计划确认

**调用 flows/plan skill（包含完整的计划生成和确认流程）：**

```python
# 调用 flows/plan - 它会自动执行以下步骤：
# 1. 调用 task:planner 生成计划
# 2. 生成计划文档
# 3. 执行计划确认（首次必须用户确认）
# 4. 返回用户决策

Skill(
    skill="task:loop:flows/plan",  # 调用计划流程 skill
    args=f"""
    用户任务：{user_task}
    迭代编号：{iteration}
    重新规划触发来源：{context.get('replan_trigger', None)}
    """
)
```

**flows/plan 会输出以下日志**：
1. `[MindFlow·xxx·计划设计/{iteration}·completed]`
2. `[MindFlow·xxx·计划确认/{iteration}·准备预览]`
3. 如果是自动重新规划：`[MindFlow·xxx·计划确认/{iteration}·auto_approved]`
4. 如果需要用户确认：`[MindFlow·xxx·计划确认/{iteration}·等待确认]`

**检查点**：在进入任务执行前，必须看到以下日志之一：
- `[MindFlow·xxx·计划确认/N·等待确认]` + 用户做出选择
- `[MindFlow·xxx·计划确认/N·auto_approved]` (仅 iteration > 1)

**如果看不到这些日志，说明 flows/plan 没有被调用，必须修正！**

### 阶段3：任务执行
```python
task:execute 执行所有任务
```

### 阶段4：结果验证
```python
verification_result = Agent(agent="task:verifier", ...)

if status == "passed":
    goto("完成")
elif status == "suggestions":
    context["replan_trigger"] = "verifier"
    goto("阶段2")  # 自动继续优化
elif status == "failed":
    goto("阶段5")  # 失败调整
```

### 阶段5：失败调整
```python
adjustment_result = Agent(agent="task:adjuster", ...)

if strategy == "retry" or strategy == "debug":
    goto("阶段3")
elif strategy == "replan":
    context["replan_trigger"] = "adjuster"
    goto("阶段2")
```

开始执行 PDCA 循环。

<!-- /DYNAMIC_CONTENT -->
