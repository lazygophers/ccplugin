---
description: 结果校验，验证执行结果是否符合预期
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

### 第2层：任务验收（align 标准）

读取 `align.json`，对照任务级验收标准：

```
对每个 acceptance_criteria：
  根据 criteria.name 选择验证策略：

  功能类（functionality / correctness / bug_resolved）：
    → 执行相关测试命令，检查退出码是否为 0
    → 读取修改的文件，确认关键逻辑存在
    → 如果有 bug 描述，验证修复逻辑覆盖了问题场景

  质量类（style_compliant / readability）：
    → 执行 lint 命令（来自 context.json 的 toolchain.lint_command）
    → 检查输出中是否有新增错误/警告
    → 读取修改的文件，确认符合 context.json 中的 code_style

  安全类（no_regression / no_new_risk）：
    → 执行完整测试套件，确认无新增失败
    → Grep 搜索常见安全风险模式（硬编码密码、SQL 拼接、eval 等）

  完整类（error_handling / coverage）：
    → 读取修改的文件，检查错误处理路径是否存在
    → 如果有覆盖率工具，执行并检查目标文件的覆盖率
```

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

### 验收通过

```json
{
  "status": true,
  "quality_score": 85,
  "evidence_summary": "5/5 验收标准通过，测试全绿，lint 无新增错误"
}
```

### 验收失败

```json
{
  "status": false,
  "failed_criteria": [
    {
      "name": "no_regression",
      "description": "未破坏现有功能",
      "category": "安全",
      "reason": "tests/test_auth.py::test_login_redirect 失败",
      "evidence": "pytest 输出: AssertionError: expected 302, got 200"
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
