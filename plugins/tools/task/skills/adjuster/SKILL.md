---
agent: task:adjuster
description: 失败调整规范 - 分析失败原因、检测停滞、应用升级策略的执行规范
model: sonnet
context: fork
user-invocable: false
---

# Skills(task:adjuster) - 失败调整规范

## 适用场景

当你需要处理任务失败并确定恢复策略时，使用此 skill：

- ✓ Loop 命令失败调整（Adjustment / Act）阶段
- ✓ 分析失败任务的错误原因
- ✓ 检测停滞模式（相同错误重复出现）
- ✓ 应用分级失败升级策略
- ✓ 防止级联失败和无限重试循环

## 核心原则

### 弹性模式最佳实践

- **Circuit Breaker**：检测失败后熔断，防止级联失败
- **Retry 策略**：指数退避（2^n 秒），避免重试风暴
- **组合模式**：Retry + Circuit Breaker + Timeout
- **分级升级**：retry → debug → replan → ask_user

详见：[输出格式文档](adjuster-output-formats.md)

## 执行流程

### 调用 adjuster agent

```python
# 基础调用
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

```python
# 检查策略
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
    # 首次失败：调整后重试
    print(f"策略：调整后重试")
    apply_adjustments(adjustment_result["adjustments"])
    return "retry"  # 回到任务执行

elif adjustment_result["strategy"] == "debug":
    # 重复失败：深度诊断
    print(f"策略：深度诊断")
    debug_result = Agent(agent="debug", prompt="分析失败原因...")
    apply_debug_fixes(debug_result)
    return "retry"  # 回到任务执行

elif adjustment_result["strategy"] == "replan":
    # 持续失败：重新规划
    print(f"策略：重新规划")
    new_plan = Agent(agent="planner", prompt="重新设计计划...")
    return "replan"  # 回到计划设计

elif adjustment_result["strategy"] == "ask_user":
    # 停滞检测：请求用户指导
    print(f"策略：请求用户指导")
    user_guidance = AskUserQuestion(adjustment_result["question"])
    # 根据用户回答继续
    return "retry"  # 回到任务执行
```

### 输出调整报告

```python
# 输出调整报告
print(f"[MindFlow·{task_name}·失败调整/{iteration + 1}·{adjustment_result['strategy']}]")
print(f"调整报告：{adjustment_result['report']}")

# 输出调整详情
for adj in adjustment_result["adjustments"]:
    print(f"  {adj['task_id']}: {adj['action']}")
    print(f"    详情：{adj['details']}")
```

## 输出格式

Adjuster 支持四种输出格式，对应不同的失败级别：

1. **retry** - 首次失败（0秒），立即重试
2. **debug** - 重复失败（2秒），深度诊断
3. **replan** - 持续失败（4秒），重新规划
4. **ask_user** - 停滞 3 次，请求用户指导

详见：[输出格式文档](adjuster-output-formats.md)

---

## 详细文档

完整的输出格式、失败策略、集成示例和错误分类详见以下文档：

- **[失败升级策略指南](adjuster-strategies.md)** - 四级升级策略、停滞检测、Circuit Breaker、指数退避
- **[输出格式文档](adjuster-output-formats.md)** - 四种策略的详细说明和示例
- **[集成示例](adjuster-integration.md)** - Loop 集成、处理流程、停滞检测

## 快速参考

### 失败升级策略

| 失败次数 | 策略 | 等待时间 | Loop 流向 |
|---------|------|---------|----------|
| 1 | `retry` | 0秒 | 任务执行 |
| 2 | `debug` | 2秒 | 任务执行 |
| 3 | `replan` | 4秒 | 计划设计 |
| 停滞 3次 | `ask_user` | - | 任务执行 |

**指数退避**：`2^(failure_count - 1)` 秒

## 注意事项

- ✓ 始终使用 `Agent(agent="task:adjuster", ...)` 调用
- ✓ 检查 `strategy` 字段确认调整策略
- ✓ 应用指数退避，避免快速重试加剧问题
- ✓ 处理四种策略：retry / debug / replan / ask_user
- ✓ 对于 ask_user，必须通过 `AskUserQuestion` 请求指导
- ✓ 记录失败历史，用于停滞检测
- ✓ 限制最大重试次数（默认 3 次）
- ✗ 不要无限重试，防止资源耗尽
- ✗ 不要忽略失败历史
- ✗ 不要跳过指数退避
- ✗ 不要在停滞时继续自动重试
- ✗ 不要修改 adjuster 返回的 JSON 结构
