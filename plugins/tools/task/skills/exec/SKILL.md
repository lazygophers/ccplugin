---
description: 任务执行，基于DAG调度并执行子任务
memory: project
color: blue
model: sonnet
permissionMode: plan
background: false
context: fork
---

# Exec Skill

## 执行流程

> 基于 DAG 调度并执行子任务
> **2 个协程并发执行，自动解析依赖，触发 hooks**

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

```python
def update_task_status(session_task_id, subtask_id, status, result=None):
    """立即更新 task.json 中任务状态"""
    task_file = f".lazygophers/tasks/{session_task_id}/task.json"
    plan = read_json(task_file)

    # 更新对应任务的状态
    for task in plan["subtasks"]:
        if task["id"] == subtask_id:
            task["status"] = status
            if result:
                task["result"] = result
            break

    write_json(task_file, plan)

def spawn_worker(worker_id, queue, dag, status, executing, completed, failed, subtasks, code_style, task_id):
    while True:
        # 检查终止条件：队列空 + 无执行中 + 无可执行
        if len(queue) == 0 and len(executing) == 0:
            remaining_executable = False
            for tid in dag:
                if status[tid] == "pending" and all(status.get(dep) == "completed" for dep in dag[tid]["deps"]):
                    remaining_executable = True
                    break
            if not remaining_executable:
                break  # 终止

        # 等待任务
        if len(queue) == 0:
            sleep(0.1)
            continue

        # 获取任务
        tid = queue.pop(0)
        executing.add(tid)
        status[tid] = "running"
        update_task_status(task_id, tid, "running")

        # 执行任务（非后台执行）
        task = subtasks[tid]
        
        # 构建包含执行规则的 prompt
        execution_rules = """
## 执行规则（必须严格遵守）

1. **有理有据**：所有修改必须有明确的理由和依据，不能随意执行
2. **风格一致**：必须确保和现有代码风格一致，不可以创造新的风格
3. **保护现有功能**：不允许影响已有的功能，除非用户明确要求
4. **返回状态**：完成后必须返回 status (true/false)
   - 如果 status 为 false，必须返回详细的错误原因

---

"""
        prompt = execution_rules + task["goal"]
        
        result = Agent(
            description=f"执行子任务: {task['goal'][:20]}",
            subagent_type=task.get("agent", "general-purpose"),
            prompt=prompt,
            mode="acceptEdits",
            run_in_background=False  # 强制非后台
        )

        # 验证结果
        passed = verify_result(result, task.get("acceptance_criteria", []), code_style)

        # 更新状态
        executing.remove(tid)

        if passed:
            status[tid] = "completed"
            completed.add(tid)
            update_task_status(task_id, tid, "completed", result)

            # 触发 hooks
            hooks_file = f".lazygophers/tasks/{task_id}/hooks.json"
            if exists(hooks_file):
                hooks = read_json(hooks_file)
                for hook in hooks.get("task_completed", []):
                    execute_hook(hook, tid, result)

            # 解锁后继任务
            for successor in dag[tid]["successors"]:
                if (status[successor] == "pending" and
                    all(status.get(dep) == "completed" for dep in dag[successor]["deps"]) and
                    successor not in queue):
                    queue.append(successor)
        else:
            status[tid] = "failed"
            failed.add(tid)
            update_task_status(task_id, tid, "failed", result)

            # 触发 hooks
            hooks_file = f".lazygophers/tasks/{task_id}/hooks.json"
            if exists(hooks_file):
                hooks = read_json(hooks_file)
                for hook in hooks.get("task_failed", []):
                    execute_hook(hook, tid, result)
```

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
- [ ] Hooks 已触发

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
