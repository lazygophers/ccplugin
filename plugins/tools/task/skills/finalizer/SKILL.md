---
description: 资源清理规范 - 系统性资源清理、任务终止、最终报告生成的执行规范
model: haiku
context: fork
user-invocable: false
---

<!-- STATIC_CONTENT: Cacheable -->

# Skills(task:finalizer) - 资源清理规范

<overview>

Loop 完成或紧急停止时执行资源清理。防御性清理：每个操作独立执行，单个失败不阻断剩余流程。按创建逆序清理：停止任务 → 清理文件 → 释放其他资源。

</overview>

<execution_flow>

调用：`Skill(skill="task:finalizer", args="执行资源清理：\n状态：{loop_state}\n已完成：{completed_tasks}\n未完成：{pending_tasks}\n计划文件：{plan_md_path}\ntask_id：{task_id}\ntask_hash：{task_hash}\n要求：1.盘点资源 2.停止运行中任务 3.清理全部6类中间产物 4.生成清理报告\n遇错误继续清理。")`

**清理目标（6类中间产物）**：

| 类型 | 路径模式 | 清理条件 |
|------|---------|---------|
| 计划文件 | `.claude/plans/{name}-{N}.md` + `.html` | 始终删除 |
| 检查点 | `.claude/checkpoints/{hash}.json` | 始终删除 |
| 审批日志 | `.claude/plans/{task_hash}/approval-log.json` | 始终删除 |
| 指标数据 | `.claude/plans/{task_hash}/metrics.json` | 始终删除 |
| 上下文快照 | `.claude/context-versions/{task_hash}/v*.json` | 始终删除 |
| 草稿产物 | `.claude/plans/*-draft-*.md` | 始终删除 |

**清理顺序**：检查点 → 上下文快照 → 审批日志 → 指标数据 → 草稿 → 计划文件 → 空目录

**保留规则**：任务状态文件(`.claude/task/`)保留30天 | 情节记忆永久保留 | 用户文件不清理

结果处理：检查 `status` ∈ [completed, partially_completed] → 输出 report + cleanup_summary → 处理 errors 列表

</execution_flow>

<output_format>

JSON: `{status, report(≤200字), cleanup_summary{tasks_terminated,tasks_cancelled,tasks_failed,files_deleted,files_failed,empty_dirs_removed,total_space_freed}, cleaned_resources{tasks[],files[],directories[]}, errors[{type,resource,error}]}`

- `status`: completed（全部成功）| partially_completed（部分成功）| failed（全部失败）
- 错误类型：task_termination_failed | file_deletion_failed | permission_denied | resource_locked

</output_format>

<reference>

详细文档：[资源清理指南](finalizer-cleanup-guide.md)

注意：即使部分失败也完成剩余清理，不因单个错误停止整个流程。

</reference>

<!-- /STATIC_CONTENT -->
