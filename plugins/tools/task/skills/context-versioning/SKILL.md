---
description: 上下文版本化 - 保存快照/列表版本/回滚/对比，支持规划前自动保存和失败回滚
model: sonnet
context: fork
user-invocable: false
---

# Skills(task:context-versioning) - 上下文版本化

<overview>

上下文版本化为 MindFlow Loop 提供上下文状态管理能力，在每次规划前自动保存上下文快照，支持失败后回滚到已知良好状态。核心目标是防止上下文污染导致的迭代失败。

**核心能力**:
- **保存快照**: 规划前自动保存当前上下文状态到版本化存储
- **列表版本**: 查看所有历史上下文快照及其元数据
- **回滚版本**: 失败后恢复到指定的上下文快照
- **对比版本**: 对比两个快照的差异，辅助问题诊断

**使用场景**:
- 规划迭代前保存上下文快照（自动触发）
- 验证失败时回滚到上次成功的上下文（adjuster 触发）
- 分析上下文污染问题（对比成功/失败快照）
- 调试迭代失败原因（查看上下文演变历史）

**文档导航**:
- **API 完整参考** → [api-reference.md](./api-reference.md)
- **集成示例** → [integration-examples.md](./integration-examples.md)

</overview>

<quick_reference>

## 核心 API 概览

完整 API 参见 [api-reference.md](./api-reference.md)

### 1. save_context_snapshot()

**功能**: 规划前自动保存上下文快照

**调用时机**: 每次进入 planner 阶段前、任务执行成功后、用户手动触发

**存储位置**: `.claude/context-versions/{task_hash}/v{iteration}.json`

**返回**: 快照版本ID（如 "v1", "v2"）

### 2. list_context_versions()

**功能**: 列出所有历史上下文快照

**调用时机**: 用户查询历史快照、选择回滚目标、调试上下文问题

**返回**: 快照列表（version_id, iteration, phase, status, timestamp）

### 3. rollback_context()

**功能**: 回滚到指定的上下文快照

**调用时机**: 验证失败时、用户手动请求、上下文污染严重时

**返回**: 快照的完整数据或 None

### 4. compare_context_snapshots()

**功能**: 对比两个上下文快照的差异

**调用时机**: 分析迭代失败原因、诊断上下文污染、调试 replan_trigger 变化

**返回**: 差异详情（added_keys, removed_keys, changed_values）

</quick_reference>

<integration>

## 集成示例

完整示例参见 [integration-examples.md](./integration-examples.md)

### 规划前自动保存

```python
version_id = save_context_snapshot(
    user_task=user_task,
    iteration=iteration,
    phase="pre-planning",
    context_state=context,
    status="pending"
)
```

### 验证失败时回滚

```python
if context.get("replan_trigger") == "verification_failed":
    snapshots = list_context_versions(user_task, status_filter="success")
    if snapshots:
        restored_snapshot = rollback_context(user_task, target_version=snapshots[0]['version_id'])
        if restored_snapshot:
            context = restored_snapshot["context_state"]
            iteration = restored_snapshot["iteration"]
```

</integration>

<notes>

## 注意事项

1. **快照存储**: `.claude/context-versions/{task_hash}/v{iteration}.json`
2. **任务哈希**: MD5(user_task)[:12]
3. **快照状态**: pending（待执行）、success（成功）、failed（失败）
4. **自动保存**: 每次进入 planner 前
5. **回滚策略**: 默认回滚到最近的 success 快照
6. **清理策略**: 任务完成后可选择保留或清理（建议保留用于审计）
7. **并发安全**: 每次迭代一个快照文件，按迭代号递增
8. **状态一致性**: 快照必须包含完整的 context_state
9. **与 checkpoint 的区别**:
   - checkpoint 用于中断恢复（进程级）
   - context-versioning 用于上下文回滚（逻辑级）

</notes>
