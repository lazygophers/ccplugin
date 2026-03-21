---
description: 上下文版本化 - 保存快照/列表版本/回滚/对比，支持规划前自动保存和失败回滚
model: sonnet
context: fork
user-invocable: false
---

# Skills(task:context-versioning) - 上下文版本化

<overview>

上下文版本化为 MindFlow Loop 提供上下文状态管理能力，在每次规划前自动保存上下文快照，支持失败后回滚到已知良好状态。核心目标是防止上下文污染导致的迭代失败。

核心能力：
- **保存快照**：规划前自动保存当前上下文状态到版本化存储
- **列表版本**：查看所有历史上下文快照及其元数据
- **回滚版本**：失败后恢复到指定的上下文快照
- **对比版本**：对比两个快照的差异，辅助问题诊断

使用场景：
- 规划迭代前保存上下文快照（自动触发）
- 验证失败时回滚到上次成功的上下文（adjuster 触发）
- 分析上下文污染问题（对比成功/失败快照）
- 调试迭代失败原因（查看上下文演变历史）

</overview>

<api>

## 核心 API

### 1. save_context_snapshot()

在规划前自动保存上下文快照。

**调用时机**：
- 每次进入 planner 阶段前（第一次和重新规划前）
- 任务执行成功后（标记为 success）
- 用户手动触发保存时

**参数**：
```python
def save_context_snapshot(
    user_task: str,           # 用户任务描述
    iteration: int,           # 当前迭代号
    phase: str,               # 当前阶段（planning/execution/verification等）
    context_state: dict,      # 上下文状态（replan_trigger、errors等）
    status: str = "pending",  # 快照状态（pending/success/failed）
    metadata: dict = None     # 额外元数据（可选）
) -> str:
    """
    保存上下文快照到 .claude/context-versions/{task_hash}/v{iteration}.json

    返回：
    - str: 快照版本ID（如 "v1", "v2"）
    """
```

**实现逻辑**：
```python
import hashlib
import json
from pathlib import Path
from datetime import datetime

def save_context_snapshot(user_task, iteration, phase, context_state, status="pending", metadata=None):
    # 生成任务哈希作为目录名
    task_hash = hashlib.md5(user_task.encode('utf-8')).hexdigest()[:12]

    versions_dir = Path(".claude/context-versions") / task_hash
    versions_dir.mkdir(parents=True, exist_ok=True)

    # 构建快照数据
    snapshot_data = {
        "version_id": f"v{iteration}",
        "user_task": user_task,
        "task_hash": task_hash,
        "iteration": iteration,
        "phase": phase,
        "context_state": context_state,
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "metadata": metadata or {}
    }

    # 写入版本化文件
    snapshot_path = versions_dir / f"v{iteration}.json"
    try:
        with open(snapshot_path, 'w', encoding='utf-8') as f:
            json.dump(snapshot_data, f, ensure_ascii=False, indent=2)
        print(f"[MindFlow] ✓ 上下文快照已保存: {snapshot_data['version_id']}")
        return snapshot_data['version_id']
    except Exception as e:
        print(f"[MindFlow] ⚠️ 快照保存失败: {e}")
        return None
```

### 2. list_context_versions()

列出所有历史上下文快照。

**调用时机**：
- 用户查询历史快照时
- 需要选择回滚目标版本时
- 调试上下文演变问题时

**参数**：
```python
def list_context_versions(
    user_task: str,           # 用户任务描述
    status_filter: str = None # 状态过滤（success/failed/pending，可选）
) -> list[dict]:
    """
    列出所有上下文快照及其元数据

    返回：
    - list[dict]: 快照列表，按迭代号倒序排列
      每个快照包含: version_id, iteration, phase, status, timestamp
    """
```

**实现逻辑**：
```python
def list_context_versions(user_task, status_filter=None):
    task_hash = hashlib.md5(user_task.encode('utf-8')).hexdigest()[:12]
    versions_dir = Path(".claude/context-versions") / task_hash

    if not versions_dir.exists():
        print(f"[MindFlow] 未找到上下文版本历史")
        return []

    # 读取所有快照文件
    snapshots = []
    for snapshot_file in sorted(versions_dir.glob("v*.json"), reverse=True):
        try:
            with open(snapshot_file, 'r', encoding='utf-8') as f:
                snapshot = json.load(f)

            # 状态过滤
            if status_filter and snapshot.get("status") != status_filter:
                continue

            snapshots.append({
                "version_id": snapshot["version_id"],
                "iteration": snapshot["iteration"],
                "phase": snapshot["phase"],
                "status": snapshot.get("status", "unknown"),
                "timestamp": snapshot["timestamp"]
            })
        except Exception as e:
            print(f"[MindFlow] ⚠️ 读取快照失败: {snapshot_file.name} - {e}")
            continue

    # 输出列表
    if snapshots:
        print(f"[MindFlow] 找到 {len(snapshots)} 个上下文快照:")
        for snap in snapshots:
            status_icon = {"success": "✓", "failed": "✗", "pending": "○"}.get(snap["status"], "?")
            print(f"[MindFlow]   {status_icon} {snap['version_id']} - {snap['phase']} ({snap['timestamp']})")
    else:
        print(f"[MindFlow] 未找到匹配的上下文快照")

    return snapshots
```

### 3. rollback_context()

回滚到指定的上下文快照。

**调用时机**：
- 验证失败时，由 adjuster 触发回滚到上次成功快照
- 用户手动请求回滚时
- 上下文污染严重需要重置时

**参数**：
```python
def rollback_context(
    user_task: str,           # 用户任务描述
    target_version: str = None # 目标版本ID（如 "v2"，None=最近的success）
) -> dict | None:
    """
    回滚到指定的上下文快照

    返回：
    - dict: 快照的完整数据（包含 context_state）
    - None: 回滚失败或未找到目标版本
    """
```

**实现逻辑**：
```python
def rollback_context(user_task, target_version=None):
    task_hash = hashlib.md5(user_task.encode('utf-8')).hexdigest()[:12]
    versions_dir = Path(".claude/context-versions") / task_hash

    if not versions_dir.exists():
        print(f"[MindFlow] ⚠️ 未找到上下文版本历史，无法回滚")
        return None

    # 确定目标版本
    if target_version is None:
        # 自动选择最近的 success 快照
        print(f"[MindFlow] 查找最近的成功快照...")
        snapshots = list_context_versions(user_task, status_filter="success")
        if not snapshots:
            print(f"[MindFlow] ⚠️ 未找到成功的上下文快照，无法回滚")
            return None
        target_version = snapshots[0]["version_id"]

    # 加载目标快照
    snapshot_path = versions_dir / f"{target_version}.json"
    if not snapshot_path.exists():
        print(f"[MindFlow] ⚠️ 快照 {target_version} 不存在")
        return None

    try:
        with open(snapshot_path, 'r', encoding='utf-8') as f:
            snapshot_data = json.load(f)

        print(f"[MindFlow] ✓ 回滚到快照 {target_version}:")
        print(f"[MindFlow]   迭代: {snapshot_data['iteration']}")
        print(f"[MindFlow]   阶段: {snapshot_data['phase']}")
        print(f"[MindFlow]   状态: {snapshot_data.get('status', 'unknown')}")
        print(f"[MindFlow]   时间: {snapshot_data['timestamp']}")

        return snapshot_data
    except Exception as e:
        print(f"[MindFlow] ⚠️ 快照加载失败: {e}")
        return None
```

### 4. compare_context_snapshots()

对比两个上下文快照的差异。

**调用时机**：
- 分析迭代失败原因时
- 诊断上下文污染问题时
- 调试 replan_trigger 变化时

**参数**：
```python
def compare_context_snapshots(
    user_task: str,           # 用户任务描述
    version_a: str,           # 快照A版本ID（如 "v1"）
    version_b: str            # 快照B版本ID（如 "v2"）
) -> dict:
    """
    对比两个快照的差异

    返回：
    - dict: {
        "diff": {
            "added_keys": [...],      # 新增的上下文键
            "removed_keys": [...],    # 删除的上下文键
            "changed_values": {...}   # 值变化的键及其新旧值
        },
        "summary": str               # 差异摘要
      }
    """
```

**实现逻辑**：
```python
def compare_context_snapshots(user_task, version_a, version_b):
    task_hash = hashlib.md5(user_task.encode('utf-8')).hexdigest()[:12]
    versions_dir = Path(".claude/context-versions") / task_hash

    # 加载两个快照
    snapshot_a_path = versions_dir / f"{version_a}.json"
    snapshot_b_path = versions_dir / f"{version_b}.json"

    try:
        with open(snapshot_a_path, 'r') as f:
            snapshot_a = json.load(f)
        with open(snapshot_b_path, 'r') as f:
            snapshot_b = json.load(f)
    except Exception as e:
        print(f"[MindFlow] ⚠️ 快照加载失败: {e}")
        return None

    # 提取上下文状态
    context_a = snapshot_a.get("context_state", {})
    context_b = snapshot_b.get("context_state", {})

    # 计算差异
    added_keys = set(context_b.keys()) - set(context_a.keys())
    removed_keys = set(context_a.keys()) - set(context_b.keys())

    changed_values = {}
    for key in set(context_a.keys()) & set(context_b.keys()):
        if context_a[key] != context_b[key]:
            changed_values[key] = {
                "old": context_a[key],
                "new": context_b[key]
            }

    # 生成差异摘要
    diff_result = {
        "diff": {
            "added_keys": list(added_keys),
            "removed_keys": list(removed_keys),
            "changed_values": changed_values
        }
    }

    # 输出对比结果
    print(f"[MindFlow] 上下文快照对比 ({version_a} → {version_b}):")
    if added_keys:
        print(f"[MindFlow]   新增键: {', '.join(added_keys)}")
    if removed_keys:
        print(f"[MindFlow]   删除键: {', '.join(removed_keys)}")
    if changed_values:
        print(f"[MindFlow]   变化键: {', '.join(changed_values.keys())}")
    if not (added_keys or removed_keys or changed_values):
        print(f"[MindFlow]   无差异")

    return diff_result
```

</api>

<integration>

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

</integration>

<examples>

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

</examples>

<notes>

## 注意事项

1. **快照存储位置**：`.claude/context-versions/{task_hash}/v{iteration}.json`
2. **任务哈希算法**：MD5(user_task)[:12]，与 checkpoint 保持一致
3. **快照状态**：pending（待执行）、success（成功）、failed（失败）
4. **自动保存时机**：每次进入 planner 前（包括首次和重新规划）
5. **回滚策略**：默认回滚到最近的 success 快照，可手动指定目标版本
6. **快照对比**：支持任意两个快照对比，辅助问题诊断
7. **清理策略**：任务完成后可选择保留或清理快照（建议保留用于审计）
8. **并发安全**：每次迭代一个快照文件，按迭代号递增，无并发冲突
9. **状态一致性**：快照必须包含完整的 context_state，确保回滚后逻辑连续
10. **与 checkpoint 的区别**：
    - checkpoint 用于中断恢复（进程级）
    - context-versioning 用于上下文回滚（逻辑级）

</notes>
