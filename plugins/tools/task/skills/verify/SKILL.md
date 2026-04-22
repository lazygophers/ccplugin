---
description: 验收校验。exec 完成后触发，对照子任务标准和任务级 SMART-V 标准逐一检查，基于命令输出和文件内容等实际证据判定通过/失败
memory: project
color: cyan
model: sonnet
permissionMode: bypassPermissions
background: false
user-invocable: false
effort: medium
context: fork
agent: task:verify
---

# Verify Skill

对照验收标准逐一检查。**所有验证必须基于实际证据，不接受假设或主观判断。**

## 验收标准来源

| 来源 | 文件 | 内容 | 粒度 |
|------|------|------|------|
| **align** | `align.json` → `acceptance_criteria` | 任务级验收标准（SMART-V） | 整体任务是否达标 |
| **plan** | `task.json` → 每个 subtask 的 `acceptance_criteria` | 子任务级验收标准 | 每个子任务是否完成 |

两层都必须通过才算验收成功。

## 验证流程

### 第1层：子任务验收（plan 标准）

读取 `task.json`，逐个检查子任务的执行结果：

```
对每个 subtask：
  1. 读取 subtask.status — 必须是 "completed"
  2. 对照 subtask.acceptance_criteria 中的每一条：
     - 读取相关文件，确认修改已生效
     - 如果标准涉及测试，执行测试命令检查退出码
     - 如果标准涉及 lint/类型检查，执行对应命令
  3. 记录通过/失败及证据
```

### 第2层：任务验收（align 标准）— 多维度并行验证

读取 `align.json`，按三个维度**并行**验证任务级验收标准：

```python
# 三个维度并行执行，各自独立收集证据
dimensions = []

# 维度1：功能验证 — 聚焦逻辑正确性
dimensions.append(Agent(
    description="功能验证",
    prompt="""验证功能正确性：
    - 执行相关测试命令，检查退出码
    - 读取修改的文件，确认关键逻辑存在
    - 如果有 bug 描述，验证修复覆盖了问题场景""",
    mode="bypassPermissions",
    run_in_background=False
))

# 维度2：质量验证 — 聚焦代码质量和风格
dimensions.append(Agent(
    description="质量验证",
    prompt="""验证代码质量：
    - 执行 lint 命令（来自 context.json 的 toolchain.lint_command）
    - 检查输出中是否有新增错误/警告
    - 读取修改的文件，确认符合 code_style""",
    mode="bypassPermissions",
    run_in_background=False
))

# 维度3：安全验证 — 聚焦回归和风险
dimensions.append(Agent(
    description="安全验证",
    prompt="""验证安全性和完整性：
    - 执行完整测试套件，确认无新增失败
    - Grep 搜索风险模式（硬编码密码、SQL 拼接、eval）
    - 检查错误处理路径是否存在""",
    mode="bypassPermissions",
    run_in_background=False
))

# 聚合三个维度的结果
all_passed = all(d.status for d in dimensions)
failed_criteria = merge_failures(dimensions)
```

> **注意**：当验收标准 ≤ 2 条时，可退化为单维度顺序验证，避免不必要的 agent 开销。

### 证据收集

每个验收点必须附带具体证据：

| 证据类型 | 获取方式 | 示例 |
|---------|---------|------|
| 命令输出 | `Bash(command="pytest tests/ -v")` | `5 passed, 0 failed` |
| 文件内容 | `Read(file_path="src/auth.py")` + 关键行引用 | `第42行: validate_token() 已添加` |
| 搜索结果 | `Grep(pattern="TODO\|FIXME\|HACK")` | `无匹配 — 无遗留标记` |
| diff 对比 | `Bash(command="git diff HEAD")` | `+3 files changed, 45 insertions` |

**无证据 = 未验证**。禁止基于"应该没问题"的推断判定通过。

## 返回结构

### 质量评分（惩罚分模型）

基础分 100，每个维度扣分。**≥80 分判定通过**，60-79 为边界（附 confidence），<60 判定失败。

| 维度 | 权重 | 扣分规则 |
|------|------|---------|
| 功能正确 | 30 | 每个失败标准 -10，致命缺陷直接 -30 |
| 测试通过 | 25 | 新增测试未通过 -15，回归测试失败 -25 |
| 代码质量 | 20 | lint 新增错误每条 -5，上限 -20 |
| 安全合规 | 15 | 风险模式每项 -5，敏感数据泄露 -15 |
| 风格一致 | 10 | 命名不一致每处 -3，上限 -10 |

### 返回结构

```json
{
  "status": true,
  "quality_score": 85,
  "confidence": 0.9,
  "score_breakdown": {
    "功能正确": {"base": 30, "deductions": 0, "final": 30},
    "测试通过": {"base": 25, "deductions": -5, "final": 20, "reason": "1 条边界测试未覆盖"},
    "代码质量": {"base": 20, "deductions": 0, "final": 20},
    "安全合规": {"base": 15, "deductions": -5, "final": 10, "reason": "1 处��编码配置"},
    "风格一致": {"base": 10, "deductions": -5, "final": 5, "reason": "2 处命名不一致"}
  },
  "evidence_summary": "5/5 验收标准通过，测试全绿，lint 无新增错误"
}
```

### 置信度与决策

| quality_score | confidence | 决策 |
|---------------|------------|------|
| ≥80 | ≥0.7 | 通过 |
| 60-79 | ≥0.7 | 通过（附警告） |
| 60-79 | <0.7 | **暂停**，通过 AskUserQuestion 让用户决定 |
| <60 | 任�� | 失败，进入 adjust |

### 验收失败

```json
{
  "status": false,
  "quality_score": 55,
  "confidence": 0.8,
  "failed_criteria": [
    {
      "name": "no_regression",
      "category": "安全",
      "reason": "tests/test_auth.py::test_login_redirect 失败",
      "evidence": "pytest 输出: AssertionError: expected 302, got 200",
      "deduction": -25
    }
  ],
  "summary": "1/5 验收标准未通过：test_login_redirect 回归失败"
}
```

## 验证检查模板

预定义的常见任务类型验证检查项见 [checklist.json](checklist.json)，包含 bug-fix / new-feature / refactor / security-fix 四种类型的验证检查清单。

## 与 adjust 的协作

验收失败时返回 `status: false`，flow 会自动调用 adjust skill，由 adjust 分析失败原因并决定后续策略：
- 上下文缺失 → 返回 explore
- 需求偏差 → 返回 align
- 重新计划 → 返回 plan
- 放弃 → 进入 done

## 检查清单

- [ ] plan 子任务级验收已逐个检查
- [ ] align 任务级验收已逐条对照
- [ ] 每个验收点都有命令输出/文件内容等实际证据
- [ ] 失败原因具体到文件名、行号、命令输出
