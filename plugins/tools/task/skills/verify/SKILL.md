---
name: verify
description: 结果验证规范 - 验收标准检查、质量验证的执行规范
user-invocable: false
context: fork
---

# 结果验证规范

结果验证是 loop 循环的第五步，负责检查任务执行结果是否符合验收标准。

## 执行目标

- 验证所有任务的验收标准是否通过
- 记录验证结果
- 决定是否进入下一轮迭代

## 执行步骤

### 0. 锚点对齐检查

在验收标准检查前，先验证任务执行结果是否与原始意图对齐。

使用工具：TaskGet

**步骤**：

1. **读取 anchor_snapshot**：
   ```
   main_task = TaskGet(main_task_id)
   anchor = main_task.metadata.get("anchor_snapshot", {})
   ```
   如果 `anchor_snapshot` 为空，跳过此步骤，直接进入步骤 1。

2. **检查关键约束**：
   ```
   for constraint in anchor.get("critical_constraints", []):
       status = verify_constraint(constraint)
       # ✅ 满足 / ⚠️ 存疑（需确认） / ❌ 违反
       if status == "violated":
           标记为 ❌，记录违反详情
   ```

3. **检查意图对齐**：
   - 比对当前执行结果与 `anchor.intent` 的一致性
   - 当有新指令（如 `/add`）修改过目标时，检查是否与原始意图冲突
   - 如发现冲突，通过 SendMessage 上报 leader

4. **输出对齐状态**：
   ```
   [锚点检查]
   Intent: ✅ 对齐
   关键约束:
     - Python 3.11+: ✅ 满足
     - 无新依赖: ⚠️ 引入了 pydantic（需确认）
   排除范围:
     - 不实现前端界面: ✅ 未涉及
   ```

**对齐状态判定**：

| 状态 | 条件 | 后续动作 |
|------|------|---------|
| ✅ 全部对齐 | 意图对齐 + 所有约束满足 | 继续步骤 1 |
| ⚠️ 部分存疑 | 意图对齐 + 部分约束存疑 | 记录存疑项，继续步骤 1 |
| ❌ 偏移/违反 | 意图偏移或关键约束被违反 | 通过 SendMessage 上报 leader，由 leader 决策 |

### 1. 检查验收标准

使用工具：TaskList, TaskGet

检查每个已完成任务的验收标准：
```
tasks = TaskList()
for task in tasks:
    if task.status == "completed":
        # 检查验收标准
        for criterion in task.acceptance_criteria:
            # 验证每一项
```

验收标准类型：
1. **自动化测试**：运行测试命令，检查通过率
2. **命令输出检查**：运行 lint、build 等，检查输出
3. **文件状态检查**：检查文件是否存在、内容是否正确

优先级：自动化测试 > 命令输出检查 > 文件状态检查

### 2. 更新验证结果

使用工具：TaskUpdate

记录每个任务的验证结果：
```
TaskUpdate(
  task_id=task_id,
  metadata={
    "verification_result": {
      "passed": true/false,  # 仅基于 acceptance_criteria
      "criteria_results": [
        {"criterion": "...", "passed": true/false, "details": "..."}
      ],
      "recommendations": [
        "建议添加 React.memo 优化性能",
        "建议拆分 NodeCard.tsx（600行）"
      ],  # 可选，不影响 passed 状态
      "verified_at": timestamp
    },
    "checkpoint_log": [
      {
        "timestamp": "2026-03-13 14:30:00",
        "phase": "verify",
        "findings": "T1 用户模型实现完成，3/3 验收标准通过",
        "alignment_check": {
          "intent": "✅",
          "constraints": {
            "Python 3.11+": "✅",
            "无新依赖": "⚠️ 引入 pydantic"
          }
        }
      }
    ]
  }
)
```

**字段说明**：

- `verification_result`：验收标准检查结果
- `checkpoint_log`：检查点记录（数组，每次验证追加一条）
  - `timestamp`：检查时间
  - `phase`：当前阶段（verify / adjust）
  - `findings`：本次检查的发现摘要
  - `alignment_check`：锚点对齐检查结果（来自步骤 0）

**关键**：`passed` 字段仅由 `acceptance_criteria` 决定，`recommendations` 中的建议事项不影响此字段。

## 验收标准规范

### 好的验收标准

必须满足：
- **可自动化**：能通过运行命令或脚本验证
- **可观测**：有明确的通过/失败判断
- **独立**：不依赖其他标准的结果
- **具体**：描述具体的检查项

示例：
```
验收标准：
- [ ] pytest tests/test_user.py 全部通过
- [ ] ruff check src/ 无错误
- [ ] API 返回 200 且包含 user_id 字段
- [ ] 文件 config.yaml 包含 database 配置块
```

### 差的验收标准

避免：
- 模糊描述："测试通过"、"代码规范"、"质量好"
- 主观判断："代码可读性好"、"性能不错"
- 无法验证："用户满意"

## 验收标准 vs 建议事项

**重要区分**：

| 类型 | 定义 | 失败处理 |
|------|------|---------|
| **验收标准** | 任务的 `acceptance_criteria` | 失败 → 进入步骤 6 |
| **建议事项** | 可选优化项（如代码风格、性能优化） | 记录但不影响任务完成 |

**示例**：
```
验收标准（必须通过）：
- [ ] 所有单元测试通过
- [ ] Lint 无错误
- [ ] API 返回正确响应

建议事项（可选优化，不影响任务完成）：
- 建议添加 React.memo 优化性能
- 建议拆分过长文件（>500行）
- 建议添加错误边界处理
```

## 验证决策

| 结果 | 定义 | 后续动作 |
|------|------|---------|
| **验收标准失败** | 部分**验收标准**未通过 | 直接进入步骤 6（失败调整） |
| **验收标准通过 + 有建议事项** | 验收标准全部通过，但有可选优化建议 | **AskUserQuestion 询问是否纳入任务** |
| **验收标准通过 + 无建议** | 验收标准全部通过，无建议 | Loop 完成 |

### 建议事项处理流程

当验收标准通过但有建议事项时：

```
1. 整理建议事项列表
2. 使用 AskUserQuestion 询问用户：
   "验收标准已全部通过，但发现以下可选优化建议：
    - 建议 1
    - 建议 2
    - 建议 3

    这些建议是否属于当前任务范围？
    - 是：将继续迭代完善
    - 否：任务完成，建议留待后续处理"

3. 根据用户回答：
   - 用户确认"是" → 进入步骤 6，将建议事项作为新的验收标准
   - 用户确认"否" → Loop 完成
```

## 输出要求

验证完成后：
1. 所有任务的验证结果已通过 TaskUpdate 记录
2. 明确哪些标准通过、哪些失败
3. 失败的标准记录了失败原因
4. 决定是否进入下一轮迭代

## 注意事项

- 不要跳过验收标准检查
- 不要主观判断，必须可自动验证
- 验证失败时记录详细原因
- 不直接修复问题，而是进入调整阶段
