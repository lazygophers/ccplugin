# Adjuster 输出格式 - Replan & Ask User

## ask_user 输出

- `strategy`: `"ask_user"`
- `report`: 停滞情况说明（≤100字）
- `stalled_info`: `{task_id, task_name, error, occurrences(≥3), error_similarity(0-1)}`
- `question`: 向用户提问，含可能原因和建议方案
- `context.task_history`: 失败历史 `[{iteration, error, action_taken}]`

Loop行为：`AskUserQuestion` 请求指导，根据回答继续。

## 通用字段参考

| 字段 | 类型 | 必填 | 适用策略 |
|------|------|------|---------|
| strategy | string | 必填 | 所有 |
| report | string(≤100字) | 必填 | 所有 |
| adjustments | array | 必填 | 所有 |
| retry_config | object | 必填 | retry/debug/replan |
| debug_plan | object | 可选 | debug |
| replan_options | array | 可选 | replan |
| stalled_info | object | 可选 | ask_user |
| question | string | 可选 | ask_user |

## Adjustment对象

`{task_id, task_name, action, details, error_type, root_cause?, failure_count?, feasibility?}`

## Retry Config

`{max_retries(默认3), current_retry, backoff_seconds}` | 退避公式：`2^(failure_count-1)`秒

## 升级策略表

| 失败次数 | 策略 | 等待 | Loop流向 |
|---------|------|------|---------|
| 首次 | retry | 0s | 任务执行 |
| 重复 | debug | 2s | 任务执行 |
| 持续 | replan | 4s | 计划设计 |
| 停滞3次 | ask_user | - | 用户决定 |

## 错误分类

| 类型 | 示例 | 策略 |
|------|------|------|
| 编译 | SyntaxError/ImportError | 修复语法/导入 |
| 测试 | AssertionError | 修复断言/逻辑 |
| 依赖 | ModuleNotFoundError | 安装/升级 |
| 运行时 | NullPointer/OOM | 修复逻辑/优化 |
| 环境 | PermissionError | 检查配置/权限 |

## 报告模板

- **retry**: `[任务ID] [错误类型]：[描述]。修复方案：[方法]。`
- **debug**: `[任务ID] [描述]，相同错误重复。需深度诊断：[方向]。`
- **replan**: `[任务ID] 连续N次失败，方案不可行。建议：[方案]。`
- **ask_user**: `检测到停滞：[任务ID] [描述]已重复N次。需用户指导。`
