# 检查点集成与示例

本文档补充 SKILL.md，提供检查点机制与 Loop 的集成方式和使用示例。

---

## 与 Loop 的集成

检查点机制无缝集成到 detailed-flow.md 的各个阶段：

### 初始化阶段
```python
print("[MindFlow] 开始初始化任务管理循环...")

# 尝试加载检查点
checkpoint = load_checkpoint(user_task)

if checkpoint:
    # 恢复状态
    iteration = checkpoint["iteration"]
    context = checkpoint["context"]
    plan_md_path = checkpoint.get("plan_md_path")

    print(f"[MindFlow] 从迭代 {iteration} 的 {checkpoint['phase']} 阶段恢复")

    # 跳转到对应阶段
    goto(checkpoint["phase"])
else:
    # 正常初始化
    iteration = 0
    context = {"replan_trigger": None}

    print(f"[MindFlow·{user_task}·初始化/0·进行中]")
```

### 计划设计完成后
```python
print(f"[MindFlow·{user_task}·计划设计/{iteration}·completed]")

# 保存检查点
save_checkpoint(
    user_task=user_task,
    iteration=iteration,
    phase="planning",
    context=context,
    plan_md_path=plan_md_path
)
```

### 计划确认后
```python
if user_decision == "立即执行":
    print(f"[MindFlow] 用户批准计划，准备执行")

    # 保存检查点
    save_checkpoint(
        user_task=user_task,
        iteration=iteration,
        phase="confirmation",
        context=context,
        plan_md_path=plan_md_path
    )

    goto("任务执行")
```

### 任务执行完成后
```python
print(f"[MindFlow·{user_task}·任务执行/{iteration}·completed]")

# 保存检查点
save_checkpoint(
    user_task=user_task,
    iteration=iteration,
    phase="execution",
    context=context,
    plan_md_path=plan_md_path
)
```

### 全部完成阶段
```python
print(f"[MindFlow·{user_task}·completed]")

# 清理检查点
cleanup_checkpoint(user_task)
```

---

## 使用示例

### 场景1：正常执行（无中断）
```
[MindFlow] 开始初始化任务管理循环...
[MindFlow] 未找到检查点，从头开始执行
[MindFlow·实现登录功能·初始化/0·进行中]
...
[MindFlow·实现登录功能·计划设计/1·completed]
[MindFlow] ✓ 检查点已保存: .claude/checkpoints/a1b2c3d4e5f6.json
...
[MindFlow·实现登录功能·completed]
[MindFlow] ✓ 检查点已清理
```

### 场景2：中断后恢复
```
[MindFlow] 开始初始化任务管理循环...
[MindFlow] ✓ 检测到检查点:
[MindFlow]   迭代: 2
[MindFlow]   阶段: execution
[MindFlow]   时间: 2026-03-21T14:30:00
? 检测到上次中断的任务（迭代 2，阶段 execution），是否恢复？
  > 恢复执行
[MindFlow] ✓ 从检查点恢复执行
[MindFlow] 从迭代 2 的 execution 阶段恢复
[MindFlow·实现登录功能·任务执行/2·进行中]
...
```

### 场景3：用户选择重新开始
```
[MindFlow] 开始初始化任务管理循环...
[MindFlow] ✓ 检测到检查点:
[MindFlow]   迭代: 1
[MindFlow]   阶段: planning
[MindFlow]   时间: 2026-03-20T18:00:00
? 检测到上次中断的任务（迭代 1，阶段 planning），是否恢复？
  > 重新开始
[MindFlow] 用户选择重新开始，忽略检查点
[MindFlow] ✓ 检查点已清理
[MindFlow·实现登录功能·初始化/0·进行中]
...
```
