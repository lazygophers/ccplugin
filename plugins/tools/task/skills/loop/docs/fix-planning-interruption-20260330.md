# 修复记录：计划设计阶段执行中断问题

> **注意**：本文档为历史修复记录。文中提到的 `plan-formatter` 已于 v0.0.186 合并至 `planner` 内部，不再作为独立组件存在。

**日期**：2026-03-30
**问题ID**：planning-stage-interruption
**严重程度**：高（阻塞核心流程）

## 问题描述

用户报告在执行 `/task:loop` 时，计划设计阶段的输出在 planner 返回 JSON 后就停止了，没有继续执行后续的 plan-formatter 和 AskUserQuestion 步骤。

**用户日志**：
```
∴ Thinking…

  好的，我已经完成了计划设计，现在需要返回 JSON 结果。让我输出最终的 JSON。

⏺ {
    "status": "completed",
（然后就停止了，没有继续）
```

## 根本原因分析

### 原因1：文档描述不够明确

loop SKILL.md 中关于阶段2的描述：

```markdown
**共同步骤**：调用 task:planner skill 设计计划 → ⚠️ **同一消息中连续执行** task:plan-formatter skill 格式化写入文件 → 更新 `context.plan_md_path` → （如需确认）**立即** AskUserQuestion
```

**问题**：
- "同一消息中连续执行"只是一个要求，不是执行指令
- 没有明确的分步骤说明
- Claude Code 看到"调用 task:planner"后，执行完就停止了

### 原因2：SKILL.md 作为执行指南的特性

SKILL.md 不是普通的文档，而是 Claude Code 的**执行指南**。描述必须：
- 具体、可操作
- 明确的步骤顺序
- 清晰的执行边界（什么时候可以停止，什么时候必须继续）

## 解决方案

### 修改前（模糊描述）

```markdown
**共同步骤**：调用 task:planner skill 设计计划 → ⚠️ **同一消息中连续执行** task:plan-formatter skill 格式化写入文件 → 更新 `context.plan_md_path` → （如需确认）**立即** AskUserQuestion
```

### 修改后（明确步骤）

```markdown
**执行步骤（必须在同一个回复消息中完成所有步骤）**：

**步骤1**：调用 `Skill(skill="task:planner", args="...")` 设计计划，必须传递6个上下文字段（project_path、task_id、iteration、plan_md_path、working_directory、user_task）

**步骤2**：处理 planner 返回的 questions 字段（如有），调用 AskUserQuestion 询问用户

**步骤3**：**在同一个回复中**，立即调用 `Skill(skill="task:plan-formatter", args="...")` 格式化计划并写入文件，更新 `context.plan_md_path`

**步骤4**：**在同一个回复中**，立即调用 `AskUserQuestion(...)` 请求用户批准计划（仅在 auto_approve=false 时执行）

⚠️ **关键要求**：步骤1-4必须在**同一个回复消息**中完成，不可分割。禁止在步骤1执行后就结束回复，必须继续执行后续步骤
```

### 关键改进

1. **明确的步骤编号**：步骤1、步骤2、步骤3、步骤4
2. **具体的工具调用**：`Skill(skill="task:planner", args="...")`
3. **强制性语言**：
   - "必须在同一个回复消息中完成所有步骤"
   - "禁止在步骤1执行后就结束回复"
   - "必须继续执行后续步骤"
4. **视觉强调**：使用 `**在同一个回复中**`、`**立即**` 等加粗文本

## 修改范围

修改了以下文件：

1. `plugins/tools/task/skills/loop/SKILL.md`（阶段2）
2. `plugins/tools/task/skills/loop/flows/plan.md`（路径A/B）
3. `plugins/tools/task/skills/loop/phases/phase-4-planning.md`（路径A/B）

## 验收标准

- ✅ loop skill 执行计划设计阶段时不再中断
- ✅ planner → plan-formatter → AskUserQuestion 在同一消息中完成
- ✅ 用户能正常看到计划确认界面
- ✅ 后续迭代中的重规划也能正常完成

## 经验教训

### 对 SKILL.md 编写的启示

1. **SKILL.md 是执行指南，不是功能说明**
   - 描述必须可操作、可执行
   - 避免使用"应该"、"建议"等模糊词汇
   - 使用"必须"、"禁止"、"立即"等强制性语言

2. **明确执行边界**
   - 什么时候可以结束当前回复
   - 什么时候必须继续执行
   - 哪些步骤必须在同一消息中完成

3. **分步骤描述复杂流程**
   - 使用步骤编号（步骤1、步骤2）
   - 每个步骤的输入和输出
   - 步骤之间的依赖关系

4. **使用具体的工具调用示例**
   - 不要只说"调用 planner"
   - 要说 `Skill(skill="task:planner", args="...")`
   - 提供参数传递的具体要求

### 类似问题预防

在编写或审查 SKILL.md 时，检查：
- ❓ 是否有"连续执行"、"同时"、"然后"等模糊词汇？
- ❓ 是否缺少明确的步骤编号？
- ❓ 是否缺少强制性语言（必须、禁止）？
- ❓ 是否没有明确的执行边界？

## 提交信息

```
commit 2e8832f4
fix(task/loop): 修复计划设计阶段执行中断问题
```

## 相关文档

- [loop SKILL.md](../SKILL.md)
- [flows/plan.md](../flows/plan.md)
- [phases/phase-4-planning.md](../phases/phase-4-planning.md)
