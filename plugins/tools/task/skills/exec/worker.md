# Worker 协程逻辑

## 状态更新

```python
import fcntl

def update_task_status(session_task_id, subtask_id, status, result=None):
    """原子性更新 task.json 中任务状态（带文件锁，防止并发写覆盖）"""
    task_file = f".lazygophers/tasks/{session_task_id}/task.json"

    with open(task_file, "r+") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            content = f.read()
            plan = json.loads(content) if content else {}

            # 更新对应任务的状态
            for task in plan.get("subtasks", []):
                if task["id"] == subtask_id:
                    task["status"] = status
                    if result:
                        task["result"] = result
                    break

            f.seek(0)
            f.truncate()
            json.dump(plan, f, indent=2, ensure_ascii=False)
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```

## Worker 主循环

```python
def spawn_worker(worker_id, queue, dag, status, executing, completed, failed, subtasks, code_style, task_id, behavior_spec, toolchain):
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
        
        # 构建最小必要上下文（避免上下文中毒）
        # 只传入当前子任务需要的信息，不传入完整 plan
        task_context = {
            "goal": task["goal"],
            "files": task.get("files", []),
            "acceptance_criteria": task.get("acceptance_criteria", []),
            "code_style": {k: v for k, v in code_style.items() 
                          if k in ("naming", "indentation", "imports", "error_handling")}
        }

        # behavior_spec 和 toolchain 由 exec 预加载传入，无需重复读取

        # 构建包含执行规则 + 行为规约 + 自检要求的 prompt
        execution_rules = f"""
## 执行规则（必须严格遵守）

1. **有理有据**：所有修改必须有明确的理由和依据，不能随意执行
2. **风格一致**：必须确保和现有代码风格一致，不可以创造新的风格
3. **保护现有功能**：不允许影响已有的功能，除非用户明确要求
4. **返回状态**：完成后必须返回 status (true/false)
   - 如果 status 为 false，必须返回详细的错误原因

## 行为约束
{format_behavior_spec(behavior_spec)}

## 完成后自检（必须执行）

完成修改后，在返回 status 之前必须执行以下自检：
1. 重新读取你修改的文件，确认修改确实生效（防止幻觉）
2. 如果有测试命令（来自 toolchain），运行并确认通过
3. 确认只修改了 files 列表中的文件，未越界

## 自动测试反馈循环

每个子任务完成后，worker 自动执行轻量级质量检查：

```python
def auto_test_feedback(task_id, tid, task, toolchain):
    """子任务完成后自动运行测试/lint，结果写入 task.json"""
    feedback = {"tests": None, "lint": None}

    # 运行测试（如果 toolchain 中定义了命令）
    test_cmd = toolchain.get("test_command")
    if test_cmd:
        result = Bash(command=f"{test_cmd} 2>&1 | tail -5", timeout=60000)
        feedback["tests"] = {"passed": result.exit_code == 0, "output": result.stdout[-200:]}

    # 运行 lint（如果定义了）
    lint_cmd = toolchain.get("lint_command")
    if lint_cmd:
        result = Bash(command=f"{lint_cmd} 2>&1 | tail -5", timeout=30000)
        feedback["lint"] = {"passed": result.exit_code == 0, "output": result.stdout[-200:]}

    update_task_status(task_id, tid, status[tid], {"feedback": feedback})
    return feedback
```

> 测试/lint 失败不直接标记子任务 failed，而是作为 verify 阶段的前置证据。

---

"""
        prompt = execution_rules + task["goal"]
        
        # 心跳：记录开始时间，用于超时检测
        update_task_status(task_id, tid, "running", {"started_at": datetime.now().isoformat()})

        result = Agent(
            description=f"执行子任务: {task['goal'][:20]}",
            subagent_type=task.get("agent", "general-purpose"),
            prompt=prompt,
            mode="acceptEdits",
            run_in_background=False  # 强制非后台
        )

        # 即时验证：子任务完成后立即检查验收标准（轻量级，非 verify 阶段的全量校验）
        passed = verify_result(result, task.get("acceptance_criteria", []), code_style)

        # === 子任务级重试（最多 1 次）===
        if not passed:
            on_failure = task.get("on_failure", {})
            failure_type = classify_subtask_failure(result)
            recovery = on_failure.get(failure_type, "retry_with_fix" if failure_type == "test-failure" else None)
            
            if recovery == "retry_with_fix":
                # 注入失败原因后重试 1 次
                retry_prompt = f"""上次执行失败：{extract_failure_reason(result)}

请修正后重试。注意：
- 仔细阅读错误信息，定位根本原因
- 不要重复上次的错误做法

{execution_rules}{task['goal']}"""
                result = Agent(
                    description=f"重试子任务: {task['goal'][:20]}",
                    subagent_type=task.get("agent", "general-purpose"),
                    prompt=retry_prompt,
                    mode="acceptEdits",
                    run_in_background=False
                )
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

            # === 失败传播：标记所有下游依赖为 blocked ===
            def propagate_blocked(failed_tid):
                for successor in dag[failed_tid]["successors"]:
                    if status[successor] == "pending":
                        status[successor] = "blocked"
                        update_task_status(task_id, successor, "blocked")
                        propagate_blocked(successor)
            propagate_blocked(tid)
```
