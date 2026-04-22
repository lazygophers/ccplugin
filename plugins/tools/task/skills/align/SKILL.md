---
description: 任务范围对齐。当用户需要明确任务目标、定义验收标准或确认实施边界时触发，自动生成 SMART-V 标准，通过交互确认后写入 align.json
memory: project
color: blue
model: sonnet
permissionMode: bypassPermissions
background: false
context: fork
user-invocable: true
effort: high
argument-hint: [任务描述]
---

# Align Skill

## 独立调用模式

当用户直接调用 `/task:align` 时（无 flow 上下文）：

1. 从用户输入生成中文 task_id（≤10 字符）
2. 执行 `task update {task_id} --status=align` 创建任务
3. 按下方执行流程生成对齐结果
4. 对齐完成后输出结果，**不自动进入后续阶段**

当由 flow 调用时：直接使用传入的 task_id 和 environment 参数。

## 执行流程

### 步骤 1：检查上下文

读取 `.lazygophers/tasks/{task_id}/context.json`。

- 如果文件存在且包含 `task_related` 和 `code_style` → 继续步骤 2
- 如果文件不存在，但用户 prompt 中已明确指定了文件路径和修改内容 → 从 prompt 中提取上下文，读取指定文件采样代码风格，写入 context.json 后继续步骤 2
- 如果文件不存在且 prompt 信息不足 → 返回 `need_explore: true`，由 flow 调度 explore

### 步骤 2：锁定项目风格

从 context.json 的 `code_style` 字段获取项目风格（命名约定、缩进、导入模式等），作为后续所有阶段的锁定风格。无需用户确认。

### 步骤 3：识别任务类型

根据用户 prompt 中的关键词判断任务类型，匹配预定义模板：

| 关键词 | 任务类型 |
|--------|---------|
| 修复/fix/bug/报错/失败 | bug-fix |
| 添加/新增/实现/开发/功能 | new-feature |
| 重构/优化/整理/简化 | refactor |
| 测试/test/覆盖 | add-tests |
| 安全/漏洞/CVE/注入 | security-fix |

匹配到模板时以模板为基础细化，未匹配时完全自主生成。模板文件见 [templates/](templates/) 目录。

### 步骤 4：生成任务目标和验收标准

基于用户 prompt、context.json 和模板（如有），生成：

**任务目标**（task_goal）：一句话描述要达成的结果。

**验收标准**（acceptance_criteria）：3-5 条，每条必须满足 SMART-V 原则：
- **S**pecific：具体明确
- **M**easurable：可量化验证
- **A**chievable：可实现
- **R**elevant：与目标相关
- **T**ime-bound：有明确完成定义
- **V**erifiable：可通过客观证据验证

每条标准结构：`name`（语义化，如 functionality / no_regression）+ `description`。

**边界**（boundary）：
- `in_scope`：本次任务要做的事
- `out_of_scope`：明确不做的事（默认包含：新功能添加、架构重构、性能优化、文档更新，除非用户明确要求）

如果是从 adjust 返回的重新对齐，参考 adjust 提供的失败原因调整上述内容。

### 步骤 5：生成行为规约

基于任务类型和边界，生成三层行为约束：

- **always_do**：必须执行的操作（如"修改代码后运行测试"、"遵循锁定风格"）
- **ask_first**：高风险操作需先确认（如"修改数据库 schema"、"删除现有代码"）
- **never_do**：硬止点，从 out_of_scope 自动派生 + "禁止提交 secrets" + "禁止跳过 lint"

### 步骤 6：向用户确认（硬性门控，不可跳过）

> ⚠ 这是整个任务流程中唯一的用户确认点。无论任务多简单，都必须执行此步骤。

通过 AskUserQuestion 向用户展示完整的对齐结果（目标、验收标准、边界、项目风格），提供两个选项：

- **确认继续**：对齐结果正确，进入规划阶段
- **需要调整**：需要修改

如果用户选择"需要调整"，追问具体调整方向（目标不准确 / 标准不合理 / 边界不清晰 / 风格检测错误），然后返回 `need_explore: true` 携带用户反馈，由 flow 重新调度。

### 步骤 7：写入对齐结果

用户确认后，将以下内容写入 `.lazygophers/tasks/{task_id}/align.json`：

```json
{
  "task_id": "任务ID",
  "task_goal": "任务目标",
  "acceptance_criteria": [...],
  "boundary": {"in_scope": [...], "out_of_scope": [...]},
  "behavior_spec": {"always_do": [...], "ask_first": [...], "never_do": [...]},
  "code_style_follow": {...},
  "user_confirmed": true
}
```

返回此对齐结果给 flow。

## 验收标准示例

常见语义化名称（仅供参考）：
- 功能：functionality, correctness, bug_resolved
- 质量：style_compliant, readability, maintainability
- 安全：no_regression, no_new_risk, vulnerability_fixed
- 性能：performance_improved, complexity_controlled

## 检查清单

- [ ] context.json 已读取或生成
- [ ] 任务类型已识别
- [ ] 3-5 条验收标准，每条满足 SMART-V
- [ ] 边界（in_scope / out_of_scope）已明确
- [ ] 行为规约三层已生成
- [ ] **用户已通过 AskUserQuestion 确认**（不可跳过）
- [ ] align.json 已写入，包含 `user_confirmed: true`
