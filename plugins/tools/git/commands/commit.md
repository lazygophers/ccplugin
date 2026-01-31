---
description: Git 智能提交 - 基于暂存变更自动生成高质量提交信息并提交
argument-hint: [message]
allowed-tools: Bash(git:*)
model: sonnet
---

# commit

## 命令描述

基于当前暂存区的变更，智能生成符合 Conventional Commits 规范的提交信息，并安全地提交代码。包含敏感信息检查和文件验证。

## 工作流描述

1. **检查 Git 状态**：获取当前分支、暂存文件和变更统计
2. **安全检查**：检查暂存区是否包含敏感文件或不合适的文件
3. **生成提交信息**：根据暂存变更内容生成高质量提交信息
4. **执行提交**：使用 `git commit` 提交暂存区变更

## 命令执行方式

### 使用方法

```bash
git-skills commit -m "[message]"
```

### 执行时机

- 完成某个功能或修复后需要提交
- 暂存区已包含需要提交的文件
- 需要生成规范的提交信息

### 执行参数

| 参数 | 说明 | 类型 | 必填 |
|------|------|------|------|
| `message` | 提交信息（可选，不提供时自动生成） | string | ✗ |

**提交信息格式**：遵循 Conventional Commits 规范
```
<type>(<scope>): <subject>

<body>

<footer>
```

### 命令说明

- 提交前自动检查敏感文件（.env、credentials 等）
- 检查临时/构建文件是否误提交
- 提示文件大小超过 10MB 的情况
- 提交信息支持中文，≤50 字符

## 相关Skills（可选）

参考 Git 操作技能：`@${CLAUDE_PLUGIN_ROOT}/skills/git/SKILL.md`

## 依赖脚本

```bash
# 无外部脚本依赖，使用 git-skills 原生命令
```

## 示例

### 基本用法

```bash
# 自动生成提交信息
git-skills add src/
git-skills commit -m "auto-generated message"

# 指定提交信息
git-skills add src/auth/
git-skills commit -m "feat: 添加用户认证"
```

### 提交信息示例

```bash
# 新功能
git-skills commit -m "feat: 添加用户登录功能"

# 缺陷修复
git-skills commit -m "fix: 修复登录超时问题"

# 代码重构
git-skills commit -m "refactor: 优化数据库查询"

# 文档更新
git-skills commit -m "docs: 更新 API 文档"
```

## 检查清单

在执行提交前，确保满足以下条件：

- [ ] 已使用 `git add` 添加需要提交的文件
- [ ] 检查暂存区内容是否正确
- [ ] 没有遗漏需要提交的重要文件
- [ ] 提交信息清晰准确（如手动指定）

## 注意事项

**敏感文件检查**：
- 禁止提交：`.env*`、`*.secret`、`*.key`、`*.pem`、`credentials.json`、`.npmrc`、`.aws/`、`.ssh/`
- 如发现敏感文件，须先移除：`git reset HEAD <file>`

**临时/构建文件检查**：
- 禁止提交：`node_modules/`、`__pycache__/`、`.venv/`、`dist/`、`build/`、`*.log`、`*.tmp`
- 检查 `.gitignore` 是否配置正确

**文件大小检查**：
- 文件大小 > 10MB 时发出警告
- 考虑使用 Git LFS 或外部存储

**提交信息要求**：
- ≤50 字符
- 使用简体中文
- 遵循 Conventional Commits 规范
- 描述意图（为什么改）而非内容（改了什么）

## 其他信息

### 提交类型说明

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | feat: 添加用户认证功能 |
| `fix` | 缺陷修复 | fix: 修复登录超时问题 |
| `refactor` | 代码重构 | refactor: 优化数据库查询 |
| `docs` | 文档更新 | docs: 更新 API 文档 |
| `test` | 测试相关 | test: 添加单元测试 |
| `chore` | 构建/工具 | chore: 更新依赖版本 |
| `style` | 代码格式 | style: 统一代码缩进 |

### 提交信息最佳实践

- **清晰具体**：描述具体改动而非模糊的"修复"或"更新"
- **单一职责**：一个提交只做一件事
- **包含上下文**：在 body 中说明为什么做这个改动

### 推送前步骤

1. 验证提交成功：`git status` 应显示工作目录干净
2. 检查提交日志：`git log --oneline -1` 确认提交信息
3. 推送到远程：`git push` 或 `git push -u origin <branch>`

### 失败处理

如提交失败：
- 检查 pre-commit hooks 错误信息
- 移除或修复不符合规范的内容
- 重新提交（不使用 amend）
