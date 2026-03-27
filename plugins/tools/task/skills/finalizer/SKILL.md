---
description: 资源清理规范 - 系统性资源清理、任务终止、最终报告生成的执行规范
model: haiku
context: fork
user-invocable: false
---

# Skills(task:finalizer) - 资源清理规范

<overview>

Loop 完成或紧急停止时执行资源清理。防御性清理：每个操作 try-except 包裹，部分失败不阻断剩余流程。按创建逆序清理：停止任务 → 清理文件 → 释放其他资源。

</overview>

<execution_flow>

调用：`Agent(agent="task:finalizer", prompt="执行资源清理：\n状态：{loop_state}\n已完成：{completed_tasks}\n未完成：{pending_tasks}\n计划文件：{plan_md_path}\n要求：1.盘点资源 2.停止运行中任务 3.清理计划文件(.md+.html)+临时文件 4.生成清理报告\n遇错误继续清理。")`

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
