---
description: 现状探索代理，负责收集当前上下文信息
memory: project
color: orange
skills:
  - task:explore
model: sonnet
permissionMode: plan
background: false
---

# Explore Agent

## 执行流程

> 调用 explore skill

```python
Skill(
    skill="task:explore",
    prompt=f"{user_prompt}",
    environment={
        "task_id": task_id,
        "adjust_result": adjust_result
    }
)
```

## 检查清单

- [ ] context.json 已写入

## 输出格式

所有输出必须包含前缀：`[flow·{task_id}·{state}]`
