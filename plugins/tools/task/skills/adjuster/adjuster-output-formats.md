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

### Loop 行为

通过 `AskUserQuestion` 请求用户指导，根据回答继续（回到任务执行）。

### 字段说明

- `strategy`: 必须是 `"ask_user"`
- `report`: 说明停滞情况
- `stalled_info`: 停滞详细信息
  - `occurrences`: 重复次数（≥ 3）
  - `error_similarity`: 错误相似度（0-1，≥ 0.9 表示相同错误）
- `question`: 向用户提出的问题，包含可能原因和建议方案
- `context.task_history`: 失败历史记录

---

## 字段参考

### 通用字段

| 字段 | 类型 | 说明 | 必填 | 适用策略 |
|------|------|------|------|---------|
| `strategy` | string | 策略类型 | ✓ | 所有 |
| `report` | string | 简短报告（≤100字） | ✓ | 所有 |
| `adjustments` | array | 调整建议列表 | ✓ | 所有 |
| `retry_config` | object | 重试配置 | ✓ | retry / debug / replan |
| `debug_plan` | object | 调试计划 | ✗ | debug |
| `replan_options` | array | 重新规划选项 | ✗ | replan |
| `stalled_info` | object | 停滞信息 | ✗ | ask_user |
| `question` | string | 用户问题 | ✗ | ask_user |

### Adjustment 对象

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `task_id` | string | 任务 ID | `"T3"` |
| `task_name` | string | 任务名称 | `"编写认证测试"` |
| `action` | string | 调整动作 | `"修复测试断言"` |
| `details` | string | 详细说明 | `"将 assertEqual(result, 0) 改为..."` |
| `error_type` | string | 错误类型 | `"test_failure"` |
| `root_cause` | string | 根本原因（可选） | `"断言条件错误"` |
| `failure_count` | number | 失败次数（debug/replan） | `2` |
| `feasibility` | string | 可行性（replan） | `"low"` |

### Retry Config 对象

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `max_retries` | number | 最大重试次数 | `3` |
| `current_retry` | number | 当前重试次数 | `1` |
| `backoff_seconds` | number | 退避时间（秒） | `0` / `2` / `4` |

---

## 失败升级策略表

| 失败次数 | 策略 | 等待时间 | 行为 | Loop 流向 |
|---------|------|---------|------|----------|
| 首次失败 | `retry` | 0 秒 | 分析错误，提供修复建议，立即重试 | 回到任务执行 |
| 重复失败 | `debug` | 2 秒 | 调用 debug agent 深度诊断 | 回到任务执行 |
| 持续失败 | `replan` | 4 秒 | 评估可行性，建议拆分或调整方案 | 回到计划设计 |
| 停滞 3 次 | `ask_user` | 无限 | 识别停滞模式，请求用户干预 | 回到任务执行 |

**指数退避公式**：`wait_time = 2^(failure_count - 1)` 秒

---

## 错误分类

| 错误类型 | 示例错误 | 处理策略 |
|---------|---------|---------|
| **编译错误** | `SyntaxError`, `ImportError`, `TypeError` | 修复语法/导入/类型问题 |
| **测试错误** | `AssertionError`, `TestFailure` | 修复断言/测试逻辑 |
| **依赖错误** | `ModuleNotFoundError`, `VersionConflict` | 安装/升级依赖 |
| **运行时错误** | `NullPointerException`, `OutOfMemoryError` | 修复代码逻辑/优化资源 |
| **环境错误** | `PermissionError`, `ConnectionError` | 检查配置/权限/网络 |

---

## 报告编写指南

### Retry 报告

**格式**：
```
[任务 ID] [错误类型]：[错误描述]。修复方案：[具体修复方法]。
```

**示例**：
```
T3 测试失败：断言错误 (AssertionError: Expected 0 but got 1)。修复方案：调整断言条件，重新运行测试。
```

### Debug 报告

**格式**：
```
[任务 ID] [问题描述]，相同错误重复出现。需要深度诊断：调用 debug agent 分析[分析方向]。
```

**示例**：
```
T3 测试再次失败，相同错误重复出现。需要深度诊断：调用 debug agent 分析测试失败的根本原因。
```

### Replan 报告

**格式**：
```
[任务 ID] 连续 [N] 次失败，当前方案可能不可行。建议重新规划：[重新规划方案]。
```

**示例**：
```
T3 连续 3 次失败，当前方案可能不可行。建议重新规划：将 T3 拆分为两个子任务，或调整技术方案。
```

### Ask User 报告

**格式**：
```
检测到停滞：[任务 ID] [问题描述]已重复 [N] 次，相同错误反复出现 ([错误信息])。自动恢复失败，需要用户指导。
```

**示例**：
```
检测到停滞：T3 测试失败已重复 3 次，相同错误反复出现 (AssertionError: Expected 0 but got 1)。自动恢复失败，需要用户指导。
```
