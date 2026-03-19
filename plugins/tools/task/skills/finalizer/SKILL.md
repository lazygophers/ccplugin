---
agent: task:finalizer
description: 资源清理规范 - 系统性资源清理、任务终止、最终报告生成的执行规范
model: haiku
context: fork
user-invocable: false
---

# Skills(task:finalizer) - 资源清理规范

<overview>

Finalizer 技能在 Loop 迭代完成或紧急停止时执行资源清理。它的设计遵循防御性清理原则——即使部分清理操作失败，也不会阻断剩余清理流程，确保资源不泄漏。清理按依赖关系逆序执行：先停止运行中的任务，再清理文件和目录。

核心原则包括：明确所有权（识别每个资源由哪个组件创建）、使用 try-except 包裹每个清理操作、按创建的逆序清理、即使操作失败也继续剩余流程。

</overview>

<execution_flow>

## 执行流程

### 调用 finalizer agent

```python
finalizer_result = Agent(
    agent="task:finalizer",
    prompt=f"""执行资源清理：

当前状态：{loop_state}
已完成任务：{completed_tasks}
未完成任务：{pending_tasks}

要求：
1. 盘点所有资源（任务、文件、其他）
2. 停止运行中的任务
3. 清理计划文件和临时文件
4. 生成最终清理报告

如遇错误，继续剩余清理流程。
"""
)
```

### 处理结果

```python
if finalizer_result["status"] not in ["completed", "partially_completed"]:
    raise Exception("清理失败")

print(f"清理完成：{finalizer_result['report']}")
print(f"清理任务数：{finalizer_result['cleanup_summary']['tasks_terminated']}")
print(f"清理文件数：{finalizer_result['cleanup_summary']['files_deleted']}")

if finalizer_result.get("errors"):
    print(f"部分清理失败：{len(finalizer_result['errors'])} 个错误")
    for error in finalizer_result["errors"]:
        print(f"  - {error}")
```

</execution_flow>

<output_format>

## 输出格式

### 正常清理成功

```json
{
  "status": "completed",
  "report": "清理完成：终止 3 个任务，删除 5 个文件，清理 2 个空目录。无错误。",
  "cleanup_summary": {
    "tasks_terminated": 3,
    "tasks_cancelled": 0,
    "files_deleted": 5,
    "empty_dirs_removed": 2,
    "total_space_freed": "1.2 MB"
  },
  "cleaned_resources": {
    "tasks": ["T1", "T2", "T3"],
    "files": [
      ".claude/plans/plan_uuid.md",
      ".claude/plans/plan_uuid.html",
      "/tmp/task_temp_file.txt"
    ],
    "directories": [".claude/plans/empty_dir"]
  },
  "errors": []
}
```

### 部分清理失败

```json
{
  "status": "partially_completed",
  "report": "清理部分完成：终止 2/3 个任务，删除 4/5 个文件。1 个任务和 1 个文件清理失败。",
  "cleanup_summary": {
    "tasks_terminated": 2,
    "tasks_failed": 1,
    "files_deleted": 4,
    "files_failed": 1
  },
  "cleaned_resources": {
    "tasks": ["T1", "T2"],
    "files": [".claude/plans/plan_1.md", ".claude/plans/plan_2.html"]
  },
  "errors": [
    {
      "type": "task_termination_failed",
      "resource": "T3",
      "error": "任务进程已不存在"
    },
    {
      "type": "file_deletion_failed",
      "resource": "/tmp/locked_file.txt",
      "error": "文件被占用"
    }
  ]
}
```

</output_format>

<reference>

## 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| status | string | completed（全部成功）、partially_completed（部分成功）、failed（全部失败） |
| report | string | 简短报告（不超过200字） |
| cleanup_summary | object | 清理统计摘要 |
| cleaned_resources | object | 已清理资源列表 |
| errors | array | 错误列表（可为空数组） |

cleanup_summary 包含 tasks_terminated、tasks_cancelled、tasks_failed、files_deleted、files_failed、empty_dirs_removed、total_space_freed 等字段。

## 清理顺序

清理按三个阶段进行：首先处理任务资源（停止运行中的任务、取消待执行的任务），然后清理文件资源（计划文件、临时文件、空目录），最后释放其他资源（内存、连接、缓存）。

## 常见错误类型

| 错误类型 | 说明 | 处理方式 |
|---------|------|---------|
| task_termination_failed | 任务终止失败 | 记录错误，继续清理其他资源 |
| file_deletion_failed | 文件删除失败 | 记录错误，尝试清理其他文件 |
| permission_denied | 权限不足 | 记录错误，跳过该资源 |
| resource_locked | 资源被占用 | 记录错误，稍后重试或跳过 |

## 详细文档

- [资源清理指南](finalizer-cleanup-guide.md) - 资源盘点、清理顺序、错误处理、防御性清理

## 注意事项

始终使用 `Agent(agent="task:finalizer", ...)` 调用，检查 status 字段确认清理结果，处理 errors 字段中的清理失败。即使部分失败也要完成剩余清理。不要因为一个错误就停止整个清理流程，不要假设清理操作一定成功。

</reference>
