---
description: 取消代理，负责处理用户取消请求
memory: project
color: red
skills:
  - task:cancel
model: sonnet
permissionMode: plan
background: false
---

# Cancel Agent

## 执行流程

> 调用 cancel skill

```python
Skill(
    skill="task:cancel",
    prompt=f"{user_prompt}",
    environment={
        "task_id": task_id
    }
)

# cancel 完成后自动进入 done
goto DONE
```

## 检查清单

- [ ] status: "cancelled" 已输出
- [ ] 临时文件已清理
