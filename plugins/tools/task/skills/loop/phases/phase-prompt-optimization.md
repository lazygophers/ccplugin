
# PromptOptimization: 提示词优化

将用户任务描述转化为可执行规格说明，输出 prompt.md 作为后续所有阶段的验收基准。

## 触发条件

| 条件 | 行为 | 说明 |
|------|------|------|
| 首次迭代（iteration=1） | **必须执行** | 从零构建规格说明 |
| 用户提供新输入 | **增量修订** | 基于已有 prompt.md 局部更新，不重写 |
| 无新输入的后续迭代 | **跳过** | 复用已有 prompt.md，直接进入复杂度评估 |

"用户新输入"的来源：Planning rejected 时的 user_feedback、Adjustment ask_user 后的用户回复、QualityGate 不达标回退时用户提供的新方向。

## 关联资源

| 类型 | 名称 | 说明 |
|------|------|------|
| Agent | `task:prompt-optimizer` | 提示词优化代理 |
| Skill | `task:prompt-optimizer` | 提示词优化规范（DCG 方法论、验收标准设计） |

## 调用 Agent

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

Agent 内部完成：TaskDecomposition → ClarificationDialog → SpecGeneration → 写入 prompt.md。详见 agent/skill 定义。

## UserConfirmation：用户确认（由 loop 执行，非 agent）

prompt-optimizer 返回后，**loop 必须立即**通过 `AskUserQuestion` 让用户确认：

| 选项 | 描述 | 后续流程 |
|------|------|---------|
| **A: 确认使用** | 接受优化后的规格说明 | 更新 `context.user_task` → 复杂度评估 |
| **B: 确认并跳过计划确认** | 接受优化后的规格说明，同时授权跳过下一次 Planning 用户确认（仅单次有效） | 更新 `context.user_task` + 设置 `skip_next_plan_confirm=true` → 复杂度评估 |
| **C: 使用原始提示词** | 保持用户原始输入 | 将原始版本写入 prompt.md → 复杂度评估 |
| **D: 修正偏离部分** | 用户指出提示词与意图偏离的部分，提供修正内容 | 收集用户修正 → 重新调用 prompt-optimizer（增量修订模式，仅修正指定部分） |
| **E: 重新优化** | 提供反馈后全面重新优化 | 收集反馈 → 重新调用 prompt-optimizer |

**禁止**：跳过确认直接进入下一阶段。

### 选项 B 的行为说明

- **授权范围**：仅跳过紧接着的 Planning 阶段的用户确认（planner 内部自动批准）
- **单次有效**：Planning 完成后，`skip_next_plan_confirm` 标记自动清除
- **不影响后续**：下一次用户确认 PromptOptimization 时（如果有），依然需要选择 A/B/C/D/E
- **实现方式**：loop 将 `skip_next_plan_confirm=true` 写入 metadata.json，planner 读取后自动批准计划

### 选项 D 的行为说明

- **精准修正**：用户只需指出有偏离的具体部分（如"验收标准第2条不符合我的意图"、"边界定义遗漏了X场景"），提供修正内容
- **保留正确部分**：prompt-optimizer 在增量修订模式下，只修改用户指出的偏离部分，保留其他已确认正确的内容
- **修正后确认**：修正完成后，再次进入 UserConfirmation（用户可选择 A/B/C/D/E）
- **与选项 E 的区别**：D 是针对性修正（局部调整），E 是全面重新优化（可能大范围调整）

## 状态转换

- **选项 A/B/C** → 复杂度评估（决定是否触发 DeepResearch，之后进入 Planning）
- **选项 D/E** → 重新调用 prompt-optimizer（D=局部修正偏离部分，E=全面重新优化）
- **跳过（无新输入）** → 直接进入复杂度评估
