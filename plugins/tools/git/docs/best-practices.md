# 最佳实践

Git 插件的最佳实践和建议。

## 工作流

### 功能开发流程

```bash
# 1. 创建功能分支
git checkout -b feature/user-auth

# 2. 开发并提交
git add src/auth/
/commit "feat: 添加用户注册"

# 3. 推送分支
git push -u origin feature/user-auth

# 4. 创建 PR
/create-pr

# 5. 根据反馈修改
vim src/auth/login.py
git add src/auth/login.py
/commit "fix: 修复登录验证逻辑"

# 6. 推送更新
git push

# 7. 更新 PR
/update-pr 123
```

### Bug 修复流程

```bash
# 1. 创建修复分支
git checkout -b fix/login-timeout

# 2. 修复并提交
git add .
/commit "fix: 修复登录超时问题"

# 3. 推送并创建 PR
git push -u origin fix/login-timeout
/create-pr
```

## 提交规范

### 提交粒度

**推荐**：

- 一个提交做一件事
- 变更范围适中（< 500 行）
- 提交信息清晰

**避免**：

- 一个提交包含多个不相关变更
- 变更范围过大（> 1000 行）
- 提交信息模糊

### 提交信息

**好的提交信息**：

```
feat: 添加用户认证功能

- 实现登录/注册
- 添加 JWT 支持
- 添加单元测试

Closes #123
```

**不好的提交信息**：

```
update
fix bug
done
```

## PR 规范

### PR 粒度

**推荐**：

- 变更范围合理（< 1000 行）
- 单一目的
- 易于审查

**避免**：

- 变更范围过大
- 多个不相关变更
- 难以审查

### PR 描述

**必须包含**：

- Summary：简要描述
- Changes：变更列表
- Test Plan：测试计划

**推荐包含**：

- Screenshots：截图
- Related Issues：关联 Issue

## 分支策略

### 分支命名

| 类型 | 格式 | 示例 |
|------|------|------|
| 功能 | `feature/<name>` | `feature/user-auth` |
| 修复 | `fix/<name>` | `fix/login-timeout` |
| 发布 | `release/<version>` | `release/1.0.0` |
| 热修复 | `hotfix/<name>` | `hotfix/security-patch` |

### 分支保护

**主分支**：

- 禁止直接推送
- 必须通过 PR 合并
- 需要 Code Review

**开发分支**：

- 允许直接推送
- 定期合并主分支
- 保持代码最新

## 安全协议

### 必须遵守

- ✅ 遵循 Git 最佳实践
- ✅ 提交前检查敏感信息
- ✅ 使用 .gitignore 忽略敏感文件
- ✅ 定期更新依赖

### 禁止行为

- ❌ 使用 `--force` 推送
- ❌ 使用 `--no-verify` 跳过 hooks
- ❌ 提交敏感信息
- ❌ 提交大文件（> 10MB）

## 常见问题

### 撤销最后一次提交

```bash
# 保留变更
git reset --soft HEAD~1

# 丢弃变更
git reset --hard HEAD~1
```

### 修改最后一次提交信息

```bash
git commit --amend -m "新的提交信息"
```

### 解决合并冲突

```bash
# 1. 查看冲突文件
git status

# 2. 编辑冲突文件
vim <conflicted-file>

# 3. 标记为已解决
git add <conflicted-file>

# 4. 完成合并
git commit
```

### 回退到特定版本

```bash
# 查看历史
git log --oneline

# 回退（保留变更）
git reset --soft <commit-hash>

# 回退（丢弃变更）
git reset --hard <commit-hash>
```
