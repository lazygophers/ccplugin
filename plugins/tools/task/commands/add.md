---
description: 补充当前任务 - 在 Loop 执行过程中追加补充说明、纠正方向、添加约束或调整目标
argument-hint: [补充内容]
model: sonnet
memory: project
---

# 补充当前任务

在 Loop 执行过程中，向当前任务注入额外的上下文信息。

## 适用场景

| 场景 | 示例 |
|------|------|
| **补充说明** | `/add 数据库用 PostgreSQL，不要用 SQLite` |
| **纠正方向** | `/add 不要改 auth 模块，只改 session 模块` |
| **添加约束** | `/add 必须兼容 Python 3.11` |
| **调整目标** | `/add 先不管性能，优先保证功能正确` |
| **提供线索** | `/add 错误可能在 utils/token.py 的 verify 方法中` |

## 执行流程

### 1. 接收补充信息

将用户的补充内容分类：
- **约束追加**：新的技术约束或限制条件
- **方向纠正**：修改当前的执行方向
- **信息补充**：提供额外的背景信息或线索
- **目标调整**：修改或细化任务目标
- **范围变更**：扩大或缩小任务范围

### 2. 检查意图偏移（Anchor 对齐）

使用工具：TaskGet

读取主任务的 anchor_snapshot，检查补充内容是否与原始意图冲突：

```python
# 1. 读取 anchor
main_task = TaskGet(main_task_id)
anchor = main_task.metadata.get("anchor_snapshot", {})
intent = anchor.get("intent")
critical_constraints = anchor.get("critical_constraints", [])
excluded_scope = anchor.get("excluded_scope", [])

# 2. 检查语义冲突
if has_semantic_conflict(user_addition, intent):
    # 意图偏移检测到冲突
    drift_detected = True
else:
    drift_detected = False
```

**当检测到意图偏移时**，使用 AskUserQuestion 提供选项：

```
补充内容与原始任务意图存在冲突：

**原始意图**：{intent}

**新补充**：{user_addition}

**冲突分析**：
- 原始任务的核心目标是 {goal_A}
- 但补充内容要求 {goal_B}
- 这可能导致任务范围扩大或方向改变

请选择如何处理：
1. 修改 Anchor（更新核心意图）→ 版本升级 v1 → v2
2. 作为临时调整（不更新 Anchor）→ 仅影响当前迭代
3. 创建新任务（独立处理）→ 拆分为新的 Loop 任务
```

**选项说明**：

| 选项 | 适用场景 | 影响 |
|------|---------|------|
| 修改 Anchor | 用户改变了核心需求 | 永久改变任务目标，版本号升级 |
| 临时调整 | 用户提供补充信息或微调 | 仅影响当前迭代，不改变 Anchor |
| 创建新任务 | 用户提出了新的需求 | 拆分为独立任务，保持原任务不变 |

**Anchor 版本更新流程**（当用户选择"修改 Anchor"时）：

```python
# 1. 更新 anchor_snapshot
new_version = increment_version(anchor["version"])  # v1 → v2

TaskUpdate(
  task_id=main_task_id,
  metadata={
    "anchor_snapshot": {
      "version": new_version,
      "intent": updated_intent,
      "critical_constraints": updated_constraints,
      "excluded_scope": updated_excluded_scope,
      "assumptions": updated_assumptions,
      "changelog": [
        {
          "version": new_version,
          "timestamp": "...",
          "reason": "用户通过 /add 修改了核心意图",
          "changes": ["intent: ... → ...", "constraints: added X"]
        },
        ...previous_changelog
      ]
    }
  }
)

# 2. 输出变更确认
print(f"[Anchor 已更新] 版本：{old_version} → {new_version}")
print(f"核心意图：{old_intent} → {updated_intent}")
```

### 3. 注入当前任务

使用工具：TaskUpdate

将补充信息注入到当前执行上下文：
```
TaskUpdate(
  task_id=current_task_id,
  metadata={
    "user_additions": [
      {
        "type": "方向纠正",
        "content": "不要改 auth 模块，只改 session 模块",
        "timestamp": "...",
        "drift_handling": "temporary"  # 或 "anchor_updated" 或 "new_task"
      }
    ]
  }
)
```

影响：
- 下一次迭代的步骤 1（信息收集）会读取此信息
- 步骤 2（计划设计）会据此调整计划
- 如果 Anchor 已更新，所有后续验证都将基于新版本

### 4. 确认反馈

输出简要确认：
```
[补充已注入] 类型：方向纠正
内容：不要改 auth 模块，只改 session 模块
意图偏移：未检测到冲突
影响：下一次迭代将跳过 auth 相关修改
```

如果检测到意图偏移并更新了 Anchor：
```
[Anchor 已更新] 版本：v1 → v2
原始意图：实现用户认证功能
更新意图：实现用户认证和会话管理功能
变更原因：用户通过 /add 扩展了任务范围
影响：所有后续验证将基于新的核心意图
```

## 优先级

- **约束追加**：高优先级，必须遵守
- **方向纠正**：高优先级，立即调整
- **目标调整**：中优先级，影响后续规划
- **信息补充**：低优先级，作为参考
- **范围变更**：高优先级，需重新评估计划

## 注意事项

- 补充信息立即生效，但不会回滚已完成的步骤
- 如果补充内容与已完成的工作矛盾，会提示用户确认
- 多次 `/add` 的内容会累积，不会互相覆盖
- 补充内容必须清晰具体，避免模糊描述
