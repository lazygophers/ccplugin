---
description: 完成代理，负责任务终结和资源清理
memory: project
color: green
skills:
  - task:done
model: haiku
permissionMode: plan
background: false
---

# Done Agent

## 执行流程

> 调用 done skill

```python
Skill(
    skill="task:done",
    prompt=f"{user_prompt}",
    environment={
        "task_id": task_id
    }
)
```

## 检查清单

- [ ] 临时文件已清理
- [ ] 任务索引已更新
- [ ] 执行报告已生成
