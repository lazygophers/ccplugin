# Adjuster 输出格式 - Retry 和 Debug

<overview>

本文档定义了 Adjuster 前两级策略的输出格式。retry 是最轻量的恢复策略，适用于首次失败的简单问题（如断言错误、拼写错误），通过直接调整后立即重试解决。debug 在 retry 失败后升级，引入 debug agent 进行深度诊断，适用于根因不明显的重复失败。两种格式共享基础结构（strategy、report、adjustments、retry_config），debug 额外包含 debug_plan。

</overview>

<format_retry>

## 格式 1：Retry（调整后重试）

第 1 次失败时触发。Loop 收到后立即应用调整建议并重新执行（回到任务执行阶段），退避时间 0 秒。

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

字段要求：strategy 必须是 "retry"，report 简短说明失败原因和修复方案（不超过100字），adjustments 包含具体的调整建议列表，retry_config.backoff_seconds 为 0（立即重试）。

</format_retry>

<format_debug>

## 格式 2：Debug（深度诊断）

第 2 次失败时触发，说明简单调整不够，需要更深入的根因分析。Loop 等待 2 秒（指数退避）后调用 debug agent，修复后重新执行（回到任务执行阶段）。

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

字段要求：strategy 必须是 "debug"，report 说明需要深度诊断，adjustments 包含 failure_count 字段，retry_config.backoff_seconds 为 2 秒，debug_plan 定义调试 agent 和关注领域。

</format_debug>

<error_classification>

## 错误分类

Adjuster 在分析失败原因时将错误归类，以便选择最合适的恢复策略：

| 错误类型 | 说明 | 典型恢复策略 |
|---------|------|------------|
| compilation_error | 编译或语法错误 | retry（修复代码后重试） |
| test_failure | 测试断言失败 | retry 或 debug |
| dependency_error | 依赖缺失或版本冲突 | replan（调整依赖方案） |
| runtime_error | 运行时异常 | debug（深度诊断） |
| environment_error | 环境配置问题 | ask_user（可能需要人工配置） |
| timeout | 执行超时 | retry（增加超时时间） |

</error_classification>
