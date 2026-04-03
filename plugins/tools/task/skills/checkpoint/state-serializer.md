# 状态序列化规范

检查点保存在 `.claude/checkpoints/{task_id}.json`，用于序列化/反序列化任务执行状态。

## Schema

必需字段：`user_task`(string) | `task_id` (string) | `iteration`(int≥0) | `phase`(enum) | `context`(object) | `timestamp`(ISO8601)

| 字段 | 类型 | 说明 |
|------|------|------|
| phase | enum | initialization/planning/confirmation/execution/verification/adjustment/completion |
| context.replan_trigger | null/user/adjuster/verifier | 重规划触发来源 |
| context.stalled_count | int | 停滞次数 |
| context.max_stalled_attempts | int | 最大停滞阈值(默认3) |
| plan_md_path | string? | 计划文档路径 |
| additional_state.completed_tasks | string[] | 已完成任务ID |
| additional_state.failed_tasks | object[] | 失败任务(task_id/failure_reason/retry_count) |
| additional_state.execution_metrics | object | started_at/total_duration_seconds/task_count |
| version | string | 格式版本(默认1.0.0) |

## 操作

- **序列化**：构建 checkpoint 对象 → json.dumps(ensure_ascii=False, indent=2)
- **反序列化**：json.loads → 验证必需字段 → 验证 phase/replan_trigger 枚举值
- **过期检查**：timestamp 距今 > 24h 则过期
- **迁移**：检查 version 字段，按版本链升级

## 注意事项

UTF-8编码 | ISO8601时间 | task_id唯一标识 | 新增字段必须Optional | 不含敏感数据
