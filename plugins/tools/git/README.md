# Git 插件

Git 仓库管理插件 - 提供完整的 Git 操作支持，包括提交管理、Pull Request 管理和仓库维护。

## 功能特性

### 📝 提交管理

- **提交所有变更** (`/commit-all`) - 快速提交所有未跟踪和已修改的文件
- **提交暂存区变更** (`/commit`) - 精确控制提交内容，仅提交暂存区文件
- **提交信息规范** - 遵循 Conventional Commits 规范

### 🔀 Pull Request 管理

- **创建 PR** (`/create-pr`) - 基于当前分支变更自动生成 PR 标题和描述
- **更新 PR** (`/update-pr`) - 根据完整变更更新 PR 描述
- **PR 模板** - 标准化的 PR 格式（Summary、Changes、Test plan）

### 🙈 忽略文件管理

- **智能更新** (`/update-ignore`) - 根据未提交内容智能更新 .gitignore
- **自动识别** - 识别临时文件、缓存目录、构建产物等
- **安全检查** - 提交前检查敏感信息

### 👥 子代理

- **git-developer** - Git 开发专家，专注于 Git 操作和工作流
- **git-reviewer** - Git 审查专家，专注于评估提交质量和 PR 完整性

## 安装

```bash
/plugin install ./plugins/git
```

## 快速开始

### 1. 首次提交

```bash
# 更新 .gitignore
/update-ignore

# 提交所有变更
/commit-all "feat: 初始化项目"

# 推送到远程
gitpush -u origin master
```

### 2. 功能开发流程

```bash
# 创建功能分支
gitcheckout -b feature/user-auth

# 开发并提交
gitadd src/auth/
/commit "feat: 添加用户注册"

gitadd tests/
/commit "test: 添加认证测试"

# 推送并创建 PR
gitpush -u origin feature/user-auth
/create-pr
```

### 3. 更新 PR

```bash
# 根据审查反馈修改
vim src/auth/login.py
gitadd src/auth/login.py
/commit "fix: 修复登录验证逻辑"

# 推送并更新 PR
gitpush
/update-pr 123
```

## 命令参考

### /commit-all

提交所有变更，包括未跟踪和已修改的文件。

```bash
/commit-all "提交信息"
```

**使用场景**：快速提交所有变更

### /commit

提交暂存区的变更，不包括未暂存的修改。

```bash
/commit "提交信息"
```

**使用场景**：精确控制提交内容，分批提交

### /update-ignore

根据未提交的文件智能更新 .gitignore。

```bash
/update-ignore
```

**自动识别**：

- 日志文件 (`*.log`)
- 环境变量 (`*.env`)
- 依赖目录 (`node_modules/`, `__pycache__/`)
- 临时文件 (`*.swp`, `.DS_Store`)
- 构建产物 (`dist/`, `build/`)

### /create-pr

基于当前分支的所有变更创建 Pull Request。

```bash
/create-pr
```

**生成内容**：

- PR 标题（基于提交类型）
- PR 描述（Summary、Changes、Test plan）
- 文件变更统计

### /update-pr

基于当前分支相对于基准分支的完整变更更新 Pull Request 描述。

```bash
/update-pr <pr-number>
```

**使用场景**：添加新功能后更新 PR 描述

## 提交信息规范

### Conventional Commits

```
<type>: <subject>

<body>

<footer>
```

### 类型（type）

| 类型       | 说明      | 示例                     |
| ---------- | --------- | ------------------------ |
| `feat`     | 新功能    | feat: 添加用户认证功能   |
| `fix`      | 缺陷修复  | fix: 修复登录超时问题    |
| `docs`     | 文档更新  | docs: 更新 API 文档      |
| `style`    | 代码格式  | style: 统一代码缩进      |
| `refactor` | 代码重构  | refactor: 优化数据库查询 |
| `test`     | 测试相关  | test: 添加单元测试       |
| `chore`    | 构建/工具 | chore: 更新依赖版本      |

### 提交信息示例

```bash
# 好的提交信息
/commit-all "feat: 添加用户认证功能"
/commit-all "fix: 修复登录超时问题"
/commit-all "docs: 更新 API 文档"

# 不好的提交信息
/commit-all "update"
/commit-all "fix bug"
/commit-all "done"
```

## 子代理

### git-developer

Git 开发专家，专注于 Git 仓库操作、提交管理和 Pull Request 工作流。

**适用场景**：

- 复杂的分支操作
- PR 创建和更新
- 提交策略规划

### git-reviewer

Git 审查专家，专注于评估提交质量、PR 完整性和仓库健康度。

**适用场景**：

- 提交质量审查
- PR 完整性检查
- 仓库健康度评估

## 安全协议

- ✅ 遵循 Git 最佳实践
- ✅ 提交前检查敏感信息
- ✅ 避免大文件提交（> 10MB）
- ❌ 不使用 `--force` 推送
- ❌ 不使用 `--no-verify` 跳过 hooks

## 最佳实践

### 1. 提交粒度

✅ **好的提交**（单一职责）：

- "feat: 添加用户注册功能"
- "test: 添加认证测试"

❌ **不好的提交**（过大）：

- "feat: 添加用户模块"（太宽泛）

### 2. PR 质量

✅ **好的 PR**：

- 变更范围合理（< 1000 行）
- 描述完整（Summary、Changes、Test plan）
- 包含测试

❌ **不好的 PR**：

- 变更范围过大
- 描述不完整
- 缺少测试

### 3. 分支策略

✅ **好的分支**：

- `feature/user-auth`
- `fix/login-timeout`

❌ **不好的分支**：

- `stuff`
- `tmp`

## 参考资源

- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [Pull Request 最佳实践](https://github.blog/2015-01-21-how-to-write-the-perfect-pull-request/)

## 许可证

AGPL-3.0-or-later

## 作者

lazygophers <admin@lazygophers.dev>
