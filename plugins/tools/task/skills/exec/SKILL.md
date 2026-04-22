---
description: DAG 任务执行引擎。plan 完成后触发，2 个 worker 协程并发调度子任务，按依赖拓扑排序执行，支持部分完成恢复
memory: project
color: blue
model: sonnet
permissionMode: bypassPermissions
background: false
user-invocable: false
effort: medium
context: fork
---

# Exec Skill

基于 DAG 调度并执行子任务。**2 个协程并发执行，自动解析依赖。**

## 执行流程

### 步骤 1：加载数据（一次性预加载）

读取以下文件，后续所有 worker 共享，不再重复读取：

- `.lazygophers/tasks/{task_id}/task.json` — 子任务列表、code_style
- `.lazygophers/tasks/{task_id}/align.json` — behavior_spec（行为规约）
- `.lazygophers/tasks/{task_id}/context.json` — toolchain（测试/lint 命令）

### 步骤 2：构建 DAG

遍历所有子任务，根据 `dependencies` 字段构建有向无环图：
- 为每个子任务记录其依赖列表和后继列表
- 验证无循环依赖，发现循环则立即报错终止

### 步骤 3：初始化执行队列

支持部分完成恢复：
- 已完成（status=completed）的子任务跳过
- 已失败（status=failed）的子任务跳过
- 所有依赖已完成的待执行子任务加入队列

### 步骤 4：启动 2 个 worker 协程

每个 worker 从共享队列中取任务执行，Worker 的详细逻辑见 [worker.md](worker.md)。

核心循环：取任务 → 标记 running → 构建 prompt → 调用 Agent → 验证结果 → 更新状态 → 解锁后继。

### 步骤 5：等待所有协程完成

两个 worker 都退出后（队列空 + 无执行中 + 无可执行），写入执行检查点到 task.json：

```json
{
  "checkpoint": {
    "state": "exec",
    "completed_subtasks": ["A", "B"],
    "failed_subtasks": ["C"],
    "pending_subtasks": [],
    "last_update": "ISO8601"
  }
}
```

### 步骤 6：汇总结果

输出 `[flow·{task_id}·exec] 任务执行完成：N/M 成功`。

## 检查清单

- [ ] DAG 已构建，无循环依赖
- [ ] 初始可执行任务已入队（跳过已完成/已失败）
- [ ] 2 个协程已启动，background 强制为 False
- [ ] 状态已更新（pending/running/completed/failed/blocked）
- [ ] task.json 已实时更新
- [ ] 心跳时间戳已记录（started_at）
- [ ] 即时验证已在子任务完成后执行
- [ ] 失败传播已实现（failed → 下游 blocked）
- [ ] 后继任务解锁已实现，无重复推送
