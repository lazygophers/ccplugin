---
description: 任务终结，清理资源并归档结果
memory: project
color: green
model: haiku
permissionMode: plan
background: false
disable-model-invocation: true
user-invocable: false
context: fork
agent: task:done
---

# Done Skill

## 执行流程

> 任务终结处理和资源清理
> **确保所有清理工作完成，生成执行报告**

```python
# 读取任务元数据
metadata_file = f".lazygophers/tasks/{task_id}/metadata.json"
metadata = read_json(metadata_file)

# 读取对齐结果（获取项目风格）
align_file = f".lazygophers/tasks/{task_id}/align.json"
align = read_json(align_file) if exists(align_file) else {}

# 获取项目风格（用于归档）
code_style = align.get("code_style_follow", {})

# 阶段1：汇总执行结果
results = collect_results({
    "task_id": task_id,
    "metadata": metadata,
    "context": read_json(f".lazygophers/tasks/{task_id}/context.json"),
    "align": align,
    "plan": read_json(f".lazygophers/tasks/{task_id}/task.json") if exists(f".lazygophers/tasks/{task_id}/task.json") else None
})

# 阶段2：生成执行报告
report = generate_completion_report({
    "results": results,
    "code_style": code_style,
    "cleanup": cleanup_success,
    "archive": archive_success
})
```

## 检查清单

### 结果汇总
- [ ] 执行结果已汇总
- [ ] 项目风格已记录（用于归档）
- [ ] 任务元数据已读取

### 资源清理
- [ ] 临时文件已清理
- [ ] 检查点已清理
- [ ] 清理结果已验证

### 文档归档
- [ ] 任务文档已归档
- [ ] 遵循的风格已记录

### 索引更新
- [ ] 任务索引已更新
- [ ] 状态已标记为 done
- [ ] 完成时间已记录

### 报告生成
- [ ] 执行报告已生成
- [ ] 包含：结果、风格、清理状态
- [ ] 用户已通知

### 最终清理（完成所有工作后）
- [ ] 所有清理工作已完成
- [ ] 最终检查已通过
- [ ] 任务目录已删除
- [ ] 检查点已清理

### 验证循环
- [ ] 清理未完成时自动重试
- [ ] 归档未完成时自动重试
- [ ] 索引未完成时自动重试
- [ ] 所有项目完成后才退出
