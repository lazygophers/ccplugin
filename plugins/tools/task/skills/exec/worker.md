# Worker 协程逻辑

## 状态更新

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
```

## Worker 主循环

```python
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
```
