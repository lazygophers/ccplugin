# Adjuster 输出格式

本文档包含 Adjuster 的四种输出格式及详细示例。

## 格式 1：Retry（调整后重试）

### 触发条件

第 1 次失败

### 输出示例

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

### Loop 行为

立即修复并重试（回到任务执行）。

### 字段说明

- `strategy`: 必须是 `"retry"`
- `report`: 简短说明失败原因和修复方案（≤100字）
- `adjustments`: 调整建议列表
- `retry_config.backoff_seconds`: `0` 秒（立即重试）

---

## 格式 2：Debug（深度诊断）

### 触发条件

第 2 次失败

### 输出示例

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

### Loop 行为

等待 2 秒（指数退避），然后调用 debug agent，修复后重试（回到任务执行）。

### 字段说明

- `strategy`: 必须是 `"debug"`
- `report`: 说明需要深度诊断
- `adjustments`: 包含 `failure_count` 字段
- `retry_config.backoff_seconds`: `2` 秒
- `debug_plan`: 调试计划，包含 agent 和关注领域

---

## 格式 3：Replan（重新规划）

### 触发条件

第 3 次失败

### 输出示例

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

### Loop 行为

等待 4 秒（指数退避），然后调用 planner agent 重新规划（回到计划设计）。

### 字段说明

- `strategy`: 必须是 `"replan"`
- `report`: 说明需要重新规划
- `adjustments`: 包含 `feasibility` 字段（low 表示当前方案不可行）
- `retry_config.backoff_seconds`: `4` 秒
- `replan_options`: 重新规划的选项列表

---

## 格式 4：Ask User（请求用户指导）

### 触发条件

停滞 3 次（相同错误重复 3 次）

### 输出示例

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
