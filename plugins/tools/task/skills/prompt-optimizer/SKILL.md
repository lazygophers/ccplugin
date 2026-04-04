---
description: "提示词优化 - 将模糊任务描述转化为可执行规格说明（Deliverable + Context + Guardrails），输出 prompt.md 作为迭代验收基准"
model: sonnet
user-invocable: false
agent: task:prompt-optimizer
hooks:
  SessionStop:
    - hooks:
        - type: command
          command: "PLUGIN_NAME=task uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py hooks_skills"
  SubagentStart:
    - hooks:
        - type: command
          command: "PLUGIN_NAME=task uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py hooks_skills"
---

# Skills(task:prompt-optimizer) - 提示词优化规范

## 定位

将用户的自然语言任务描述转化为**可执行的规格说明**（Executable Specification）。优化后的 prompt.md 是整个 Loop 迭代的**验收基准**——Verification 阶段逐条对照其中的验收标准判定是否通过，是决定迭代是否继续的核心依据。

## 触发条件

| 条件 | 说明 |
|------|------|
| 首次迭代（iteration=1） | 必须执行，建立初始规格说明 |
| 用户提供新输入 | rejected/ask_user/QualityGate不达标回退时，用户给出了新的方向或反馈 |
| 无新输入的后续迭代 | **跳过**，复用已有 prompt.md |

## 核心方法论

基于 Anthropic 2026 最佳实践和学术研究共识，提示词优化的本质不是"写更长的提示词"，而是**写更清晰的规格说明**。

### 规格说明三要素（Deliverable-Context-Guardrails）

| 要素 | 必须回答的问题 | 输出 |
|------|--------------|------|
| **Deliverable（交付物）** | 做什么？做到什么程度算完？ | 目标描述 + 验收标准（可量化） |
| **Context（最小必要上下文）** | 项目背景、技术栈、当前状态、依赖约束 | 技术上下文 + 约束条件 |
| **Guardrails（护栏）** | 什么不做？什么不能碰？格式/风格要求？ | in-scope / out-of-scope 边界 |

### 验收标准设计原则

验收标准是 prompt.md 中最关键的部分——它直接决定 Verification 的判定结果和迭代是否继续。

| 原则 | 好 | 差 |
|------|---|---|
| 可验证 | "用户可通过邮箱+密码登录" | "实现登录功能" |
| 可量化 | "测试覆盖率≥80%" | "覆盖率高" |
| 独立 | 每条标准可独立验证 | 多个条件混在一句话里 |
| 原子 | "API 返回 200 + 正确 JSON" | "API 工作正常" |
| 结果导向 | "用户看到成功提示" | "调用了 toast 组件" |

## 执行流程

### TaskDecomposition：任务分解与边界定义

分析用户原始提示词，通过代码探索（Glob/Grep/Read）了解项目现状，输出：

1. **任务目标**：最终要达到什么结果，用具体动词描述
2. **任务边界**：in-scope（本次要做的）/ out-of-scope（明确不做的）
3. **验收标准**：可量化、可独立验证的完成条件（每条一个判定点）

### ClarificationDialog：澄清对话

针对分解结果中的模糊点，通过 `SendMessage(@main)` 向用户提问。

**提问策略**（按优先级排序）：
1. **What**：交付物不明确时——"你期望最终产出什么？"
2. **Where**：影响范围不清时——"这个变更涉及哪些模块？"
3. **How**：技术约束不明时——"有技术栈或架构限制吗？"
4. **Why**：动机不清影响方案选择时——"这个需求要解决什么问题？"

**提问规则**：
- 每次只问一个问题，附 2-3 个建议选项
- 已可从代码/上下文推断的信息不提问
- 用户回答后立即更新规格说明，不累积问题
- 最多 3 轮提问，避免过度打扰

### SpecGeneration：生成规格说明

基于分解结果和用户回答，生成结构化的规格说明（≤500字），直接写入 prompt.md 文件。**禁止**将规格说明内容输出到对话中——只写入文件，不打印。

## 调用协议

```
Skill(skill="task:prompt-optimizer", args="优化用户提示词：\n原始提示：{input}\ntask_id：{task_id}\n项目路径：{project_path}\n迭代：{iteration}\n触发原因：{trigger_reason}")
```

`trigger_reason` 取值：`first_iteration` | `user_new_input` | `rejected` | `quality_gate_fail`

## 输出格式

```json
{
  "status": "optimized",
  "original_prompt": "用户原始输入",
  "optimized_prompt": "优化后的规格说明（≤500字）",
  "boundary": {
    "in_scope": ["要做的事项"],
    "out_of_scope": ["不做的事项"]
  },
  "acceptance_criteria": ["可量化的验收标准"],
  "improvements": ["相比原始提示词的改进点"],
  "questions_asked": 0,
  "report": "≤100字的优化摘要"
}
```

**关键字段说明**：
- `acceptance_criteria`：Verification 阶段逐条对照此数组判定 passed/failed，是迭代是否继续的核心依据
- `boundary`：Verification 检查是否超出 in-scope 或遗漏，是否引入 out-of-scope 变更
- `status`：固定为 `"optimized"`

## 与其他阶段的交互

| 阶段 | 交互方式 |
|------|---------|
| **Loop（调用方）** | 首次迭代或用户新输入时调用，其他迭代跳过 |
| **Planning** | 读取 prompt.md 的边界和验收标准，据此设计任务分解 |
| **Verification** | 读取 prompt.md，逐条对照验收标准判定 passed/failed |
| **QualityGate** | 验收标准全部通过 + 质量分达标 → 迭代结束 |
| **Adjustment** | 失败时分析哪些验收标准未满足，决定恢复策略 |
