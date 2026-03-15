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

**Circuit Breaker 模式（熔断器）**：
- 检测失败后临时阻止访问，防止重复尝试加剧问题
- 三态机制：Closed（正常）→ Open（熔断）→ Half-Open（试探）
- 帮助系统有效恢复，防止级联失败

**Retry 策略（重试）**：
- 指数退避：每次重试等待时间递增（2^n 秒）
- 避免雷鸣群效应（所有客户端同时重试）
- 单独使用可能加剧故障，应与 Circuit Breaker 组合

**组合模式**：
- Retry 在外层，Circuit Breaker 在内层，Timeout 最内层
- 先重试，失败后熔断，避免重试风暴

**分级升级**：
- 第 1 次失败：Retry（调整后重试）
- 第 2 次失败：Debug（深度诊断）
- 第 3 次失败：Replan（重新规划）
- 停滞检测：Ask User（请求用户指导）

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

### 格式 1：Retry（调整后重试）

**触发条件**：第 1 次失败

```json
{
  "strategy": "retry",
  "report": "T3 测试失败：断言错误 (AssertionError: Expected 0 but got 1)。修复方案：调整断言条件，重新运行测试。",
  "adjustments": [
    {
      "task_id": "T3",
      "task_name": "编写认证测试",
      "action": "修复测试断言",
      "details": "将 assertEqual(result, 0) 改为 assertEqual(result, 1)",
      "error_type": "test_failure",
      "root_cause": "断言条件错误"
    }
  ],
  "retry_config": {
    "max_retries": 3,
    "current_retry": 1,
    "backoff_seconds": 0
  }
}
```

**行为**：立即修复并重试（回到任务执行）。

---

### 格式 2：Debug（深度诊断）

**触发条件**：第 2 次失败

```json
{
  "strategy": "debug",
  "report": "T3 测试再次失败，相同错误重复出现。需要深度诊断：调用 debug agent 分析测试失败的根本原因。",
  "adjustments": [
    {
      "task_id": "T3",
      "task_name": "编写认证测试",
      "action": "调用调试 agent",
      "details": "使用 debug agent 分析：1) 测试数据是否正确；2) 被测代码逻辑是否有误；3) 测试环境是否一致",
      "error_type": "test_failure",
      "failure_count": 2
    }
  ],
  "retry_config": {
    "max_retries": 3,
    "current_retry": 2,
    "backoff_seconds": 2
  },
  "debug_plan": {
    "agent": "debug（调试专家）",
    "focus_areas": ["测试数据", "代码逻辑", "环境配置"]
  }
}
```

**行为**：等待 2 秒（指数退避），然后调用 debug agent，修复后重试（回到任务执行）。

---

### 格式 3：Replan（重新规划）

**触发条件**：第 3 次失败

```json
{
  "strategy": "replan",
  "report": "T3 连续 3 次失败，当前方案可能不可行。建议重新规划：将 T3 拆分为两个子任务，或调整技术方案。",
  "adjustments": [
    {
      "task_id": "T3",
      "task_name": "编写认证测试",
      "action": "重新规划任务",
      "details": "建议方案：1) 将 T3 拆分为 T3a（基础功能测试）和 T3b（边界测试）；2) 或调整测试框架（从 pytest 切换到 unittest）",
      "error_type": "test_failure",
      "failure_count": 3,
      "feasibility": "low"
    }
  ],
  "retry_config": {
    "max_retries": 3,
    "current_retry": 3,
    "backoff_seconds": 4
  },
  "replan_options": [
    {
      "option": "拆分任务",
      "description": "将 T3 拆分为 T3a（基础测试）和 T3b（边界测试）",
      "estimated_effort": "medium"
    },
    {
      "option": "调整方案",
      "description": "切换测试框架或调整测试策略",
      "estimated_effort": "high"
    }
  ]
}
```

**行为**：等待 4 秒（指数退避），然后调用 planner agent 重新规划（回到计划设计）。

---

### 格式 4：Ask User（请求用户指导）

**触发条件**：停滞 3 次（相同错误重复 3 次）

```json
{
  "strategy": "ask_user",
  "report": "检测到停滞：T3 测试失败已重复 3 次，相同错误反复出现 (AssertionError: Expected 0 but got 1)。自动恢复失败，需要用户指导。",
  "stalled_info": {
    "task_id": "T3",
    "task_name": "编写认证测试",
    "error": "AssertionError: Expected 0 but got 1",
    "occurrences": 3,
    "error_similarity": 0.95,
    "first_occurrence": "2026-03-15 10:30:00",
    "last_occurrence": "2026-03-15 11:45:00"
  },
  "question": "T3 测试连续失败 3 次，相同错误反复出现。可能的原因：\n1. 验收标准设置错误（期望值应为 1 而非 0）\n2. 被测代码实现有误\n3. 测试数据不正确\n\n建议的解决方案：\nA. 调整验收标准（将期望值改为 1）\nB. 修复被测代码逻辑\nC. 检查并修正测试数据\n\n请问应该采取哪种方案？或者您有其他建议吗？",
  "context": {
    "task_history": [
      {
        "iteration": 1,
        "error": "AssertionError: Expected 0 but got 1",
        "action_taken": "调整断言条件"
      },
      {
        "iteration": 2,
        "error": "AssertionError: Expected 0 but got 1",
        "action_taken": "深度诊断"
      },
      {
        "iteration": 3,
        "error": "AssertionError: Expected 0 but got 1",
        "action_taken": "重新规划"
      }
    ]
  }
}
```

**行为**：通过 `AskUserQuestion` 请求用户指导，根据回答继续（回到任务执行）。

---

## 字段说明

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| `strategy` | string | 策略类型：`retry` / `debug` / `replan` / `ask_user` | ✓ |
| `report` | string | 简短报告（≤100字） | ✓ |
| `adjustments` | array | 调整建议列表 | ✓ |
| `retry_config` | object | 重试配置（含退避时间） | ✓ |
| `debug_plan` | object | 调试计划（仅 debug 策略） | ✗ |
| `replan_options` | array | 重新规划选项（仅 replan 策略） | ✗ |
| `stalled_info` | object | 停滞信息（仅 ask_user 策略） | ✗ |
| `question` | string | 用户问题（仅 ask_user 策略） | ✗ |

### Adjustment 对象字段

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `task_id` | string | 任务 ID | `"T3"` |
| `task_name` | string | 任务名称 | `"编写认证测试"` |
| `action` | string | 调整动作 | `"修复测试断言"` |
| `details` | string | 详细说明 | `"将 assertEqual(result, 0) 改为..."` |
| `error_type` | string | 错误类型 | `"test_failure"` |
| `root_cause` | string | 根本原因（可选） | `"断言条件错误"` |

## 失败升级策略表

| 失败次数 | 策略 | 等待时间 | 行为 | Loop 流向 |
|---------|------|---------|------|----------|
| 首次失败 | Retry | 0 秒 | 分析错误，提供修复建议，立即重试 | 回到任务执行 |
| 重复失败 | Debug | 2 秒 | 调用 debug agent 深度诊断 | 回到任务执行 |
| 持续失败 | Replan | 4 秒 | 评估可行性，建议拆分或调整方案 | 回到计划设计 |
| 停滞 3 次 | Ask User | 无限 | 识别停滞模式，请求用户干预 | 回到任务执行 |

**指数退避公式**：`wait_time = 2^(failure_count - 1)` 秒

## 错误分类

| 错误类型 | 示例错误 | 处理策略 |
|---------|---------|---------|
| **编译错误** | `SyntaxError`, `ImportError`, `TypeError` | 修复语法/导入/类型问题 |
| **测试错误** | `AssertionError`, `TestFailure` | 修复断言/测试逻辑 |
| **依赖错误** | `ModuleNotFoundError`, `VersionConflict` | 安装/升级依赖 |
| **运行时错误** | `NullPointerException`, `OutOfMemoryError` | 修复代码逻辑/优化资源 |
| **环境错误** | `PermissionError`, `ConnectionError` | 检查配置/权限/网络 |

## 集成示例

### Loop 命令中的使用

```python
# loop 命令的失败调整阶段
def adjustment_phase(task_description, iteration):
    """Loop 命令失败调整（Adjustment / Act）阶段"""

    # 调用 adjuster agent
    adjustment_result = Agent(
        agent="task:adjuster",
        prompt=f"""执行失败调整：

任务目标：{task_description}
当前迭代：第 {iteration + 1} 轮

要求：
1. 获取所有失败任务的详细信息
2. 分析失败原因
3. 检测停滞模式
4. 应用分级升级策略
5. 生成调整报告（≤100字）
"""
    )

    # 输出报告
    print(f"[MindFlow·{task_description}·失败调整/{iteration + 1}·{adjustment_result['strategy']}]")
    print(f"调整报告：{adjustment_result['report']}")

    # 应用指数退避
    if "retry_config" in adjustment_result:
        backoff_seconds = adjustment_result["retry_config"]["backoff_seconds"]
        if backoff_seconds > 0:
            print(f"应用指数退避：等待 {backoff_seconds} 秒...")
            time.sleep(backoff_seconds)

    # 根据策略执行
    strategy = adjustment_result["strategy"]

    if strategy == "retry":
        # 应用调整建议
        for adj in adjustment_result["adjustments"]:
            apply_adjustment(adj)
        return "execution"  # 回到任务执行

    elif strategy == "debug":
        # 调用 debug agent
        debug_result = Agent(
            agent="debug",
            prompt=f"深度分析失败原因：{adjustment_result['debug_plan']}"
        )
        apply_debug_fixes(debug_result)
        return "execution"  # 回到任务执行

    elif strategy == "replan":
        # 调用 planner agent 重新规划
        new_plan = Agent(
            agent="planner",
            prompt=f"重新规划任务：{adjustment_result['replan_options']}"
        )
        return "planning"  # 回到计划设计

    elif strategy == "ask_user":
        # 请求用户指导
        user_response = AskUserQuestion(adjustment_result["question"])
        # 根据用户回答应用修复
        apply_user_guidance(user_response)
        return "execution"  # 回到任务执行

    return "execution"  # 默认回到任务执行
```

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
