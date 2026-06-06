---
description: "Generates Conventional Commits Git commit messages."
when_to_use: |
  Use when the user needs to commit code changes, stage or unstage Git changes, amend a commit, draft or review a commit message, or format a message using Conventional Commits.
  Trigger on: commit, git commit, staged changes, stage, unstage, amend, commit message, Conventional Commits, save changes, 提交, 暂存, 提交信息, 生成提交, 生成提交信息, 改提交, 帮我提交.
user-invocable: true
context: fork
model: haiku
memory: project
---

# Git Commit 规范

生成符合 Conventional Commits 的提交信息，并指导提交前后检查。

## 提交信息模板

```
<type>(<scope>): <subject>

<body>
<footer>
```

## 字段规则

- `type`: 必填。可选值：`feat`、`fix`、`docs`、`style`、`refactor`、`perf`、`test`、`chore`、`revert`、`build`、`ci`、`wip`、`workflow`、`types`、`release`、`other`
- `scope`: 可选。使用受影响模块、包、插件、目录或功能名，如 `git`、`commit`、`api`、`docs`、`build`
- `subject`: 必填。不超过 50 字符，使用祈使语气，首字母小写，结尾无句号
- `body`: 可选。说明变更原因、影响和关键取舍，单行建议不超过 80 字符
- `footer`: 可选。填写 breaking change 或 issue 关闭信息，如 `BREAKING CHANGE: ...`、`close #123`

## 提交流程

1. 运行 `git status` 查看工作区状态。
2. 确认变更文件符合预期，没有敏感信息、临时文件、日志、备份或无关文件。
3. 运行相关测试或 lint；若用户明确要求跳过，说明风险。
4. 使用 `git add <file...>` 只暂存本次提交需要的文件。
5. 运行 `git diff --cached` 检查暂存内容。
6. 根据暂存 diff 生成 Conventional Commits 信息。
7. 执行 `git commit -m "<message>"`，多行提交使用 heredoc。
8. 运行 `git log -1 --oneline` 或 `git status` 验证提交成功。

## 检查清单

### 提交前

- [ ] `git status` 已查看
- [ ] 暂存文件只包含本次提交范围
- [ ] `git diff --cached` 已检查
- [ ] 敏感信息、备份、日志、临时、二进制、压缩文件未提交
- [ ] 相关测试或 lint 已运行，或跳过原因已说明

### 提交信息

- [ ] 格式符合 `<type>(<scope>): <subject>`
- [ ] `type` 与变更性质匹配
- [ ] `scope` 聚焦受影响区域
- [ ] `subject` 简洁、祈使语气、无句号
- [ ] 多类型变更拆成多个 commit
- [ ] breaking change 或 issue footer 正确填写

### 提交后

- [ ] 最新提交存在且信息正确
- [ ] 提交包含预期文件
- [ ] 工作区只剩用户刻意保留的变更

## 示例

```bash
git commit -m "feat(auth): add login flow"
git commit -m "fix(api): handle empty user response"
git commit -m "docs(readme): update install guide"
git commit -m "refactor(git): merge commit command into skill"
```

## 禁止

- 禁止提交模糊信息，如 `update`、`fix bug`、`changes`
- 禁止把无关变更混入同一 commit
- 禁止提交未授权的敏感信息、临时文件、日志、备份、构建产物
- 禁止主动跳过 hooks，除非用户明确要求
