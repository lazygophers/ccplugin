
# PromptOptimization: 提示词优化

将用户任务描述转化为可执行规格说明，输出 prompt.md 作为后续所有阶段的验收基准。

## 触发条件

| 条件 | 行为 | 说明 |
|------|------|------|
| 首次迭代（iteration=1） | **必须执行** | 从零构建规格说明 |
| 用户提供新输入 | **增量修订** | 基于已有 prompt.md 局部更新，不重写 |
| 无新输入的后续迭代 | **跳过** | 复用已有 prompt.md，直接进入复杂度评估 |

"用户新输入"的来源：Planning rejected 时的 user_feedback、Adjustment ask_user 后的用户回复、QualityGate 不达标回退时用户提供的新方向。

## 执行流程

### 首次迭代：从零构建

**TaskDecomposition：任务分解与边界定义**

使用 `task:prompt-optimizer` 分析用户原始提示词，结合代码探索明确：
- **交付物定义**：最终应产出什么（用具体动词描述）
- **任务边界**：in-scope（本次要做的）/ out-of-scope（明确不做的）
- **影响范围**：涉及的模块、文件、功能区域
- **验收标准**：可量化、可独立验证的完成条件

**ClarificationDialog：澄清对话**

针对模糊点，通过 SendMessage(@main) → AskUserQuestion 向用户提问：
- 每次一个问题，附 2-3 建议选项
- 已可从代码/上下文推断的不问
- 最多 3 轮提问

**SpecGeneration：生成规格说明**

生成结构化的规格说明（≤500字），包含目标、边界、技术上下文、验收标准。

### 增量修订：用户新输入触发

1. 读取已有 `.claude/tasks/{task_id}/prompt.md`
2. 对比用户新输入与现有规格，识别需要变更的部分
3. 仅修改受影响的节（边界/验收标准/约束），保留其余内容
4. 如有新模糊点，提问确认（最多 1-2 轮）
5. 更新 iteration 字段

### PromptPersistence：持久化存储

将规格说明写入 `.claude/tasks/{task_id}/prompt.md`：
```markdown
---
task_id: ${task_id}
iteration: ${iteration}
created_at: ISO8601
---

## 目标
{目标描述}

## 边界
### In-scope
- {要做的事项}

### Out-of-scope
- {不做的事项}

## 技术上下文
- {约束条件}

## 验收标准
- [ ] {可独立验证的条件}
```

### UserConfirmation：用户确认

通过 `AskUserQuestion` 展示优化结果。用户可选择：

| 选项 | 描述 | 后续流程 |
|------|------|---------|
| **A: 确认使用** | 接受优化后的规格说明 | 更新 `context.user_task` → 复杂度评估 |
| **B: 使用原始提示词** | 保持用户原始输入 | 仍写入 prompt.md（原始版本）→ 复杂度评估 |
| **C: 重新优化** | 提供反馈后重新优化 | 收集反馈 → 回到 TaskDecomposition |

## prompt.md 作为验收基准

prompt.md 是整个 Loop 迭代的核心判定依据：

- **Planning**：读取 prompt.md 的边界和验收标准，据此设计任务分解
- **Verification**：逐条对照验收标准判定 passed/failed
- **QualityGate**：验收标准全部通过 + 质量分达标 → 迭代结束
- **Adjustment**：分析哪些验收标准未满足，决定恢复策略

如果 Verification 发现不满足 prompt.md 中的要求，标记为 failed → Adjustment → 若用户提供新方向则增量修订 prompt.md。

## 提问机制

Agent（prompt-optimizer）不可直接向用户提问。正确路径：Agent 通过 `SendMessage(@main)` 将问题发给 main，由 main 执行 `AskUserQuestion` 向用户提问。

## 状态转换

- **选项 A/B** → 复杂度评估（决定是否触发 DeepResearch，之后进入 Planning）
- **选项 C** → 回到 TaskDecomposition 重新优化
- **跳过（无新输入）** → 直接进入复杂度评估
