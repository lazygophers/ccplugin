# PR 规范指南

## PR 命令使用

### 创建 PR

```bash
gh pr create
```

**功能**：

- 创建 Pull Request
- 支持通过 `--title` 和 `--body` 参数指定标题和描述
- 返回 PR URL

**前提条件**：

- 分支已推送到远程
- 有相对于基准分支的变更
- 已安装 GitHub CLI (gh)

**生成的 PR 信息**：

```markdown
## Summary

- 功能点 1
- 功能点 2

## Changes

- 提交 1: 简短描述
- 提交 2: 简短描述

## Test plan

- [ ] 单元测试通过
- [ ] 集成测试通过
```

### 更新 PR

```bash
gh pr edit <pr-number>
```

**功能**：

- 更新 PR 标题和描述
- 使用 `--title` 和 `--body` 参数更新内容

**使用场景**：

- 添加新功能后更新 PR
- 修复审查反馈后更新 PR
- 补充测试后更新 PR

**注意事项**：

- 需要提供 PR 编号
- 仅更新标题和描述
- 保留现有评论和审查

## PR 质量标准

### ✅ 好的 PR

- 变更范围合理（< 1000 行）
- 描述完整（Summary、Changes、Test plan）
- 包含测试
- 提交信息清晰具体
- 遵循 Conventional Commits 规范

### ❌ 不好的 PR

- 变更范围过大（> 1000 行）
- 描述不完整或不清晰
- 缺少测试
- 提交信息模糊不具体
- 包含无关的变更

## PR 编写最佳实践

### 1. PR 描述结构

**建议格式**：

```markdown
## Summary（必需）

清晰简洁地说明这个 PR 的目标和主要变更，用 1-3 句话说明。

## Changes（必需）

- 主要变更 1: 简短描述
- 主要变更 2: 简短描述
- 主要变更 3: 简短描述

## Test plan（必需）

- [ ] 单元测试通过
- [ ] 集成测试通过
- [ ] 手动测试已验证

## Related issues（可选）

Closes #123
```

### 2. 变更范围控制

✅ **合理的 PR 范围**：

- 单一功能或缺陷修复
- 变更范围 < 1000 行
- 可以在 30 分钟内审查完成
- 提交数量 3-8 个

❌ **过大的 PR**：

- 一个 PR 包含多个功能
- 变更范围 > 1000 行
- 审查时间 > 1 小时
- 提交数量 > 20 个

### 3. 测试要求

**每个 PR 必须包含**：

- 新增功能的单元测试
- 相关功能的集成测试（如适用）
- 手动测试验证结果
- 测试通过截图或日志（如需要）

### 4. 文档更新

**如果 PR 涉及以下内容，需要更新文档**：

- 新增 API 或命令
- 行为变更
- 配置变更
- 新增或移除功能

### 5. 审查周期

**标准审查周期**：

1. 提交 PR → 自动检查
2. 代码审查 → 通常 24 小时内
3. 修改反馈 → 提供新提交
4. 最终审批 → 合并到主分支

## PR 常见问题

**Q: 多少行代码的变更算是"过大的 PR"？**
A: 通常认为 > 1000 行是过大的 PR。建议将大功能拆分成多个 PR，每个 PR 聚焦于一个功能或模块。

**Q: PR 中有多少个提交是合理的？**
A: 通常 3-8 个提交是合理的。每个提交应该对应一个独立的功能或缺陷修复。如果超过 10 个提交，说明可能需要整理提交历史。

**Q: 如何处理 PR 审查中的反馈？**
A:

1. 理解反馈意见
2. 修改代码
3. 创建新提交（不要 amend 已推送的提交）
4. 推送新提交
5. 使用 `pr update` 命令更新 PR 描述

**Q: PR 被拒绝了怎么办？**
A:

1. 了解拒绝原因
2. 创建新分支（不要在原分支继续修改）
3. 修改代码
4. 创建新 PR

**Q: PR 中的提交信息不符合规范怎么办？**
A: 创建新 PR 前，确保所有提交遵循 Conventional Commits 规范。如果已提交，不要 amend（会改写历史），而应创建新提交修复。

## PR 工作流示例

### 完整 PR 工作流

```bash
# 1. 创建功能分支
gitcheckout -b feature/user-auth

# 2. 开发功能
# ... 编写代码 ...

# 3. 分批提交
gitadd src/auth/register.py
gitcommit -m "feat: 添加用户注册功能"

gitadd tests/test_auth.py
gitcommit -m "test: 添加认证测试"

# 4. 推送到远程
gitpush -u origin feature/user-auth

# 5. 创建 PR
gh pr create --title "feat: 添加用户认证功能" --body "实现用户注册、登录和会话管理"

# 6. 根据审查反馈修改
vim src/auth/login.py
gitadd src/auth/login.py
gitcommit -m "fix: 修复登录验证逻辑"

# 7. 推送修改
gitpush

# 8. 更新 PR（如需更新描述）
gh pr edit 123 --body "更新后的 PR 描述"
```

## PR 创建失败处理

### 错误排查

```bash
# 错误：分支未推送
# 解决：先执行 gitpush
gitpush -u origin feature/branch-name

# 错误：gh 未安装
# 解决：安装 GitHub CLI
# macOS: brew install gh
# Linux: apt install gh
# Windows: choco install gh

# 错误：gh 未认证
# 解决：使用 gh auth login 登录
gh auth login

# 错误：PR 已存在
# 解决：使用 gh pr edit 命令更新现有 PR
gh pr edit <pr-number>

# 错误：无相对于基准分支的变更
# 解决：确保当前分支有相对于基准分支（通常是 master/main）的新提交
```

### 常见解决方案

**问题：分支落后于主分支**

```bash
# 解决：更新分支
gitfetch origin
gitrebase origin/master
gitpush --force-with-lease  # 仅当确定无人基于此分支工作时使用
```

**问题：PR 与其他 PR 冲突**

```bash
# 解决：解决冲突后创建新 PR
gitmerge origin/master
# ... 解决冲突 ...
gitadd .
gitcommit -m "fix: 解决合并冲突"
gitpush
```

**问题：需要修改已合并的 PR**

```bash
# 解决：创建新 PR 修复
gitcheckout master
gitpull origin master
gitcheckout -b fix/previous-issue
# ... 修改代码 ...
gitadd .
gitcommit -m "fix: 修复之前 PR 中的问题"
gitpush -u origin fix/previous-issue
gh pr create --title "fix: 修复之前 PR 中的问题" --body "描述修复内容"
```

## 参考资源

- [Pull Request 最佳实践](https://github.blog/2015-01-21-how-to-write-the-perfect-pull-request/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [Conventional Commits](https://www.conventionalcommits.org/)
