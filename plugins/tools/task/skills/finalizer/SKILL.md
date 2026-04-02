---
description: "Finalizer 资源清理 - Loop 完成或紧急停止时调用：按创建逆序清理计划/检查点/快照等4类产物，生成最终报告。防御性清理，单个失败不阻断。由 Loop 内部调度，不直接面向用户"
model: haiku
context: fork
user-invocable: false
hooks:
  SubagentStop:
    - hooks:
        - type: command
          command: "VALIDATE_TYPE=finalizer bash ${CLAUDE_PLUGIN_ROOT}/hooks/validate-output.sh"
          timeout: 10
---


# Skills(task:finalizer) - 资源清理规范

<overview>

Loop 完成或紧急停止时执行资源清理。防御性清理：每个操作独立执行，单个失败不阻断剩余流程。按创建逆序清理：停止任务 → 清理文件 → 释放其他资源。

</overview>

<execution_flow>

调用：`Skill(skill="task:finalizer", args="执行资源清理：\n状态：{loop_state}\n已完成：{completed_tasks}\n未完成：{pending_tasks}\n计划文件：{plan_md_path}\ntask_id：{task_id}\n要求：1.盘点资源 2.停止运行中任务 3.清理全部4类中间产物 4.生成清理报告\n遇错误继续清理。")`

**清理目标（4类中间产物）**：

| 类型 | 路径模式 | 清理条件 |
|------|---------|---------|
| 计划文件 | `.claude/tasks/{task_id}/plan.md` | 始终删除（包括 draft 状态文件） |
| 检查点 | `.claude/checkpoints/{task_id}.json` | 始终删除 |
| 审批日志 | `.claude/tasks/{task_id}/approval-log.json` | 始终删除 |
| 上下文快照 | `.claude/context/{task_id}/v*.json` | 始终删除 |

**清理顺序**：检查点 → 上下文快照 → 审批日志 → 计划文件（含所有状态） → 空目录

**清理规则**：任务状态文件(`.claude/tasks/{task_id}/`)立即清理 | 情节记忆永久保留 | 用户文件不清理

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

