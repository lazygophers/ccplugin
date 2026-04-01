---
description: "上下文版本化 - 保存快照、列表版本、回滚、对比上下文状态，规划前自动保存，失败后回滚到已知良好状态，防止上下文污染"
model: sonnet
context: fork
user-invocable: false
---

<!-- STATIC_CONTENT: Cacheable -->

# Skills(task:context-versioning) - 上下文版本化

<overview>

为 MindFlow Loop 提供上下文状态管理，规划前自动保存快照，失败后回滚到已知良好状态，防止上下文污染。

文档：[api-reference.md](./api-reference.md) | [integration-examples.md](./integration-examples.md)

</overview>

<quick_reference>

## API

| 方法 | 功能 | 时机 | 返回 |
|------|------|------|------|
| save_context_snapshot() | 保存上下文快照 | planner前/执行成功后/手动 | 版本ID(v1,v2...) |
| list_context_versions() | 列出历史快照 | 查询/选择回滚目标/调试 | 快照列表(id,iteration,phase,status,time) |
| rollback_context() | 回滚到指定快照 | 验证失败/手动/污染严重 | 完整快照数据或None |
| compare_context_snapshots() | 对比两个快照差异 | 分析失败原因/诊断污染 | 差异(added/removed/changed) |

</quick_reference>

<notes>

存储：`.claude/context/{task_id}/v{iteration}.json`。状态：pending→success/failed。回滚默认最近 success 快照。

与 checkpoint 区别：checkpoint 是进程级中断恢复，context-versioning 是逻辑级上下文回滚。

</notes>

<!-- /STATIC_CONTENT -->
