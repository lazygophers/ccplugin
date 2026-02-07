# Golang 版本控制规范

## 核心原则

### ✅ 必须遵守

1. **Git 工作流** - 使用 Git Flow 或 GitHub Flow 工作流
2. **分支命名** - 分支名称清晰表达意图
3. **提交信息** - 提交信息清晰描述变更
4. **代码审查** - 所有代码变更必须经过审查
5. **版本标签** - 使用语义化版本号

### ❌ 禁止行为

- 直接提交到主分支
- 提交信息不清晰
- 跳过代码审查
- 不使用版本标签
- 提交编译错误或测试失败的代码

## Git 工作流

### GitHub Flow

```
main (主分支)
    ↑
    │
feature/user-login (功能分支)
```

**流程**：

1. 从 main 分支创建功能分支
2. 在功能分支上开发
3. 提交代码并创建 Pull Request
4. 代码审查通过后合并到 main
5. 删除功能分支

### Git Flow

```
main (主分支)
    ↑
    │
develop (开发分支)
    ↑
    │
feature/user-login (功能分支)
```

**流程**：

1. 从 develop 分支创建功能分支
2. 在功能分支上开发
3. 提交代码并创建 Pull Request 到 develop
4. 代码审查通过后合并到 develop
5. 从 develop 创建 release 分支
6. 测试通过后合并到 main 和 develop
7. 从 main 创建标签

## 分支命名

### 功能分支

```bash
# ✅ 正确 - 清晰的功能分支命名
git checkout -b feature/user-login
git checkout -b feature/add-friend-api
git checkout -b feature/improve-performance

# ❌ 错误 - 不清晰的分支命名
git checkout -b feature1
git checkout -b new-feature
git checkout -b test
```

### 修复分支

```bash
# ✅ 正确 - 清晰的修复分支命名
git checkout -b fix/login-error
git checkout -b fix/memory-leak
git checkout -b hotfix/security-issue

# ❌ 错误 - 不清晰的分支命名
git checkout -b fix1
git checkout -b bugfix
```

### 发布分支

```bash
# ✅ 正确 - 清晰的发布分支命名
git checkout -b release/v1.0.0
git checkout -b release/v2.1.0

# ❌ 错误 - 不清晰的分支命名
git checkout -b release
git checkout -b v1.0.0
```

## 提交信息

### 提交信息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 提交类型

| 类型   | 说明     | 示例                     |
| ------ | -------- | ------------------------ |
| feat   | 新功能   | feat(user): 添加用户登录   |
| fix    | 修复     | fix(auth): 修复认证错误     |
| docs   | 文档     | docs(readme): 更新 README   |
| style  | 格式     | style(format): 格式化代码   |
| refactor | 重构   | refactor(api): 重构 API    |
| test   | 测试     | test(user): 添加用户测试   |
| chore  | 构建/工具 | chore(deps): 更新依赖      |

### 提交信息示例

```bash
# ✅ 正确 - 清晰的提交信息
git commit -m "feat(user): 添加用户登录功能

实现用户登录接口，支持用户名和密码验证。

- 添加 UserLogin 函数
- 添加密码验证逻辑
- 添加登录测试
"

git commit -m "fix(auth): 修复认证中间件错误

修复认证中间件在处理无效令牌时的错误。
"

git commit -m "docs(readme): 更新快速开始指南

更新 README.md 中的快速开始部分，添加更多示例。
"

# ❌ 错误 - 不清晰的提交信息
git commit -m "update"
git commit -m "fix bug"
git commit -m "add feature"
```

## Pull Request

### PR 标题

```markdown
# ✅ 正确 - 清晰的 PR 标题
feat(user): 添加用户登录功能
fix(auth): 修复认证中间件错误
docs(readme): 更新快速开始指南

# ❌ 错误 - 不清晰的 PR 标题
update
fix bug
add feature
```

### PR 描述

```markdown
# ✅ 正确 - 完整的 PR 描述
## 变更说明

添加用户登录功能，支持用户名和密码验证。

## 变更内容

- 添加 UserLogin 函数
- 添加密码验证逻辑
- 添加登录测试
- 更新 API 文档

## 测试

- [x] 单元测试通过
- [x] 集成测试通过
- [x] 手动测试通过

## 截图

（如果有 UI 变更，添加截图）

## 相关 Issue

Closes #123

# ❌ 错误 - 不完整的 PR 描述
添加用户登录功能。
```

### PR 审查清单

```markdown
## 审查清单

- [ ] 代码符合编码规范
- [ ] 测试覆盖充分
- [ ] 文档已更新
- [ ] 无编译错误
- [ ] 无测试失败
- [ ] 提交信息清晰
- [ ] 变更范围合理
```

## 版本标签

### 语义化版本

```
MAJOR.MINOR.PATCH

MAJOR：不兼容的 API 变更
MINOR：向后兼容的功能性新增
PATCH：向后兼容的问题修正
```

### 版本标签示例

```bash
# ✅ 正确 - 语义化版本标签
git tag -a v1.0.0 -m "首次发布"
git tag -a v1.1.0 -m "添加用户登录功能"
git tag -a v1.1.1 -m "修复登录错误"

# ❌ 错误 - 不规范的版本标签
git tag -a 1.0.0 -m "首次发布"
git tag -a v1 -m "首次发布"
git tag -a release -m "首次发布"
```

### 发布流程

```bash
# 1. 创建发布分支
git checkout -b release/v1.0.0

# 2. 更新版本号
# 更新 go.mod 中的版本号

# 3. 运行测试
go test -v ./...

# 4. 合并到 main
git checkout main
git merge release/v1.0.0

# 5. 创建标签
git tag -a v1.0.0 -m "首次发布"

# 6. 推送标签
git push origin v1.0.0

# 7. 合并到 develop（如果使用 Git Flow）
git checkout develop
git merge release/v1.0.0

# 8. 删除发布分支
git branch -d release/v1.0.0
```

## 检查清单

提交代码前，确保：

- [ ] 使用正确的分支命名
- [ ] 提交信息清晰描述变更
- [ ] 提交信息符合格式规范
- [ ] 代码已通过测试
- [ ] 代码已通过代码审查
- [ ] 文档已更新
- [ ] 无编译错误
- [ ] 无测试失败
- [ ] 使用语义化版本号
- [ ] 创建版本标签
