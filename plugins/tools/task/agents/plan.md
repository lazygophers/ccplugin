---
description: 规划代理，负责分解任务并制定执行方案
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
plan_result = Skill(
    skill="task:plan",
    prompt=f"{user_prompt}",
    environment={
        "task_id": task_id,
        "adjust_result": adjust_result
    }
)

# 规划时发现上下文缺失，返回 explore
if plan_result.get("status") == "上下文缺失":
    goto EXPLORE
```

## 检查清单

- [ ] task.json 已写入
- [ ] status 已输出
