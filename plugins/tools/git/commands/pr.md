---
description: 准备 Pull Request - 基于分支变更自动生成 PR 标题和描述
argument-hint: [--update <pr-number>]
allowed-tools: Bash(git:*, gh*)
model: sonnet
---

# pr

## 命令描述

基于当前分支相对于基准分支的所有变更，智能分析并生成高质量的 Pull Request 标题和描述。支持创建新 PR 和更新已有 PR。

## 工作流描述

1. **分析分支变更**：获取当前分支相对于基准分支（main/master）的所有提交和文件变更
2. **提取关键信息**：从提交信息中提取功能、修复、重构等核心内容
3. **生成 PR 信息**：生成符合规范的 PR 标题和描述
4. **创建/更新 PR**：通过 GitHub CLI 创建新 PR 或更新现有 PR

## 命令执行方式

### 使用方法

```bash
# 创建新 PR
gh pr create

# 更新现有 PR
gh pr edit <pr-number>
```

### 执行时机

- 完成功能开发，需要创建 Pull Request
- 根据 Code Review 反馈修改代码，需要更新 PR 描述
- PR 中添加了新功能或修复，需要同步描述

### 执行参数

| 参数                   | 说明                  | 类型 | 默认值 |
| ---------------------- | --------------------- | ---- | ------ |
| `--update <pr-number>` | 更新指定的 PR（可选） | int  | -      |

### 命令说明

- 创建 PR：分析分支变更，生成标题和描述，通过 gh cli 创建
- 更新 PR：重新分析分支变更，更新 PR 标题和描述
- 支持多个提交的自动汇总
- 自动生成测试计划检查清单

## 相关Skills（可选）

参考 Git 操作技能：`@${CLAUDE_PLUGIN_ROOT}/skills/git/SKILL.md`

## 依赖脚本

```bash
# 使用 GitHub CLI (gh) 原生命令
```

## 示例

### 创建新 PR

```bash
# 推送分支到远程
gitpush -u origin feature/user-auth

# 创建 PR（需手动指定标题和描述）
gh pr create --title "feat: 添加用户认证" --body "实现用户注册、登录和会话管理"
```

### 更新 PR

```bash
# 修改代码后提交
gitadd src/auth/
gitcommit -m "fix: 修复登录验证"
gitpush

# 更新 PR 信息
gh pr edit 123 --body "更新后的 PR 描述"
```

### PR 信息示例

生成的 PR 会包含以下结构：

```markdown
## 变更摘要

实现用户认证系统，包括用户注册、登录和会话管理。

## 技术实现

- 使用 JWT 进行会话管理
- 实现 bcrypt 密码加密
- 添加请求速率限制

## 测试说明

- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试场景：用户可正常注册和登录

## 相关 Issue

Closes #123
```

## 检查清单

在创建/更新 PR 前，确保满足以下条件：

- [ ] 分支已推送到远程仓库
- [ ] 分支包含相对于基准分支的新提交
- [ ] 已安装 GitHub CLI（gh）
- [ ] 已认证到 GitHub（`gh auth login`）
- [ ] 提交信息符合 Conventional Commits 规范

## 注意事项

**PR 范围**：

- 变更范围应合理（建议 < 1000 行）
- 超大 PR 应分解为多个 PR

**PR 标题**：

- ≤50 字符
- 使用简体中文
- 遵循 Conventional Commits 规范
- 清晰描述变更内容

**PR 描述**：

- **变更摘要**：1-3 句话概述
- **技术实现**：列出关键技术点
- **测试说明**：提供可执行的测试步骤
- **相关 Issue**：链接相关 Issue

**测试计划**：

- 提供明确的测试场景
- 包含边界情况测试
- 说明破坏性变更的迁移步骤

## 其他信息

### PR 标题格式

遵循 Conventional Commits 规范：

```
<type>(<scope>): <description>
```

**示例**：

- `feat(auth): 添加用户登录功能`
- `fix(api): 修复分页查询返回错误`
- `refactor(db): 优化查询性能`
- `docs(readme): 更新安装说明`

### 提交信息最佳实践

- **清晰的提交信息**：每个提交清晰说明改动
- **合理的提交粒度**：单一职责原则
- **完整的提交历史**：保留有意义的提交记录

### 与代码审查配合

1. 创建 PR 并请求审查
2. 等待审查反馈
3. 根据反馈修改代码
4. 使用 `pr --update` 更新 PR 描述
5. 重新请求审查

### 合并 PR

PR 获批后：

- 在 GitHub 上进行 merge 操作
- 或使用 gh cli：`gh pr merge <pr-number> --squash`

### 常见问题

**Q: 如何更新已有 PR？**
A: 修改代码后提交和推送，然后运行 `pr --update <pr-number>`

**Q: PR 变更范围太大怎么办？**
A: 将 PR 分解为多个较小的 PR，每个 PR 只处理一个功能或问题

**Q: 如何处理冲突？**
A: 先 pull 基准分支并解决冲突，然后推送更新
