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

对照验收标准和项目现状逐一检查。**所有验证必须基于实际证据，不接受假设或主观判断。**

## 验收标准来源

| 来源 | 文件 | 粒度 |
|------|------|------|
| align | `align.json` → `acceptance_criteria` | 任务级（整体是否达标） |
| plan | `task.json` → 每个 subtask 的 `acceptance_criteria` | 子任务级（每个是否完成） |
| context | `context.json` → `code_style`、`toolchain` | 项目现状基准 |

## 执行流程

### 步骤 1：子任务验收（plan 标准）

读取 task.json，逐个检查子任务：

1. 确认 subtask.status 是否为 "completed"
2. 对照 subtask.acceptance_criteria 逐条验证：读取相关文件确认修改已生效、执行测试命令检查退出码、执行 lint/类型检查
3. 参考 exec worker 写入的 feedback 字段（自动测试结果）作为前置证据
4. 记录每条标准的通过/失败及证据

### 步骤 2：任务验收（align 标准）

读取 align.json，对照任务级验收标准逐条验证。每条标准需要通过命令执行、文件读取、搜索等方式获取客观证据。

### 步骤 3：收集证据

每个验收点必须附带具体证据：

| 证据类型 | 获取方式 | 示例 |
|---------|---------|------|
| 命令输出 | 执行 `pytest tests/ -v` | `5 passed, 0 failed` |
| 文件内容 | 读取文件并引用关键行 | `第42行: validate_token() 已添加` |
| 搜索结果 | Grep 搜索特定模式 | `无 TODO/FIXME 标记` |
| diff 对比 | 执行 `git diff HEAD` | `+3 files changed, 45 insertions` |

**无证据 = 未验证**。禁止基于"应该没问题"的推断判定通过。

### 步骤 4：双层评分

评分分为两层：**自动检查**（基于命令输出的客观指标）和**对齐评估**（基于 align 内容的主观判定）。

---

#### 第一层：自动检查（auto）

通过执行命令获取客观结果，每项 pass / fail / skip。这些检查项根据项目实际情况自动确定，常见项包括但不限于：

| 检查项 | 方法 | 判定 |
|--------|------|------|
| 测试通过 | 执行 toolchain.test_command | 退出码 0 = pass |
| Lint 通过 | 执行 toolchain.lint_command | 无新增错误 = pass |
| 类型检查 | 执行类型检查命令（如有） | 无新增错误 = pass |
| 构建成功 | 执行 toolchain.build_command（如有） | 退出码 0 = pass |
| 无回归 | 执行完整测试套件 | 无新增失败 = pass |
| 无风险模式 | Grep 搜索硬编码密码/SQL拼接/eval | 无匹配 = pass |
| 无半成品 | Grep 搜索 TODO/FIXME/HACK | 无新增 = pass |

> 自动检查项由 verify agent 根据 context.json 的 toolchain 和修改的文件类型动态决定。没有对应工具链的项标记 skip。

**自动检查不独立评分**，其结果作为第二层对齐评估的客观证据输入。

---

#### 第二层：对齐评估（alignment）

基于 align.json 的目标/标准/边界 和 context.json 的项目现状，对执行结果进行六个维度的评分。每个维度 0-10 分，必须给出扣分原因和证据（可引用第一层的自动检查结果）。

**维度 1：项目现状符合度（权重 15%）**

执行结果是否与项目当前状态一致。

- 依赖关系是否正确处理（未引入不存在的模块、未破坏现有导入链）
- 使用的 API/库版本是否与项目一致
- 是否考虑了项目现有的架构约束

评分依据：对照 context.json 的 dependencies 和 toolchain，引用构建命令的自动检查结果。

**维度 2：风格一致性（权重 15%）**

执行结果是否遵循项目现有代码风格。

- 命名约定（函数/变量/类）、缩进格式、导入组织、错误处理模式、注释风格

评分依据：对照 context.json 的 code_style 和 align.json 的 code_style_follow，引用 lint 的自动检查结果，读取修改的文件与同目录文件对比。

**维度 3：需求符合度（权重 25%）**

执行结果是否满足 align.json 中定义的任务目标和验收标准。

- 每条 acceptance_criteria 是否有证据表明已满足
- task_goal 描述的结果是否已实现

评分依据：逐条对照 acceptance_criteria，每条未满足扣 2-3 分。引用测试命令的自动检查结果。

**维度 4：实现完备性（权重 20%）**

任务是否被完整实现，没有遗漏。

- 所有子任务是否都已完成
- 边界条件和错误处理是否覆盖
- 是否存在半成品代码

评分依据：检查 task.json 中子任务 status，引用半成品搜索的自动检查结果。

**维度 5：任务偏离度（权重 15%）**

执行结果是否偏离了原始任务目标。

- 是否解决了错误的问题
- 修改的文件是否在 align.json 的 in_scope 范围内

评分依据：对照 task_goal 和 boundary.in_scope，执行 `git diff --name-only` 对比。

**维度 6：范围越界度（权重 10%）**

是否做了任务以外的事情。

- 是否修改了 boundary.out_of_scope 中列出的内容
- 是否引入了未要求的新功能/新依赖/新文件

评分依据：执行 `git diff --stat` 对照 out_of_scope 和 in_scope。

### 步骤 5：计算总分与判定

**总分** = 各维度得分 × 权重 之和（满分 10 分）

| 总分 | 判定 | flow 行为 |
|------|------|----------|
| ≥ 8.0 | **通过** | 进入 done |
| 6.0 - 7.9 | **边界** | 展示评分明细，由用户决定通过或继续迭代 |
| < 6.0 | **不通过** | 自动进入 adjust，携带低分维度作为失败原因 |

### 步骤 6：返回结果

返回结构包含两层数据：

```json
{
  "status": true,
  "total_score": 8.5,
  "auto_checks": [
    {"name": "测试通过", "result": "pass", "evidence": "pytest: 12 passed, 0 failed"},
    {"name": "Lint 通过", "result": "pass", "evidence": "ruff: no errors"},
    {"name": "无半成品", "result": "pass", "evidence": "grep TODO: 0 matches"}
  ],
  "dimensions": {
    "项目现状符合度": {"score": 9, "weight": 0.15, "evidence": "构建通过，依赖一致", "deductions": "无"},
    "风格一致性": {"score": 8, "weight": 0.15, "evidence": "lint 无新增错误", "deductions": "1处命名用了camelCase"},
    "需求符合度": {"score": 9, "weight": 0.25, "evidence": "5/5 标准通过", "deductions": "无"},
    "实现完备性": {"score": 8, "weight": 0.20, "evidence": "3/3 子任务完成", "deductions": "1处缺少边界检查"},
    "任务偏离度": {"score": 9, "weight": 0.15, "evidence": "所有修改在 in_scope 内", "deductions": "无"},
    "范围越界度": {"score": 8, "weight": 0.10, "evidence": "无额外文件修改", "deductions": "添加了1个辅助函数"}
  },
  "evidence_summary": "总体质量良好，5/5 验收标准通过",
  "low_dimensions": []
}
```

- `auto_checks`：自动检查的客观结果，pass / fail / skip
- `dimensions`：六维对齐评估，每维 0-10 分
- `low_dimensions`：得分 < 6 的维度列表，供 adjust 定位问题
- `total_score`：六维加权总分（0-10），决定通过/边界/不通过

## 验证检查模板

预定义的常见任务类型验证检查项见 [checklist.json](checklist.json)。

## 检查清单

- [ ] 子任务级验收已逐个检查
- [ ] 任务级验收已逐条对照
- [ ] 每个验收点都有实际证据
- [ ] 六维评分已完成（每个维度有证据和扣分原因）
- [ ] 总分已计算
- [ ] low_dimensions 已标记（得分 < 6 的维度）
