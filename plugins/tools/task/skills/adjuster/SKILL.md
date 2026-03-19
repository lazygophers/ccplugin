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

四级升级策略按失败次数递进：retry（首次失败，立即重试）、debug（第2次，深度诊断）、replan（第3次，重新规划）、ask_user（停滞3次，请求用户指导）。指数退避公式 `2^(failure_count - 1)` 秒确保重试间隔逐步增大。

</overview>

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
- 第 1 次失败：Retry（0 秒，立即重试）
- 第 2 次失败：Debug（2 秒退避，深度诊断）
- 第 3 次失败：Replan（4 秒退避，重新规划）
- 停滞 3 次：Ask User（请求用户指导）

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

| 失败次数 | 策略 | 等待时间 | Loop 流向 |
|---------|------|---------|----------|
| 1 | retry | 0秒 | 任务执行 |
| 2 | debug | 2秒 | 任务执行 |
| 3 | replan | 4秒 | 计划设计 |
| 停滞 3次 | ask_user | - | 任务执行 |

## 详细文档

- [失败升级策略指南](adjuster-strategies.md) - 四级升级策略、停滞检测、Circuit Breaker、指数退避
- [输出格式文档](adjuster-output-formats.md) - 四种策略的详细 JSON 示例
- [集成示例](adjuster-integration.md) - Loop 集成、处理流程、停滞检测

## 注意事项

始终使用 `Agent(agent="task:adjuster", ...)` 调用，检查 strategy 字段确认调整策略，应用指数退避避免重试风暴。对于 ask_user 策略必须通过 AskUserQuestion 请求指导。记录失败历史用于停滞检测，限制最大重试次数（默认 3 次）。不要无限重试、不要忽略失败历史、不要跳过指数退避、不要在停滞时继续自动重试、不要修改 adjuster 返回的 JSON 结构。

</reference>
