
# PromptOptimization: 提示词优化

**必选阶段**：每次迭代必须执行，确保任务描述清晰、边界明确、范围可控。优化后的提示词存储为独立文件，作为后续所有阶段的执行基准。

## 执行流程

**BoundaryAnalysis：任务边界分析**

使用 `task:prompt-optimizer` 分析用户原始提示词，明确以下内容：
- **任务边界**：哪些是本次任务要做的，哪些不做（in-scope / out-of-scope）
- **任务范围**：涉及哪些模块、文件、功能区域
- **交付物定义**：最终应产出什么（代码/文档/配置等）
- **验收标准**：怎样算做完了（可量化、可验证）

**StructuredQuestioning：结构化提问**

针对边界/范围中的模糊点，通过 5W1H 框架向用户提问：
- What：具体功能/期望输出
- Why：目的/解决什么问题
- Who：目标用户/权限要求
- When：截止时间/阶段目标
- Where：涉及模块/部署环境
- How：技术栈限制/性能要求

必要时（涉及未知技术栈/最佳实践）执行 WebSearch 补充信息。

**PromptGeneration：生成优化提示词**

基于分析和用户回答，生成结构化的优化提示词（≤500字），包含：
- 明确目标
- 任务边界（in-scope / out-of-scope）
- 技术约束
- 验收标准

**PromptPersistence：持久化存储**

将优化后的提示词写入 `.claude/tasks/{task_id}/prompt.md`：
```markdown
---
task_id: ${task_id}
iteration: ${iteration}
created_at: ISO8601
---

## 任务目标
{目标描述}

## 任务边界
### In-scope
- {要做的事项}

### Out-of-scope
- {不做的事项}

## 技术约束
- {约束条件}

## 验收标准
- {可量化标准}
```

**UserConfirmation：用户确认**

通过 `AskUserQuestion` 展示：
- 原始提示词
- 优化后的提示词
- 改进点列表

用户可选择：

| 选项 | 描述 | 后续流程 |
|------|------|---------|
| **A: 确认使用** | 接受优化后的提示词 | 更新 `context.user_task = optimized_prompt` → 复杂度评估 |
| **B: 使用原始提示词** | 保持用户原始输入 | 仍写入 prompt.md（原始版本）→ 复杂度评估 |
| **C: 重新优化** | 提供反馈后重新优化 | 收集反馈 → 回到 BoundaryAnalysis |

## 与 Verification 的关系

Verification 阶段必须读取 `.claude/tasks/{task_id}/prompt.md`，对照其中的：
- **任务边界**：验证交付物未超出 in-scope / 未遗漏
- **验收标准**：逐条验证是否满足
- **Out-of-scope**：确认未引入范围外的变更

如果 Verification 发现不满足 prompt.md 中的要求，标记为 failed，进入 Adjustment → 下一次迭代时重新执行 PromptOptimization。

## 提问机制

Agent（prompt-optimizer）不可直接向用户提问。正确路径：Agent 通过 `SendMessage(@main)` 将问题发给 main，由 main 执行 `AskUserQuestion` 向用户提问。

## 状态转换

- **选项 A/B** → 复杂度评估（决定是否触发 DeepResearch，之后进入 Planning）
- **选项 C** → 回到 BoundaryAnalysis 重新优化
