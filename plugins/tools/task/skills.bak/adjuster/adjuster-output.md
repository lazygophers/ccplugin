# Adjuster 输出格式

**所有结果通过文件传递**：adjuster 完成后更新 `.lazygophers/tasks/{task_id}/metadata.json` 的 `result` 字段，禁止输出 JSON 到对话。

## 通用字段

| 字段 | 类型 | 必填 | 适用策略 |
|------|------|------|---------|
| strategy | string | 必填 | 所有（retry/debug/replan/ask_user） |
| report | string(≤100字) | 必填 | 所有 |
| adjustments | array | 必填 | 所有 |
| retry_config | object | 必填 | retry/debug/replan |
| debug_plan | object | 可选 | debug |
| replan_options | array | 可选 | replan |
| stalled_info | object | 可选 | ask_user |
| question | string | 可选 | ask_user |

### Adjustment对象

`{task_id, task_name, action, details, error_type, root_cause?, failure_count?, feasibility?}`

### Retry Config

`{max_retries(默认3), current_retry, backoff_seconds}` | 退避公式：`2^(failure_count-1)`秒

## retry（L1：首次失败）

轻量恢复，直接调整后立即重试。

输出：`{strategy:"retry", report, adjustments[{task_id,task_name,action,details,error_type,root_cause}], retry_config:{max_retries:3,current_retry:1,backoff_seconds:0}}`

Loop行为：应用调整 → 回到PromptOptimization，退避 0s。

## debug（L2：持续失败）

简单调整不够，调用 debug agent 深度诊断。

输出：在 retry 基础上增加 `debug_plan:{agent,focus_areas[]}`，adjustments 含 `failure_count`，`backoff_seconds:2`

Loop行为：等待 2s → 调用 debug agent → 修复 → 回到PromptOptimization。

## replan（L3：方案不可行）

输出：在 retry 基础上增加 `replan_options[]`，`backoff_seconds:4`

Loop行为：等待 4s → 回到PromptOptimization。

## ask_user（L4：停滞/振荡）

输出：`{strategy:"ask_user", report, stalled_info:{task_id,task_name,error,occurrences(≥3),error_similarity(0-1)}, question:"...", context:{task_history:[{iteration,error,action_taken}]}}`

Loop行为：`AskUserQuestion` 请求指导，根据回答继续。

## 错误分类

| 类型 | 示例 | 典型策略 |
|------|------|---------|
| compilation_error | SyntaxError/ImportError | retry |
| test_failure | AssertionError | retry/debug |
| dependency_error | ModuleNotFoundError | replan |
| runtime_error | NullPointer/OOM | debug |
| environment_error | PermissionError | ask_user |
| timeout | 执行超时 | retry(增加超时) |

## 报告模板

- **retry**: `[任务ID] [错误类型]：[描述]。修复方案：[方法]。`
- **debug**: `[任务ID] [描述]，相同错误重复。需深度诊断：[方向]。`
- **replan**: `[任务ID] 连续N次失败，方案不可行。建议：[方案]。`
- **ask_user**: `检测到停滞：[任务ID] [描述]已重复N次。需用户指导。`
