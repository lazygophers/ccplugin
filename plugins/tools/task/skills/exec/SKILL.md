---
description: 任务执行，基于DAG调度并执行子任务
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

## 执行流程

> 基于 DAG 调度并执行子任务
> **2 个协程并发执行，自动解析依赖**

```python
# 读取执行计划
plan = read_json(f".lazygophers/tasks/{task_id}/task.json")
subtasks = {t["id"]: t for t in plan["subtasks"]}
code_style = plan.get("code_style", {})

# === 阶段1：构建 DAG ===
dag = {}
for tid in subtasks:
    dag[tid] = {"deps": [], "successors": []}

for tid, task in subtasks.items():
    deps = task.get("dependencies", [])
    dag[tid]["deps"] = deps
    for dep in deps:
        if dep in dag:
            dag[dep]["successors"].append(tid)

# 验证无循环依赖
if has_cycle(dag):
    raise ValueError("DAG 包含循环依赖")

# === 阶段2：初始化状态和队列 ===
status = {tid: "pending" for tid in subtasks}
queue = []
executing = set()
completed = set()
failed = set()

# 推送初始可执行任务（无依赖）
for tid in subtasks:
    if all(status.get(dep) == "completed" for dep in dag[tid]["deps"]):
        queue.append(tid)

# === 阶段3：启动 2 个 worker 协程 ===
workers = []
for i in range(2):
    workers.append(spawn_worker(f"worker-{i}", queue, dag, status, executing, completed, failed, subtasks, code_style, task_id))

# === 阶段4：等待所有协程完成 ===
wait_all(workers)

# === 阶段5：汇总结果 ===
results = {
    "total": len(status),
    "completed": len(completed),
    "failed": len(failed),
    "status": status,
    "failed_tasks": list(failed)
}

# 输出格式：所有输出必须包含前缀 [flow·{task_id}·{state}]
print(f"[flow·{task_id}·exec] 任务执行完成：{results['completed']}/{results['total']} 成功")

return results
```

## Worker 协程逻辑

Worker 的状态更新、主循环、执行规则注入和依赖解锁的完整实现见 [worker.md](worker.md)。

核心流程：从队列取任务 → 更新状态为 running → 构建 prompt（注入执行规则）→ 调用 Agent 执行 → 验证结果 → 更新状态 → 解锁后继任务。

## 检查清单

### DAG 构建
- [ ] DAG 已构建
- [ ] 依赖关系已验证
- [ ] 无循环依赖

### 队列管理
- [ ] 初始可执行任务已入队
- [ ] 任务去重机制已实现
- [ ] 队列空检查已实现

### 协程管理
- [ ] 2 个协程已启动
- [ ] 终止条件已实现
- [ ] 协程清理已实现

### 任务执行
- [ ] background 强制为 False
- [ ] 状态已更新（pending/running/completed/failed）
- [ ] task.json 已实时更新

### 依赖解析
- [ ] 可执行性检查已实现
- [ ] 后继任务已入队
- [ ] 无重复推送

### 输出
- [ ] 执行结果已汇总
- [ ] 任务状态已更新
- [ ] 失败任务已记录

## 输出格式

所有输出必须包含前缀：`[flow·{task_id}·{state}]`

- task_id：当前任务ID
- state：当前状态（exec）
