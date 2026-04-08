---
description: 等待调度的任务代理，负责初始化任务上下文
memory: project
color: cyan
skills:
  - task:pending
model: sonnet
permissionMode: plan
background: false
---

# Pending Agent

## 执行流程

> 调用 pending skill

```python
Skill(
    skill="task:pending",
    prompt=f"{user_prompt}",
    environment={
        "task_id": task_id
    }
)
```

## 检查清单

- [ ] 初始上下文已准备
- [ ] 任务优先级已确定
- [ ] 任务元数据已记录
