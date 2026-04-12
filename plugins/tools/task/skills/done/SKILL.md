---
description: 任务终结，总结输出并整理记忆
memory: project
color: green
model: haiku
permissionMode: bypassPermissions
background: false
context: fork
agent: task:done
---

# Done Skill

## 执行流程

> 任务终结，总结执行结果并整理记忆

```python
# 读取任务元数据（从索引文件获取）
index_file = ".lazygophers/tasks/index.json"
index = read_json(index_file)
metadata = index.get(task_id, {})

# 读取对齐结果（获取项目风格）
align_file = f".lazygophers/tasks/{task_id}/align.json"
align = read_json(align_file) if exists(align_file) else {}

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
    "code_style": align.get("code_style_follow", {})
})

# 阶段3：整理记忆
save_lessons_learned({
    "task_id": task_id,
    "results": results,
    "report": report
})

# 输出格式：所有输出必须包含前缀 [flow·{task_id}·{state}]
print(f"[flow·{task_id}·done] 任务已完成")

return report
```

## 检查清单

### 结果汇总
- [ ] 执行结果已汇总
- [ ] 任务元数据已从 index.json 读取

### 报告生成
- [ ] 执行报告已生成
- [ ] 用户已通知

### 记忆整理
- [ ] 经验教训已保存
- [ ] 项目记忆已更新

## 输出格式

所有输出必须包含前缀：`[flow·{task_id}·{state}]`

- task_id：当前任务ID
- state：当前状态（done）
