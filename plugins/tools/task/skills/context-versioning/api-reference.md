# Context Versioning API Reference

快照存储：`.claude/context/{task_id}/v{iteration}.json`

## API

| 函数 | 参数 | 返回 | 说明 |
|------|------|------|------|
| save_context_snapshot | user_task, iteration, phase, context_state, status="pending", metadata={} | version_id(str) | 保存快照。时机：planner前+执行成功后标记success |
| list_context_versions | user_task, status_filter=None | list[dict] | 列出快照(version_id/iteration/phase/status/timestamp)，按迭代倒序 |
| rollback_context | user_task, target_version=None | dict/None | 回滚到指定版本(默认最近success)。返回完整snapshot含context_state |
| compare_context_snapshots | user_task, version_a, version_b | dict | 对比差异：added_keys/removed_keys/changed_values |

## 注意事项

- 状态：pending/success/failed
- 与checkpoint区别：checkpoint用于进程级中断恢复，context-versioning用于逻辑级上下文回滚
- 每次迭代一个快照文件，无并发冲突
- 任务完成后建议保留用于审计
