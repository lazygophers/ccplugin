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

| 来源 | 文件 | 粒度 |
|------|------|------|
| align | `align.json` → `acceptance_criteria` | 任务级（整体是否达标） |
| plan | `task.json` → 每个 subtask 的 `acceptance_criteria` | 子任务级（每个是否完成） |

两层都必须通过才算验收成功。

## 执行流程

### 步骤 1：子任务验收（plan 标准）

读取 task.json，逐个检查子任务：

1. 确认 subtask.status 是否为 "completed"
2. 对照 subtask.acceptance_criteria 逐条验证：读取相关文件确认修改已生效、执行测试命令检查退出码、执行 lint/类型检查
3. 参考 exec worker 写入的 feedback 字段（自动测试结果）作为前置证据
4. 记录每条标准的通过/失败及证据

### 步骤 2：任务验收（align 标准）

读取 align.json，按三个维度验证任务级验收标准：

- **功能验证**：执行测试命令、读取修改文件确认关键逻辑、验证 bug 修复场景
- **质量验证**：执行 lint 命令检查新增错误/警告、确认符合 code_style
- **安全验证**：执行完整测试套件确认无回归、搜索风险模式（硬编码密码、SQL 拼接、eval）、检查错误处理路径

> 当验收标准 ≤ 2 条时，可退化为单维度顺序验证，避免不必要的开销。

### 步骤 3：收集证据

每个验收点必须附带具体证据：

| 证据类型 | 获取方式 | 示例 |
|---------|---------|------|
| 命令输出 | 执行 `pytest tests/ -v` | `5 passed, 0 failed` |
| 文件内容 | 读取文件并引用关键行 | `第42行: validate_token() 已添加` |
| 搜索结果 | Grep 搜索特定模式 | `无 TODO/FIXME 标记` |
| diff 对比 | 执行 `git diff HEAD` | `+3 files changed, 45 insertions` |

**无证据 = 未验证**。禁止基于"应该没问题"的推断判定通过。

### 步骤 4：计算质量评分（惩罚分模型）

基础分 100，每个维度扣分。**≥80 分判定通过**，60-79 为边界（附 confidence），<60 判定失败。

| 维度 | 权重 | 扣分规则 |
|------|------|---------|
| 功能正确 | 30 | 每个失败标准 -10，致命缺陷 -30 |
| 测试通过 | 25 | 新增测试未通过 -15，回归测试失败 -25 |
| 代码质量 | 20 | lint 新增错误每条 -5，上限 -20 |
| 安全合规 | 15 | 风险模式每项 -5，敏感数据泄露 -15 |
| 风格一致 | 10 | 命名不一致每处 -3，上限 -10 |

### 步骤 5：返回结果

返回结构包含 status、quality_score、confidence、score_breakdown、evidence_summary。

**置信度决策表**：

| quality_score | confidence | 决策 |
|---------------|------------|------|
| ≥80 | ≥0.7 | 通过 |
| 60-79 | ≥0.7 | 通过（附警告） |
| 60-79 | <0.7 | **暂停**，由 flow 通过 AskUserQuestion 让用户决定 |
| <60 | 任意 | 失败，进入 adjust |

失败时包含 failed_criteria 列表（name / category / reason / evidence / deduction）。

## 验证检查模板

预定义的常见任务类型验证检查项见 [checklist.json](checklist.json)。

## 检查清单

- [ ] 子任务级验收已逐个检查
- [ ] 任务级验收已逐条对照
- [ ] 每个验收点都有实际证据
- [ ] 失败原因具体到文件名、行号、命令输出
- [ ] 质量评分已计算（惩罚分模型）
- [ ] confidence 已评估
