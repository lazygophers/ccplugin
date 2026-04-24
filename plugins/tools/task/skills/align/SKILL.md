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

**核心规则：**

1. **align 的唯一终止条件是用户通过 AskUserQuestion 明确确认**。未经确认，禁止写入 align.json，禁止返回结果。
2. **任何时候 align 内容发生变化（首次生成、用户调整、adjust 回来重新对齐、explore 补充上下文后重新生成），都必须重新向用户确认。** 没有例外。
3. **已有 align.json 也不能跳过确认。** 从 adjust 返回时，必须展示修改后的内容让用户重新确认。

## 独立调用模式

当用户直接调用 `/task:align` 时（无 flow 上下文）：

1. 从用户输入生成中文 task_id（≤10 字符）
2. 执行 `task update {task_id} --status=align` 创建任务
3. 按下方流程执行
4. 对齐完成后输出结果，**不自动进入后续阶段**

当由 flow 调用时：直接使用传入的 task_id 和 environment 参数。

## 执行流程

align 分为两个阶段：**生成**和**确认**。生成阶段准备对齐内容，确认阶段获得用户批准。两个阶段缺一不可。

---

### 阶段一：生成对齐内容

#### 1. 检查上下文

读取 `.lazygophers/tasks/{task_id}/context.json`。

- 文件存在且包含 `task_related` 和 `code_style` → 继续
- 文件不存在，但 prompt 已明确指定文件路径和修改内容 → 从 prompt 提取上下文，采样代码风格，写入 context.json
- 文件不存在且信息不足 → 返回 `need_explore: true`

#### 2. 锁定项目风格

从 context.json 的 `code_style` 获取项目风格，作为后续所有阶段的锁定风格。

#### 3. 识别任务类型

根据 prompt 关键词判断任务类型：

| 关键词 | 类型 |
|--------|------|
| 修复/fix/bug/报错/失败 | bug-fix |
| 添加/新增/实现/开发/功能 | new-feature |
| 重构/优化/整理/简化 | refactor |
| 测试/test/覆盖 | add-tests |
| 安全/漏洞/CVE/注入 | security-fix |

匹配到模板时以模板为基础细化。模板文件见 [templates/](templates/)。

#### 4. 生成目标、标准、边界

**任务目标**：一句话描述要达成的结果。

**验收标准**：3-5 条，每条满足 SMART-V（Specific/Measurable/Achievable/Relevant/Time-bound/Verifiable），结构为 `name` + `description`。

**边界**：`in_scope`（要做的事）+ `out_of_scope`（不做的事）。

如果是从 adjust 返回的重新对齐，参考失败原因调整。**调整后必须重新走阶段二确认，不能复用之前的确认。**

#### 5. 生成行为规约

- **always_do**：必须执行的操作
- **ask_first**：高风险操作需先确认
- **never_do**：硬止点（从 out_of_scope 派生 + 禁止提交 secrets + 禁止跳过 lint）

---

### 阶段二：用户确认

**⚠ 以下步骤是硬性门控。不执行此步骤 = align 未完成。禁止跳过。**

#### 6. 通过 AskUserQuestion 展示对齐结果并等待确认

必须调用 AskUserQuestion，向用户展示以下全部内容：

- 任务目标
- 验收标准（逐条列出）
- 边界（in_scope / out_of_scope）
- 检测到的项目风格

提供两个选项：
- **确认继续** — 对齐结果正确
- **需要调整** — 需要修改

**如果用户选择"需要调整"**：追问具体方向（目标不准确 / 标准不合理 / 边界不清晰 / 风格检测错误），然后返回 `need_explore: true` 携带反馈。

**如果用户选择"确认继续"**：进入步骤 7。

#### 7. 写入 align.json

**仅在用户确认后执行此步骤。**

写入 `.lazygophers/tasks/{task_id}/align.json`：

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

`user_confirmed: true` 是 flow 进入 plan 的前置条件。

---

## 验收标准示例

常见语义化名称：functionality, correctness, bug_resolved, style_compliant, no_regression, no_new_risk, performance_improved

## 检查清单

- [ ] context.json 已读取或生成
- [ ] 任务类型已识别
- [ ] 3-5 条验收标准，每条满足 SMART-V
- [ ] 边界已明确
- [ ] 行为规约三层已生成
- [ ] **AskUserQuestion 已调用，用户已选择"确认继续"**
- [ ] align.json 已写入，包含 `user_confirmed: true`
