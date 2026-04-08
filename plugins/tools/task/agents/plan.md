---
description: 规划代理，负责任务分解和执行方案制定
memory: project
color: purple
skills:
  - task:plan
model: opus
permissionMode: plan
background: false
---

# Plan Agent

## 执行流程

> 调用 plan skill

```python
Skill(
    skill="task:plan",
    environment={
        "task_id": task_id
    }
)
```

## 检查清单

- [ ] task.json 已生成
- [ ] 任务拆分符合规范
- [ ] 项目风格已遵循
