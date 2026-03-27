# Finalizer 资源清理指南

## 最佳实践

| 原则 | 说明 |
|------|------|
| 明确所有权 | 创建者负责释放，最小化共享所有权 |
| 错误处理 | 失败也释放部分资源，不阻止整体清理 |
| 清理顺序 | 按依赖逆序：先停任务后删文件 |
| 防御性 | try-except包裹，记录异常，继续剩余清理 |

语言模式：Python=`with` | Java/C#=`try-with-resources`/`using` | C++=RAII

## 执行流程

### 阶段1：资源盘点

- **任务**：`TaskList()` → 分类running/pending/completed/failed
- **文件**：计划文件(`~/.claude/plans/*.md`) + 临时文件(`/tmp/claude_task_*`)
- **其他**：lock_files + cache_files + log_files

### 阶段2：任务终止

- 停止running任务：`TaskStop(task.id)` → 记录stopped/failed_to_stop
- 取消pending任务：`TaskStop(task.id)` → 标记cancelled

### 阶段3：文件清理

- 删除计划文件 → 删除临时文件 → 清理空目录
- 每步try-except，记录失败但继续

### 阶段4：最终报告

`{tasks_stopped, tasks_failed_to_stop, files_deleted, files_failed_to_delete, total_duration_seconds}` → 简洁报告≤100字

## 检查清单

- 所有running/pending任务已处理
- 计划文件/临时文件已删除，空目录已清理
- 所有清理操作有错误处理且已记录
- 报告简洁准确
