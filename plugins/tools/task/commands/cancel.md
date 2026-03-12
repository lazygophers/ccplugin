---
description: 取消当前任务 - 终止正在执行的 Loop 流程，保留已完成的工作
model: sonnet
memory: project
---

# 取消当前任务

立即终止当前正在执行的 Loop 流程。

## 取消流程

### 1. 停止执行

使用工具：TaskStop

- 终止所有正在运行的 Agent
- 中断当前迭代循环
- 不再调度新的子任务

### 2. 状态保存

使用工具：TaskUpdate

取消不等于丢弃，保留已完成的工作：
```
# 已完成的任务保持状态
TaskUpdate(task_id, status="completed")

# 执行中的任务标记为已取消
TaskUpdate(task_id, status="cancelled", metadata={
  "cancelled_at": timestamp,
  "cancelled_reason": "用户主动中断"
})

# 待执行的任务保持 pending
```

### 3. 清理团队

使用工具：TeamDelete

```
TeamDelete(team_id)
```

### 4. 输出取消报告

```
[取消] 任务已终止

已完成：T1, T2
已取消：T3（执行中被终止）
未开始：T4, T5

可通过 /loop 重新开始
```

## 恢复选项

取消后用户可以：
- `/loop` — 用新的目标重新开始

## 安全保证

- 取消操作是安全的，不会丢弃已完成的工作
- 已提交的代码变更不会被回退
- 任务状态保留在 TaskList 中

## 适用场景

- 用户主动中断（Ctrl+C 或明确取消指令）
- 发现任务规划错误，需要重新规划
- 遇到无法解决的阻塞，需要用户介入

## 不适用场景

- 任务即将完成（建议等待完成）
- 只需要调整部分内容（使用 `/add` 补充说明）
- 需要修复失败任务（让 Loop 自动迭代修复）
