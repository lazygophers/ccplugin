
# PromptOptimization: 提示词优化

将用户任务描述转化为可执行规格说明，输出 prompt.md 作为后续所有阶段的验收基准。

## 触发条件

| 条件 | 行为 | 说明 |
|------|------|------|
| 首次迭代（iteration=1） | **必须执行** | 从零构建规格说明 |
| 用户提供新输入 | **增量修订** | 基于已有 prompt.md 局部更新，不重写 |
| 无新输入的后续迭代 | **跳过** | 复用已有 prompt.md，直接进入复杂度评估 |

"用户新输入"的来源：Planning rejected 时的 user_feedback、Adjustment ask_user 后的用户回复、QualityGate 不达标回退时用户提供的新方向。

## 调用 prompt-optimizer

```
Agent(subagent_type="task:prompt-optimizer", prompt="
  project_path: {project_path}
  task_id: {task_id}
  iteration: {iteration}
  working_directory: {working_directory}
  user_task: {user_task}
  mode: {首次迭代 ? 'create' : 'revise'}
  user_feedback: {user_feedback | null}
  existing_prompt_path: .claude/tasks/{task_id}/prompt.md
")
```

Agent 内部完成：TaskDecomposition → ClarificationDialog → SpecGeneration → 写入 prompt.md。详见 agent 定义。

## UserConfirmation：用户确认（由 loop 执行，非 agent）

prompt-optimizer 返回后，**loop 必须立即**通过 `AskUserQuestion` 让用户确认：

| 选项 | 描述 | 后续流程 |
|------|------|---------|
| **A: 确认使用** | 接受优化后的规格说明 | 更新 `context.user_task` → 复杂度评估 |
| **B: 使用原始提示词** | 保持用户原始输入 | 将原始版本写入 prompt.md → 复杂度评估 |
| **C: 重新优化** | 提供反馈后重新优化 | 收集反馈 → 重新调用 prompt-optimizer |

**禁止**：跳过确认直接进入下一阶段。

## 状态转换

- **选项 A/B** → 复杂度评估（决定是否触发 DeepResearch，之后进入 Planning）
- **选项 C** → 重新调用 prompt-optimizer（增量修订模式）
- **跳过（无新输入）** → 直接进入复杂度评估
