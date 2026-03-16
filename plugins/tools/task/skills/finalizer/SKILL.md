---
agent: task:finalizer
description: 资源清理规范 - 系统性资源清理、任务终止、最终报告生成的执行规范
model: haiku
context: fork
user-invocable: false
---

# Skills(task:finalizer) - 资源清理规范

## 适用场景

当你需要清理迭代完成后的资源时，使用此 skill：

- ✓ Loop 命令执行完成后的资源清理
- ✓ 紧急停止时的资源释放
- ✓ 迭代周期完成后的收尾工作
- ✓ 任务终止和文件清理
- ✓ 生成最终清理报告

## 核心原则

### 资源清理最佳实践

- **明确所有权**：识别每个资源的"所有者"（哪个组件负责创建）
- **错误处理**：即使操作失败，也要释放部分资源
- **清理顺序**：按依赖关系逆序清理（先创建的后清理）
- **防御性清理**：使用 try-except 包裹清理逻辑

## 执行流程

### 调用 finalizer agent

```python
# 基础调用
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

### 处理 finalizer 结果

```python
# 检查状态
if finalizer_result["status"] not in ["completed", "partially_completed"]:
    raise Exception("清理失败")

# 输出清理报告
print(f"✓ 清理完成：{finalizer_result['report']}")
print(f"清理任务数：{finalizer_result['cleanup_summary']['tasks_terminated']}")
print(f"清理文件数：{finalizer_result['cleanup_summary']['files_deleted']}")

# 检查是否有部分失败
if finalizer_result.get("errors"):
    print(f"⚠ 部分清理失败：{len(finalizer_result['errors'])} 个错误")
    for error in finalizer_result["errors"]:
        print(f"  - {error}")
```

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
    "directories": [
      ".claude/plans/empty_dir"
    ]
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

## 字段说明

| 字段 | 类型 | 说明 | 必填 |
|------|------|------|------|
| `status` | string | 执行状态：`completed`（全部成功）、`partially_completed`（部分成功）、`failed`（全部失败） | ✓ |
| `report` | string | 简短报告（≤200字） | ✓ |
| `cleanup_summary` | object | 清理统计摘要 | ✓ |
| `cleaned_resources` | object | 已清理资源列表 | ✓ |
| `errors` | array | 错误列表（可为空数组） | ✓ |

### cleanup_summary 字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `tasks_terminated` | number | 成功终止的任务数 |
| `tasks_cancelled` | number | 成功取消的任务数 |
| `tasks_failed` | number | 清理失败的任务数 |
| `files_deleted` | number | 成功删除的文件数 |
| `files_failed` | number | 删除失败的文件数 |
| `empty_dirs_removed` | number | 清理的空目录数 |
| `total_space_freed` | string | 释放的磁盘空间 |

## 详细文档

完整的清理策略、错误处理和集成示例详见以下文档：

- **[资源清理指南](finalizer-cleanup-guide.md)** - 资源盘点、清理顺序、错误处理、防御性清理
- **[输出格式参考](finalizer-output-formats.md)** - 所有输出格式、错误类型、状态转换

## 快速参考

### 清理顺序

1. **任务资源**：停止运行中的任务 → 取消待执行的任务
2. **文件资源**：清理计划文件 → 清理临时文件 → 清理空目录
3. **其他资源**：释放内存、关闭连接、清理缓存

### 常见错误类型

| 错误类型 | 说明 | 处理方式 |
|---------|------|---------|
| `task_termination_failed` | 任务终止失败 | 记录错误，继续清理其他资源 |
| `file_deletion_failed` | 文件删除失败 | 记录错误，尝试清理其他文件 |
| `permission_denied` | 权限不足 | 记录错误，跳过该资源 |
| `resource_locked` | 资源被占用 | 记录错误，稍后重试或跳过 |

### 最佳实践

- 使用 try-except 包裹每个清理操作
- 即使部分清理失败，也继续剩余清理
- 记录所有清理操作和错误
- 按依赖关系逆序清理
- 确保清理过程的原子性

## 注意事项

- ✓ 始终使用 `Agent(agent="task:finalizer", ...)` 调用
- ✓ 检查 `status` 字段确认清理结果
- ✓ 处理 `errors` 字段中的清理失败
- ✓ 记录清理统计用于监控和调试
- ✓ 即使部分失败也要完成剩余清理
- ✗ 不要因为一个错误就停止整个清理流程
- ✗ 不要忽略清理过程中的错误
- ✗ 不要假设清理操作一定成功
