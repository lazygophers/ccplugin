# Context Versioning Integration Examples

本文档包含上下文版本化与 Loop 集成的示例和使用场景。

---

## 与 Planner 的集成

上下文版本化无缝集成到 planner-context-learning.md 的规划流程：

### 规划前自动保存快照

在 planner 开始收集上下文信息前，自动保存当前上下文快照：

```python
# planner-context-learning.md - 信息收集阶段开始前

print(f"[MindFlow·{user_task}·信息收集/{iteration}·进行中]")

# 保存规划前上下文快照
version_id = save_context_snapshot(
    user_task=user_task,
    iteration=iteration,
    phase="pre-planning",
    context_state=context,
    status="pending",
    metadata={
        "trigger": context.get("replan_trigger"),
        "note": "规划前自动保存"
    }
)

print(f"[MindFlow] 当前上下文快照: {version_id}")

# 继续信息收集流程...
```

### 执行成功后标记快照

在任务执行成功后，将对应快照标记为 success：

```python
# planner-context-learning.md - 任务执行成功后

print(f"[MindFlow·{user_task}·任务执行/{iteration}·completed]")

# 更新快照状态为成功
task_hash = hashlib.md5(user_task.encode('utf-8')).hexdigest()[:12]
snapshot_path = Path(f".claude/context-versions/{task_hash}/v{iteration}.json")

if snapshot_path.exists():
    with open(snapshot_path, 'r') as f:
        snapshot = json.load(f)

    snapshot["status"] = "success"
    snapshot["metadata"]["completed_at"] = datetime.now().isoformat()

    with open(snapshot_path, 'w') as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)

    print(f"[MindFlow] ✓ 快照 v{iteration} 标记为成功")
```

### 验证失败时回滚上下文

在 adjuster 检测到验证失败时，支持回滚到上次成功的上下文：

```python
# planner-context-learning.md - 失败调整阶段

if context.get("replan_trigger") == "verification_failed":
    print(f"[MindFlow] 检测到验证失败，评估是否需要回滚上下文...")

    # 查询上下文快照历史
    snapshots = list_context_versions(user_task, status_filter="success")

    if snapshots and len(snapshots) > 0:
        # 建议回滚到最近的成功快照
        print(f"[MindFlow] 找到 {len(snapshots)} 个成功快照，最近: {snapshots[0]['version_id']}")

        user_decision = AskUserQuestion(
            question=f"验证失败，是否回滚到上次成功的上下文快照 {snapshots[0]['version_id']}？",
            options=["回滚上下文", "保持当前上下文", "查看快照对比"]
        )

        if user_decision == "查看快照对比":
            # 对比当前失败快照与最近成功快照
            current_version = f"v{iteration}"
            target_version = snapshots[0]['version_id']
            compare_context_snapshots(user_task, target_version, current_version)

            # 再次询问是否回滚
            user_decision = AskUserQuestion(
                question="查看对比后，是否回滚上下文？",
                options=["回滚上下文", "保持当前上下文"]
            )

        if user_decision == "回滚上下文":
            # 执行回滚
            restored_snapshot = rollback_context(user_task, target_version=snapshots[0]['version_id'])

            if restored_snapshot:
                # 恢复上下文状态
                context = restored_snapshot["context_state"]

                # 重置迭代号到快照迭代
                iteration = restored_snapshot["iteration"]

                print(f"[MindFlow] ✓ 上下文已回滚，从迭代 {iteration} 重新开始")
                goto("计划设计")
    else:
        print(f"[MindFlow] ⚠️ 未找到成功的上下文快照，无法回滚")
```

---

## 使用示例

### 场景1：正常迭代（自动保存快照）

```
[MindFlow·实现登录功能·信息收集/1·进行中]
[MindFlow] ✓ 上下文快照已保存: v1
[MindFlow] 当前上下文快照: v1
...
[MindFlow·实现登录功能·任务执行/1·completed]
[MindFlow] ✓ 快照 v1 标记为成功
...
[MindFlow·实现登录功能·信息收集/2·进行中]
[MindFlow] ✓ 上下文快照已保存: v2
[MindFlow] 当前上下文快照: v2
```

### 场景2：验证失败回滚

```
[MindFlow·实现登录功能·结果验证/3·failed]
[MindFlow] 检测到验证失败，评估是否需要回滚上下文...
[MindFlow] 找到 2 个成功快照:
[MindFlow]   ✓ v2 - execution (2026-03-21T14:30:00)
[MindFlow]   ✓ v1 - execution (2026-03-21T14:00:00)
[MindFlow] 找到 2 个成功快照，最近: v2
? 验证失败，是否回滚到上次成功的上下文快照 v2？
  > 查看快照对比
[MindFlow] 上下文快照对比 (v2 → v3):
[MindFlow]   变化键: replan_trigger, error_count
[MindFlow]     replan_trigger: None → verification_failed
[MindFlow]     error_count: 0 → 3
? 查看对比后，是否回滚上下文？
  > 回滚上下文
[MindFlow] ✓ 回滚到快照 v2:
[MindFlow]   迭代: 2
[MindFlow]   阶段: execution
[MindFlow]   状态: success
[MindFlow] ✓ 上下文已回滚，从迭代 2 重新开始
```

### 场景3：查询版本历史

```
[MindFlow] 找到 5 个上下文快照:
[MindFlow]   ✓ v5 - execution (2026-03-21T15:30:00)
[MindFlow]   ✗ v4 - verification (2026-03-21T15:15:00)
[MindFlow]   ✓ v3 - execution (2026-03-21T15:00:00)
[MindFlow]   ✓ v2 - execution (2026-03-21T14:30:00)
[MindFlow]   ✓ v1 - execution (2026-03-21T14:00:00)
```
