
# PromptOptimization: 提示词优化

将用户任务描述转化为可执行规格说明，输出 prompt.md 作为后续所有阶段的验收基准。

## 触发条件

| 条件 | 行为 | 说明 |
|------|------|------|
| 首次迭代（iteration=1） | **必须执行** | 从零构建规格说明 |
| 用户提供新输入 | **增量修订** | 基于已有 prompt.md 局部更新，不重写 |
| 无新输入的后续迭代 | **复用** | 读取已有 prompt.md 确认内容有效，进入复杂度评估 |

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
  existing_prompt_path: .lazygophers/tasks/{task_id}/prompt.md
")
```

Agent 内部完成：TaskDecomposition → ClarificationDialog → SpecGeneration → 写入 `.lazygophers/tasks/{task_id}/prompt.md`。详见 agent/skill 定义。

## UserConfirmation：用户确认（由 loop 执行，非 agent）

prompt-optimizer 返回后，**loop 必须立即**通过 `AskUserQuestion` 让用户确认。

**AskUserQuestion 调用格式**（必须先 `ToolSearch(query="select:AskUserQuestion")` 加载工具）：

```json
AskUserQuestion({
  "questions": [{
    "question": "规格说明已生成（.lazygophers/tasks/${task_id}/prompt.md），请确认是否使用",
    "header": "[MindFlow·${task_id}·提示词确认]",
    "options": [
      {"label": "A: 确认使用", "description": "接受优化后的规格说明"},
      {"label": "B: 确认并跳过计划确认", "description": "接受规格说明并授权跳过下一次Planning确认（单次有效）"},
      {"label": "C: 使用原始提示词", "description": "保持用户原始输入"},
      {"label": "D: 修正偏离部分", "description": "指出偏离部分或提供反馈重新优化"}
    ],
    "multiSelect": false
  }]
})
```

**后续流程**：

| 选项 | 后续处理 |
|------|---------|
| **A: 确认使用** | 更新 `context.user_task` → 复杂度评估 → **必须进入 Planning** |
| **B: 确认并跳过计划确认** | 更新 `context.user_task` + `skip_next_plan_confirm=true` → 复杂度评估 → **必须进入 Planning**（自动批准） |
| **C: 使用原始提示词** | 写入 `.lazygophers/tasks/{task_id}/prompt.md` → 复杂度评估 → **必须进入 Planning** |
| **D: 修正偏离部分** | 收集用户修正/反馈 → 重新调用 prompt-optimizer（增量修订模式） |

**禁止**：跳过确认直接进入下一阶段。

### 非预期响应处理（强制规则）

当用户**未选择 A/B/C/D**（包括但不限于：拒绝回答、连续拒绝、直接纠正错误、提供文字反馈、Other 输入等任何非选项响应），loop **必须**：

1. 将用户的反馈作为 `user_feedback` 重新调用 prompt-optimizer（增量修订模式）
2. prompt-optimizer 修订完成后，**再次进入 UserConfirmation**（再次 AskUserQuestion）
3. **重复此循环**直到用户明确选择 A/B/C

**核心原则**：只有用户明确选择 A/B/C 才是授权继续到下一阶段的唯一信号。无论用户拒绝多少次、纠正多少次，每次都必须重新确认。

**绝对禁止**：
- loop 自行判断"用户不想确认"而跳过 UserConfirmation
- prompt-optimizer 修改后不经确认直接进入 Planning
- 将连续拒绝解读为"用户同意"或"用户想跳过"

### 选项 B 的行为说明

- **授权范围**：仅跳过紧接着的 Planning 阶段的用户确认（planner 内部自动批准）
- **单次有效**：Planning 完成后，`skip_next_plan_confirm` 标记自动清除
- **不影响后续**：下一次用户确认 PromptOptimization 时（如果有），依然需要选择 A/B/C/D
- **实现方式**：loop 将 `skip_next_plan_confirm=true` 写入 metadata.json，planner 读取后自动批准计划

### 选项 D 的行为说明

- **精准修正**：用户只需指出有偏离的具体部分（如"验收标准第2条不符合我的意图"、"边界定义遗漏了X场景"），提供修正内容
- **保留正确部分**：prompt-optimizer 在增量修订模式下，只修改用户指出的偏离部分，保留其他已确认正确的内容
- **修正后确认**：修正完成后，再次进入 UserConfirmation（用户可选择 A/B/C/D）

## 状态转换

- **选项 A/B/C**（明确授权） → 复杂度评估 → (DeepResearch?) → **必须进入 Planning**（绝对禁止跳过 Planning 直接执行）
- **选项 D / 任何非预期响应** → 重新调用 prompt-optimizer（增量修订）→ 再次 UserConfirmation
- **无新输入** → 读取已有 prompt.md 确认内容有效 → 复杂度评估
