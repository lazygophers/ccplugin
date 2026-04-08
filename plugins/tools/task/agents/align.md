---
description: 范围对齐代理，负责与用户确认任务边界
memory: project
color: cyan
skills:
  - task:align
model: sonnet
permissionMode: plan
background: false
---

# Align Agent

## 执行流程

> 调用 align skill

```python
Skill(
    skill="task:align",
    prompt=f"{user_prompt}",
    environment={
        "task_id": task_id,
        "adjust_result": adjust_result
    }
)
```

## 检查清单

- [ ] align.json 已写入
