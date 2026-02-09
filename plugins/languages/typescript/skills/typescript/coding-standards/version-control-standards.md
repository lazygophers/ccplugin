# TypeScript 版本控制规范

## 核心原则

### ✅ 必须遵守

1. **语义化版本** - 遵循 Semantic Versioning 2.0.0
2. **约定式提交** - 使用 Conventional Commits 规范
3. **分支策略** - 使用 Git Flow 或 GitHub Flow
4. **变更日志** - 维护 CHANGELOG.md
5. **发布说明** - 每次发布包含变更说明

### ❌ 禁止行为

- 直接提交到 main/master 分支
- 推送包含敏感信息的代码
- 不写提交信息
- 提交编译不通过的代码

## 提交规范

### 约定式提交格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 提交类型

| 类型 | 描述 | 示例 |
|------|------|------|
| `feat` | 新功能 | feat(auth): add OAuth login support |
| `fix` | 修复 bug | fix(api): handle empty response correctly |
| `docs` | 文档变更 | docs(readme): update installation instructions |
| `style` | 代码格式（不影响功能） | style: format code with prettier |
| `refactor` | 重构（不是新功能也不是修复） | refactor(auth): extract validation logic |
| `perf` | 性能优化 | perf(cache): implement memoization |
| `test` | 测试相关 | test(user): add unit tests for getUser |
| `chore` | 构建/工具相关 | chore(deps): upgrade typescript to 5.9 |
| `ci` | CI/CD 相关 | ci(github): add workflow for deploy |
| `revert` | 回退提交 | revert: feat(api): add new endpoint |

### 提交示例

```bash
# ✅ 正确 - 功能提交
git commit -m "feat(auth): add JWT token refresh"

# ✅ 正确 - 修复提交
git commit -m "fix(button): prevent multiple clicks during loading"

# ✅ 正确 - 带详细说明的提交
git commit -m "feat(api): implement rate limiting

- Add rate limiting middleware
- Configure limits per endpoint
- Add X-RateLimit headers to responses

Closes #123"

# ✅ 正确 - 破坏性变更
git commit -m "feat(user)!: change userId type from string to number

BREAKING CHANGE: userId is now a number instead of string.
Update all API calls accordingly."

# ❌ 错误 - 不规范的提交
git commit -m "update"
git commit -m "fix bug"
git commit -m "add stuff"
```

## 分支策略

### Git Flow

```
main          ──────●────────────────────────────●──────
                   │                            │
                   │ v1.0.0                    │ v1.1.0
                   │                            │
develop       ●────●────────────●────────────●──●───────
               │                │            │
feature/auth  ──●────────────────●            │
               │  完成后合并到 develop          │
feature/user  ────────────────────────●───────●───────
                                        │
                                        │  完成后合并到 develop
release/1.1.0  ─────────────────────────────────────●───
                                             │  发布后合并到 main 和 develop
```

### 分支命名

```bash
# 功能分支
feature/功能名称
feature/user-authentication
feature/add-payment

# 修复分支
fix/问题描述
fix/login-redirect
fix/memory-leak

# 发布分支
release/版本号
release/1.2.0
release/2.0.0

# 热修复分支
hotfix/版本号-问题描述
hotfix/1.2.1-critical-bug
```

### 工作流程

```bash
# 1. 从 develop 创建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/add-payment

# 2. 开发并提交
git add .
git commit -m "feat(payment): add stripe integration"

# 3. 推送到远程
git push -u origin feature/add-payment

# 4. 创建 Pull Request 到 develop

# 5. 代码审查通过后合并

# 6. 删除功能分支
git branch -d feature/add-payment
```

## Pull Request 规范

### PR 标题格式

```markdown
feat(auth): add OAuth login support

fix(api): handle rate limiting errors

docs(readme): update installation guide

chore(deps): upgrade to React 19
```

### PR 描述模板

```markdown
## 变更类型
- [ ] feat: 新功能
- [ ] fix: 修复 bug
- [ ] docs: 文档变更
- [ ] style: 代码格式
- [ ] refactor: 重构
- [ ] perf: 性能优化
- [ ] test: 测试相关
- [ ] chore: 构建/工具相关

## 变更描述
简要描述本 PR 的变更内容。

## 相关 Issue
Closes #123
Related to #456

## 变更截图
如果有 UI 变更，请添加截图。

## 测试
描述如何测试这些变更：
- [ ] 单元测试通过
- [ ] 手动测试通过
- [ ] 添加了新的测试用例

## 检查清单
- [ ] 代码符合项目规范
- [ ] 添加了必要的文档
- [ ] 所有测试通过
- [ ] 没有引入新的警告
```

## 版本管理

### 语义化版本

```
主版本号.次版本号.修订号 (MAJOR.MINOR.PATCH)

例：1.2.3
- MAJOR (1): 不兼容的 API 变更
- MINOR (2): 向下兼容的功能性新增
- PATCH (3): 向下兼容的问题修正
```

### 版本变更规则

| 变更类型 | 版本变化 | 示例 |
|---------|---------|------|
| 破坏性变更 | MAJOR | 1.2.3 → 2.0.0 |
| 新功能 | MINOR | 1.2.3 → 1.3.0 |
| 问题修复 | PATCH | 1.2.3 → 1.2.4 |
| 文档变更 | 不变 | - |
| 代码格式 | 不变 | - |

### package.json 版本

```json
{
  "name": "@workspace/ui",
  "version": "1.2.3",
  "dependencies": {
    "react": "^18.3.0",
    "zod": "~3.23.0"
  }
}
```

## 发布流程

### 准备发布

```bash
# 1. 确保在正确的分支
git checkout main
git pull origin main

# 2. 运行测试
pnpm test
pnpm typecheck
pnpm lint

# 3. 运行构建
pnpm build

# 4. 更新版本号
pnpm version major  # 2.0.0
pnpm version minor  # 1.3.0
pnpm version patch  # 1.2.4

# 5. 生成 CHANGELOG（使用 conventional-changelog）
pnpm changelog

# 6. 提交变更
git add .
git commit -m "chore(release): 1.2.4"

# 7. 创建 Git 标签
git tag v1.2.4

# 8. 推送
git push origin main
git push origin v1.2.4

# 9. 发布到 npm（如果需要）
pnpm publish
```

## .gitignore 规范

### 标准 .gitignore

```gitignore
# Dependencies
node_modules/
.pnp
.pnp.js

# Build outputs
dist/
build/
.next/
out/

# Environment files
.env
.env.local
.env.*.local
!.env.example

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Testing
coverage/
.nyc_output/

# Logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*

# Misc
.turbo/
.vitest/
```

## 检查清单

提交代码前，确保：

- [ ] 提交信息符合约定式提交规范
- [ ] `pnpm typecheck` 通过
- [ ] `pnpm lint` 通过
- [ ] `pnpm test` 通过
- [ ] 没有敏感信息（密钥、密码等）
- [ ] `pnpm build` 成功
- [ ] 更新了相关文档

发布版本前，确保：

- [ ] 更新了 CHANGELOG.md
- [ ] 更新了版本号（语义化版本）
- [ ] 创建了 Git 标签
- [ ] 推送了标签到远程
- [ ] 发布说明已准备好
