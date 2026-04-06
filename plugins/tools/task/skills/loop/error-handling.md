# Loop 错误处理和重试

## 重试策略

| failure_count | 退避 | 策略 |
|---------------|------|------|
| 1 | 0s | 简单调整后重试 |
| 2 | 2s | 深度诊断(debug agent) |
| ≥3 | 4s | 重新规划 |

停滞检测：连续3次相同错误签名→请求用户指导。超过max_stalled_attempts→强制结束+停滞报告。

## Saga Pattern（补偿模式）

任务失败且无法恢复时，按逆序执行补偿操作(sql/file/api)确保系统一致性。补偿在任务定义时声明。

## 错误分类

| 类别 | 示例 | 处理 |
|------|------|------|
| 可恢复 | 网络超时/资源临时不可用/测试失败 | 自动重试+退避 |
| 不可恢复 | 配置错误/权限不足/依赖缺失 | 请求用户介入 |

## 分级升级

L1 Retry(首次,简单调整) → L2 Debug(重复,深度诊断) → L3 Replan(持续,重新规划) → L4 Ask User(停滞,用户指导)

## 结构化错误格式

JSON必含：error_id(`err_`+8位hash) | timestamp | category(recoverable/unrecoverable) | severity(critical/high/medium/low) | message | context(task_id/iteration/phase/agent/file_path/line_number) | stack_trace | suggested_fix(strategy/details/estimated_success_rate) | related_patterns(pattern_id/confidence)

生成：`create_structured_error(message, category, severity, context, ...)`
存储：`.lazygophers/logs/task-{task_id}.log`（JSONL格式，30天保留）
集成：try/except → create_structured_error → log → 传递给adjuster
