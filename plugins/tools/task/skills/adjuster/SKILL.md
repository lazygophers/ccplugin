---
agent: task:adjuster
description: 失败调整规范 - 分析失败原因、检测停滞、应用升级策略的执行规范
model: sonnet
context: fork
user-invocable: false
---

# Skills(task:adjuster) - 失败调整规范

<overview>

Adjuster 技能在任务执行失败时介入，负责分析失败原因、检测停滞模式并应用分级升级策略。它的核心设计借鉴了弹性工程中的 Circuit Breaker 模式——当简单重试无法解决问题时，自动升级到更深层次的诊断和修复，避免无限重试造成的资源浪费。

六级升级策略按失败次数递进：Level 1 Retry with adjustment（1次相同错误）、Level 1.5 Self-Healing（匹配 17 类错误）、Level 2 Debug（深度诊断）、Level 2.5 Micro-Replan（仅重规划失败任务+直接依赖，保留成功任务）、Level 3 Full Replan（重建整个计划）、Level 4 Ask User（请求人工指导）。指数退避公式 `2^(failure_count - 1)` 秒确保重试间隔逐步增大。支持振荡检测（A->B->A->B 立即 ask_user）和紧急逃逸（总失败>=15 立即 ask_user）。

</overview>

<red_flags>

| AI Rationalization | Reality Check |
|-------------------|---------------|
| "失败一次立即升级到 replan 更快" | 升级策略是分级的：retry→debug→replan，跳级意味着浪费之前的信息，必须按顺序 |
| "指数退避太慢，删掉等待时间继续重试" | 指数退避是 Circuit Breaker 的关键，删掉等于无限快速重试，会消耗资源 |
| "停滞检测用失败次数就行，不用检查错误类型" | 不同错误的停滞表现不同，相同错误重复3次 ≠ 不同错误各1-2次 |
| "ask_user 策略可以自动重试，不用等用户" | ask_user 强制阻塞，等用户指导是规则，自动重试违反了升级策略 |
| "调整报告写'失败了'就可以，不用分析原因" | 报告必须包含：失败原因、应用策略、具体调整方案，否则无法追踪问题 |
| "第2次失败后的 debug 可以跳过，直接用之前的诊断结果" | 第2次可能是不同原因，必须新建 debug agent 重新诊断，不能复用旧结果 |
| "失败了3次就应该自动给出修复代码，用户不用参与" | ask_user 是让用户指导，不是等待自动修复，规则是停滞后必须人工确认 |
| "记录失败历史太复杂，简化成总失败次数就行" | 失败历史需要：时间戳、错误类型、应用策略、调整内容，总次数太粗糙 |

</red_flags>

<execution_flow>

## 执行流程

### 调用 adjuster agent

```python
adjustment_result = Agent(
    agent="task:adjuster",
    prompt="""执行失败调整：

要求：
1. 获取所有失败任务的详细信息
2. 分析失败原因（编译/测试/依赖/运行时/环境）
3. 检测停滞模式（相同错误重复 3 次）
4. 应用分级升级策略
5. 生成调整报告（≤100字）

升级策略：
- Level 1：Retry with adjustment（1次相同错误，0秒）
- Level 1.5：Self-Healing（匹配17类错误，0秒）
- Level 2：Debug（深度诊断，2秒退避）
- Level 2.5：Micro-Replan（连续3次Debug无效，仅重规划失败任务+直接依赖）
- Level 3：Full Replan（Micro-Replan失败，重建整个计划）
- Level 4：Ask User（所有自动策略失败/振荡检测/总失败>=15）

指数退避公式：wait_time = 2^(failure_count - 1) 秒
"""
)
```

### 处理调整结果

根据返回的 strategy 字段决定下一步行为。先应用指数退避等待，然后按策略分别处理：retry 应用简单调整后重新执行，debug 调用 debug agent 深度诊断后重新执行，replan 交给 planner 重新设计计划，ask_user 通过 AskUserQuestion 请求用户指导。

```python
if adjustment_result["strategy"] not in ["retry", "debug", "replan", "ask_user"]:
    raise Exception("无效的调整策略")

# 应用指数退避
if "retry_config" in adjustment_result:
    backoff_seconds = adjustment_result["retry_config"]["backoff_seconds"]
    if backoff_seconds > 0:
        print(f"等待 {backoff_seconds} 秒（指数退避）...")
        time.sleep(backoff_seconds)

# 根据策略执行
if adjustment_result["strategy"] == "retry":
    apply_adjustments(adjustment_result["adjustments"])
    return "retry"  # 回到任务执行

elif adjustment_result["strategy"] == "debug":
    debug_result = Agent(agent="debug", prompt="分析失败原因...")
    apply_debug_fixes(debug_result)
    return "retry"  # 回到任务执行

elif adjustment_result["strategy"] == "replan":
    new_plan = Agent(agent="planner", prompt="重新设计计划...")
    return "replan"  # 回到计划设计

elif adjustment_result["strategy"] == "ask_user":
    user_guidance = AskUserQuestion(adjustment_result["question"])
    return "retry"  # 回到任务执行
```

### 输出调整报告

```python
print(f"[MindFlow·{task_name}·失败调整/{iteration + 1}·{adjustment_result['strategy']}]")
print(f"调整报告：{adjustment_result['report']}")

for adj in adjustment_result["adjustments"]:
    print(f"  {adj['task_id']}: {adj['action']}")
    print(f"    详情：{adj['details']}")
```

</execution_flow>

<reference>

## 快速参考

| 级别 | 策略 | 触发条件 | 等待时间 | Loop 流向 |
|------|------|---------|---------|----------|
| Level 1 | Retry with adjustment | 1次相同错误 | 0秒 | 任务执行 |
| Level 1.5 | Self-Healing | 匹配17类错误 | 0秒 | 任务执行 |
| Level 2 | Debug | 持续性错误 | 2秒 | 任务执行 |
| Level 2.5 | Micro-Replan | 连续3次Debug无效 | 4秒 | 部分计划重设计 |
| Level 3 | Full Replan | Micro-Replan失败 | 8秒 | 完整计划重设计 |
| Level 4 | Ask User | 所有自动策略失败/振荡/总失败>=15 | - | 等待用户 |

### Level 2.5 Micro-Replan 详细定义

**触发条件**：连续 3 次 Debug 无效

**行为**：仅重规划失败任务及其直接依赖，保留所有成功完成的任务

**输出格式**：
```json
{
  "status": "micro_replan",
  "strategy": "micro_replan",
  "report": "Debug 3 次无效，对失败任务局部重规划。",
  "replan_scope": {
    "failed_tasks": ["T3"],
    "direct_dependencies": ["T4"],
    "keep_completed": ["T1", "T2"],
    "new_approach": "调整 T3 实现方式"
  }
}
```

**失败条件**：Micro-Replan 失败 -> 升级到 Level 3 Full Replan

### 振荡检测

当检测到策略振荡模式（A->B->A->B 重复出现）时，立即升级到 Level 4 Ask User，避免无限循环。

### 紧急逃逸

总失败次数 >= 15 时，无论当前处于哪个级别，立即升级到 Level 4 Ask User。

## 详细文档

- [失败升级策略指南](adjuster-strategies.md) - 六级升级策略、停滞检测、Circuit Breaker、指数退避
- [升级流程图](escalation-flowchart.md) - 分级升级决策树、振荡检测、紧急逃逸
- [输出格式文档](adjuster-output-formats.md) - 四种策略的详细 JSON 示例
- [集成示例](adjuster-integration.md) - Loop 集成、处理流程、停滞检测

## 注意事项

始终使用 `Agent(agent="task:adjuster", ...)` 调用，检查 strategy 字段确认调整策略，应用指数退避避免重试风暴。对于 ask_user 策略必须通过 AskUserQuestion 请求指导。记录失败历史用于停滞检测，限制最大重试次数（默认 3 次）。不要无限重试、不要忽略失败历史、不要跳过指数退避、不要在停滞时继续自动重试、不要修改 adjuster 返回的 JSON 结构。

</reference>
