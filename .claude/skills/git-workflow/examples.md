# Git工作流示例（Git Workflow Examples）

本文档提供 Git 工作流的详细示例，包括三种主流工作流模式、最佳实践和冲突处理。

## 工作流模式

### 1. GitHub Flow（推荐）

**适用场景**：持续部署、小团队、快速迭代

**流程图**：
```
main ─────●─────●─────●─────●────→
           ↖   ↗ ↖   ↗
feature     ●─●   ●─●
```

**详细流程**：

1. **从 main 创建功能分支**：
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/user-authentication
   ```

2. **开发并提交**：
   ```bash
   git add src/auth/
   git commit -m "feat(auth): add JWT authentication"
   ```

3. **推送到远程并创建 PR**：
   ```bash
   git push origin feature/user-authentication
   gh pr create --title "Add JWT authentication" --body "Implements #123"
   ```

4. **代码审查**：
   - 团队成员审查代码
   - CI/CD 自动运行测试
   - 修改代码并推送更新

5. **合并到 main**：
   ```bash
   # Squash merge（推荐）
   gh pr merge --squash
   ```

6. **自动部署**：
   - CI/CD 自动部署到生产环境

**优点**：
- 流程简单，易于理解
- 适合持续部署（CD）
- 分支生命周期短，冲突少

**缺点**：
- 不适合多版本维护
- 生产环境直接基于 main 分支

### 2. Git Flow

**适用场景**：定期发布、多版本维护、大型项目

**流程图**：
```
main ────●───────────●────────→ (生产)
          ↖         ↗
release    ●───────●
            ↖     ↗
develop ─────●─●─●─●─●────→ (开发)
              ↖ ↗ ↖ ↗
feature        ● ●   ● ●
```

**详细流程**：

1. **从 develop 创建功能分支**：
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/payment-integration
   ```

2. **开发完成后合并回 develop**：
   ```bash
   git checkout develop
   git merge --no-ff feature/payment-integration
   git push origin develop
   git branch -d feature/payment-integration
   ```

3. **创建发布分支**：
   ```bash
   git checkout -b release/1.2.0 develop
   # 更新版本号
   echo "1.2.0" > VERSION
   git commit -m "chore(release): bump to 1.2.0"
   ```

4. **发布分支合并到 main 和 develop**：
   ```bash
   # 合并到 main
   git checkout main
   git merge --no-ff release/1.2.0
   git tag -a v1.2.0 -m "Release 1.2.0"

   # 合并到 develop
   git checkout develop
   git merge --no-ff release/1.2.0

   # 删除发布分支
   git branch -d release/1.2.0

   # 推送到远程
   git push origin main develop --tags
   ```

5. **Hotfix 流程**（紧急修复）：
   ```bash
   # 从 main 创建 hotfix 分支
   git checkout -b hotfix/1.2.1 main

   # 修复并提交
   git commit -m "fix: critical security issue"

   # 合并到 main 和 develop
   git checkout main
   git merge --no-ff hotfix/1.2.1
   git tag -a v1.2.1 -m "Hotfix 1.2.1"

   git checkout develop
   git merge --no-ff hotfix/1.2.1

   git branch -d hotfix/1.2.1
   ```

**优点**：
- 适合定期发布（每月/每季度）
- 支持多版本维护（hotfix）
- 生产环境稳定（main 分支）

**缺点**：
- 流程复杂，学习成本高
- 分支管理开销大

### 3. Trunk-Based Development

**适用场景**：高频部署、强依赖自动化测试、小团队

**流程图**：
```
main ─●─●─●─●─●─●─●─●─●─●→
       ↖↗ ↖↗ ↖↗
feature ● ● ●  (短期分支，<1天)
```

**详细流程**：

1. **从 main 创建短期分支**（几小时到1天）：
   ```bash
   git checkout -b feature/fix-login-bug main
   ```

2. **快速开发并合并**：
   ```bash
   # 开发（几小时内完成）
   git commit -m "fix: login timeout issue"

   # 立即推送并合并
   git push origin feature/fix-login-bug
   gh pr create --title "Fix login timeout" --body "Fixes #456"
   gh pr merge --squash
   ```

3. **使用 Feature Flag 控制功能发布**：
   ```python
   # 代码中使用 Feature Flag
   if feature_flags.is_enabled('new_payment_flow'):
       # 新功能代码
       process_payment_v2()
   else:
       # 旧功能代码
       process_payment_v1()
   ```

4. **高频部署**（每天多次）：
   - 每次合并到 main 自动部署
   - Feature Flag 控制功能上线

**优点**：
- 高频部署（每天多次）
- 流程简单，分支少
- 强制小步快跑

**缺点**：
- 需要强大的自动化测试
- 需要 Feature Flag 系统
- 对团队要求高

## 最佳实践

### Commit 最佳实践

#### 1. 原子性提交

**好的示例**：
```bash
git commit -m "feat(auth): add JWT token generation"
git commit -m "feat(auth): add JWT token validation"
git commit -m "test(auth): add JWT tests"
```

**不好的示例**：
```bash
git commit -m "feat: add auth, fix bugs, update docs"
```

#### 2. 有意义的消息

**好的示例**：
```bash
git commit -m "fix(payment): handle Stripe API timeout

- Add 5s timeout to Stripe API calls
- Retry 3 times with exponential backoff
- Log error details for debugging

Closes #789"
```

**不好的示例**：
```bash
git commit -m "fix bug"
git commit -m "update code"
```

### 分支最佳实践

#### 1. 分支命名规范

**功能分支**：
- `feature/user-authentication`
- `feature/123-add-payment` (带 Issue 编号)

**修复分支**：
- `bugfix/login-timeout`
- `hotfix/security-vulnerability`

**发布分支**（Git Flow）：
- `release/1.2.0`

**不好的示例**：
- `myfeature`
- `test`
- `temp`

#### 2. 分支保护规则

**main/master 分支**：
```json
{
  "protection": {
    "required_pull_request_reviews": {
      "required_approving_review_count": 1
    },
    "required_status_checks": {
      "strict": true,
      "contexts": ["ci/test", "ci/lint"]
    },
    "enforce_admins": true,
    "required_linear_history": true
  }
}
```

### PR 最佳实践

#### 1. PR 模板示例

```markdown
## 变更说明
实现JWT认证功能，包括token生成、验证和刷新。

## 变更类型
- [x] 新功能
- [ ] Bug修复
- [ ] 重构
- [ ] 文档更新

## 测试计划
- [x] 单元测试通过（覆盖率：92%）
- [x] 集成测试通过
- [x] 手动测试完成（登录、登出、token刷新）

## 相关Issue
Closes #123

## 截图
![login-flow](./screenshots/login.png)

## 检查清单
- [x] 代码符合项目规范
- [x] 测试覆盖率≥80%
- [x] 文档已更新
- [x] 无安全漏洞
- [x] 性能测试通过
```

#### 2. 代码审查清单

**功能性**：
- [ ] 功能是否符合需求
- [ ] 边界情况是否处理
- [ ] 错误处理是否完善

**代码质量**：
- [ ] 命名是否清晰
- [ ] 逻辑是否简洁
- [ ] 是否有重复代码

**测试**：
- [ ] 测试覆盖率是否≥80%
- [ ] 测试用例是否完整
- [ ] 是否有集成测试

**安全**：
- [ ] 输入验证是否完善
- [ ] 是否有SQL注入风险
- [ ] 敏感信息是否加密

### 冲突处理示例

#### 场景1：合并冲突（Merge Conflict）

**情况**：功能分支与 main 分支都修改了同一文件

**解决方案1：Rebase（推荐）**
```bash
# 1. 拉取最新代码
git checkout main
git pull origin main

# 2. 切换到功能分支
git checkout feature/my-feature

# 3. 变基到最新main
git rebase main

# 4. 解决冲突
# 编辑冲突文件，保留需要的变更
# Git 会标记冲突：
# <<<<<<< HEAD
# 你的变更
# =======
# main 分支的变更
# >>>>>>> main

# 5. 标记冲突已解决
git add <冲突文件>
git rebase --continue

# 6. 强制推送（仅在功能分支）
git push --force-with-lease
```

**解决方案2：Merge**
```bash
# 1. 拉取最新代码
git checkout main
git pull origin main

# 2. 切换到功能分支并合并
git checkout feature/my-feature
git merge main

# 3. 解决冲突
# 编辑冲突文件

# 4. 提交合并
git add <冲突文件>
git commit -m "merge: resolve conflicts with main"

# 5. 推送
git push origin feature/my-feature
```

#### 场景2：回滚错误提交

**情况**：已推送到远程的提交有错误，需要回滚

**解决方案1：Revert（推荐，安全）**
```bash
# 创建新提交撤销错误提交
git revert <commit-hash>
git push origin main
```

**解决方案2：Reset（慎用）**
```bash
# 仅用于未推送的提交
git reset --hard HEAD~1

# 如果已推送，需要强制推送（危险！）
git push --force-with-lease origin main
```

#### 场景3：Cherry-pick 特定提交

**情况**：只需要另一个分支的某些提交

**解决方案**：
```bash
# 1. 查看要cherry-pick的提交
git log feature/other-branch

# 2. Cherry-pick 特定提交
git checkout main
git cherry-pick <commit-hash>

# 3. 解决冲突（如有）
git add <冲突文件>
git cherry-pick --continue

# 4. 推送
git push origin main
```

## 版本发布最佳实践

### SemVer 版本号示例

**格式**：`MAJOR.MINOR.PATCH`

**示例**：
- `1.0.0` → `1.0.1`：Bug修复（PATCH）
- `1.0.1` → `1.1.0`：新功能（MINOR）
- `1.1.0` → `2.0.0`：破坏性变更（MAJOR）

**预发布版本**：
- `1.0.0-alpha.1`：Alpha版本
- `1.0.0-beta.2`：Beta版本
- `1.0.0-rc.1`：Release Candidate

### CHANGELOG.md 示例

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- New feature in development

## [1.2.0] - 2026-03-20
### Added
- JWT authentication (#123)
- User profile management (#124)
- Password reset via email (#125)

### Fixed
- Login timeout issue (#126)
- Session expiration bug (#127)

### Changed
- Updated API response format (#128)
- Improved error messages (#129)

### Deprecated
- Old authentication endpoint `/auth/login` (use `/api/v1/auth/login`)

### Removed
- Unused legacy code

### Security
- Fixed SQL injection vulnerability (#130)

## [1.1.0] - 2026-02-15
### Added
- User registration (#100)

## [1.0.0] - 2026-01-01
### Added
- Initial release
```

## 工具集成示例

### GitHub Actions 工作流

```yaml
name: CI/CD

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: npm test
      - name: Check coverage
        run: npm run coverage

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        run: ./deploy.sh
```

### Git Aliases

```bash
# ~/.gitconfig
[alias]
    # 简化命令
    co = checkout
    br = branch
    ci = commit
    st = status

    # 美化日志
    lg = log --graph --oneline --decorate --all

    # 撤销最后一次提交（保留变更）
    undo = reset HEAD~1 --mixed

    # 快速修改最后一次提交
    amend = commit --amend --no-edit

    # 查看文件变更统计
    stat = diff --stat
```
