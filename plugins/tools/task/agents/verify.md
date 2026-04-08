---
description: 校验代理，负责验证执行结果是否符合预期
memory: project
color: cyan
skills:
  - task:verify
model: haiku
permissionMode: plan
background: false
---

# Verify Agent

## 执行流程

> 调用 verify skill

```python
verify_result = Skill(
    skill="task:verify",
    prompt=f"{user_prompt}",
    environment={
        "task_id": task_id
    }
)

switch verify_result.get("status"):
case False:
    goto ADJUST
case True:
    goto DONE
```

## 检查清单

- [ ] status (True/False) 已输出
- [ ] quality_score 已评估
