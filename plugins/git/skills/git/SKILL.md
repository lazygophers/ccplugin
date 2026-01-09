---
name: git
description: Git 操作技能 - 当用户需要进行 Git 提交、创建 PR、更新 PR 或管理 .gitignore 时自动激活。提供 Git 工作流指导、提交规范和 PR 最佳实践。
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
context: true
agent: ${CLAUDE_PLUGIN_ROOT}/agents/git.md
---

# Git 操作技能

## 核心原则（强制）

⚠️ **必须使用 git 插件进行所有 Git 操作**

**禁止行为**：

- ❌ 直接使用 Bash 命令进行 Git 操作（除非通过插件命令）
- ❌ 跳过 Git 安全协议（force、no-verify 等）
- ❌ 提交包含敏感信息的文件
- ❌ 创建过大的 PR（> 1000 行）

**必须行为**：

- ✅ 所有 Git 操作通过 git 插件命令执行
- ✅ 遵循 Conventional Commits 规范
- ✅ 提交前检查敏感信息
- ✅ 使用清晰、具体的提交信息

## 使用场景

当用户以下情况时，必须使用 git 插件：

### 1. 提交相关

- "提交代码"、"commit"、"提交所有"
- "提交暂存区"、"提交已暂存的"
- "提交这个"、"提交修改"

### 2. PR 相关

- "创建 PR"、"新建 Pull Request"、"create pr"
- "更新 PR"、"更新 PR 描述"、"update pr"
- "PR 内容"、"PR 描述"

### 3. 忽略文件相关

- "更新 .gitignore"、"忽略文件"
- "不要提交这个"、"添加到忽略列表"

### 4. 分支相关

- "创建分支"、"切换分支"
- "合并分支"、"rebase"

## 命令使用

### 提交命令

#### 提交所有变更

```bash
uvx --from git+https://github.com/lazygophers/ccplugin commit-all "feat: 添加用户认证功能"
```

**使用场景**：

- 快速提交所有变更
- 不需要精确控制提交内容
- 确保 .gitignore 配置正确

**注意事项**：

- 提交前会检查敏感信息
- 会添加所有未跟踪和已修改的文件
- 不会自动推送到远程

#### 提交暂存区变更

```bash
uvx --from git+https://github.com/lazygophers/ccplugin commit "fix: 修复登录超时问题"
```

**使用场景**：

- 精确控制提交内容
- 分批提交不同功能的修改
- 仅提交已暂存的文件

**注意事项**：

- 需要先使用 `git add` 添加文件
- 不会影响未暂存的修改
- 适合分阶段提交

### PR 命令

#### 创建 PR

```bash
uvx --from git+https://github.com/lazygophers/ccplugin pr
```

**功能**：

- 分析当前分支相对于基准分支的所有变更
- 自动生成 PR 标题和描述
- 创建 PR 并返回 PR URL

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

#### 更新 PR

```bash
uvx --from git+https://github.com/lazygophers/ccplugin pr update <pr-number>
```

**功能**：

- 分析当前分支相对于基准分支的完整变更
- 重新生成 PR 描述（包含所有新增变更）
- 更新 PR 标题和描述

**使用场景**：

- 添加新功能后更新 PR
- 修复审查反馈后更新 PR
- 补充测试后更新 PR

**注意事项**：

- 需要提供 PR 编号
- 仅更新标题和描述
- 保留现有评论和审查

### 忽略文件命令

#### 更新 .gitignore

```bash
uvx --from git+https://github.com/lazygophers/ccplugin ignore
```

**功能**：

- 分析未提交的文件
- 识别可能不应该追踪的文件类型
- 建议 .gitignore 规则
- 更新 .gitignore 文件

**自动识别的文件类型**：

- `*.log` - 日志文件
- `*.env` - 环境变量文件
- `node_modules/` - Node.js 依赖
- `__pycache__/` - Python 缓存
- `.DS_Store` - macOS 系统文件
- `*.swp` - Vim 临时文件
- `dist/`, `build/` - 构建输出

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
uvx --from git+https://github.com/lazygophers/ccplugin commit-all "feat: 添加用户认证功能"
uvx --from git+https://github.com/lazygophers/ccplugin commit-all "fix: 修复登录超时问题"
uvx --from git+https://github.com/lazygophers/ccplugin commit-all "docs: 更新 API 文档"
uvx --from git+https://github.com/lazygophers/ccplugin commit-all "refactor: 优化数据库查询性能"

# 不好的提交信息
uvx --from git+https://github.com/lazygophers/ccplugin commit-all "update"
uvx --from git+https://github.com/lazygophers/ccplugin commit-all "fix bug"
uvx --from git+https://github.com/lazygophers/ccplugin commit-all "done"
uvx --from git+https://github.com/lazygophers/ccplugin commit-all "tmp"
```

## 工作流程

### 完整开发流程

```bash
# 1. 创建功能分支
git checkout -b feature/user-auth

# 2. 开发并提交
git add src/auth/
uvx --from git+https://github.com/lazygophers/ccplugin commit "feat: 添加用户注册"

git add tests/
uvx --from git+https://github.com/lazygophers/ccplugin commit "test: 添加认证测试"

# 3. 推送到远程
git push -u origin feature/user-auth

# 4. 创建 PR
uvx --from git+https://github.com/lazygophers/ccplugin pr

# 5. 根据审查反馈修改
vim src/auth/login.py
git add src/auth/login.py
uvx --from git+https://github.com/lazygophers/ccplugin commit "fix: 修复登录验证逻辑"

# 6. 更新 PR
git push
uvx --from git+https://github.com/lazygophers/ccplugin pr update 123
```

### 快速提交流程

```bash
# 1. 更新 .gitignore
uvx --from git+https://github.com/lazygophers/ccplugin ignore

# 2. 提交所有变更
uvx --from git+https://github.com/lazygophers/ccplugin commit-all "feat: 初始化项目"

# 3. 推送到远程
git push
```

### 分批提交流程

```bash
# 1. 添加并提交第一个功能
git add feature1.py
uvx --from git+https://github.com/lazygophers/ccplugin commit "feat: 添加功能1"

# 2. 添加并提交第二个功能
git add feature2.py
uvx --from git+https://github.com/lazygophers/ccplugin commit "feat: 添加功能2"

# 3. 推送并创建 PR
git push
uvx --from git+https://github.com/lazygophers/ccplugin pr
```

## 安全协议

### 提交前检查

- [ ] 检查是否包含敏感信息（.env、credentials.json）
- [ ] 检查文件大小（避免 > 10MB）
- [ ] 验证提交信息格式
- [ ] 确认暂存区内容

### 禁止操作

- ❌ 使用 `--force` 或 `--force-with-lease` 推送
- ❌ 使用 `--no-verify` 跳过 hooks
- ❌ 修改 Git 配置
- ❌ 提交包含敏感信息的文件

### 提交失败处理

如果提交失败：

1. 检查错误信息
2. 识别问题类型
3. 提供解决方案
4. **不要使用 amend**，创建新提交

## 常见场景

### 场景 1：首次提交

```bash
# 用户：我需要初始化项目并提交
uvx --from git+https://github.com/lazygophers/ccplugin ignore
uvx --from git+https://github.com/lazygophers/ccplugin commit-all "feat: 初始化项目"
git push -u origin master
```

### 场景 2：功能开发

```bash
# 用户：我开发了一个新功能，需要创建 PR
git checkout -b feature/user-auth
# ... 开发代码 ...
git add .
uvx --from git+https://github.com/lazygophers/ccplugin commit-all "feat: 添加用户认证功能"
git push -u origin feature/user-auth
uvx --from git+https://github.com/lazygophers/ccplugin pr
```

### 场景 3：修复 Bug

```bash
# 用户：发现一个 bug，需要修复
git checkout -b fix/login-timeout
# ... 修复代码 ...
git add src/login.py
uvx --from git+https://github.com/lazygophers/ccplugin commit "fix: 修复登录超时问题"
git push -u origin fix/login-timeout
uvx --from git+https://github.com/lazygophers/ccplugin pr
```

### 场景 4：更新 PR

```bash
# 用户：根据 PR 审查反馈修改了代码，需要更新 PR
vim src/auth/login.py
git add src/auth/login.py
uvx --from git+https://github.com/lazygophers/ccplugin commit "fix: 修复登录验证逻辑"
git push
uvx --from git+https://github.com/lazygophers/ccplugin pr update 123
```

## 最佳实践

### 1. 提交粒度

✅ **好的提交**（单一职责）：

- "feat: 添加用户注册功能"
- "feat: 添加用户登录功能"
- "test: 添加认证测试"

❌ **不好的提交**（过大）：

- "feat: 添加用户模块"（太宽泛）

### 2. 提交信息

✅ **好的提交信息**：

- 清晰、具体
- 遵循规范
- 包含上下文

```
feat: 添加用户认证功能

实现用户注册、登录和会话管理
```

❌ **不好的提交信息**：

- 模糊、不具体
- 不遵循规范

```
update
fix bug
done
```

### 3. PR 质量

✅ **好的 PR**：

- 变更范围合理（< 1000 行）
- 描述完整（Summary、Changes、Test plan）
- 包含测试

❌ **不好的 PR**：

- 变更范围过大
- 描述不完整
- 缺少测试

### 4. 分支策略

✅ **好的分支**：

- `feature/user-auth`
- `fix/login-timeout`
- `refactor/database`

❌ **不好的分支**：

- `stuff`
- `tmp`
- `test`

## 与 Agent 配合

### git Agent

使用 `git` agent 进行复杂的 Git 操作：

```
启动 git agent 处理：
- 复杂的分支操作
- PR 创建和更新
- 提交策略规划
- 推送失败处理（包括代理设置）
- 仓库维护和优化
```

## 错误处理

### 提交失败

```bash
# 错误：暂存区为空
# 解决：先使用 git add 添加文件

# 错误：hooks 失败
# 解决：修复 hooks 报告的问题，重新提交

# 错误：包含敏感信息
# 解决：移除敏感文件，更新 .gitignore
```

### 推送失败

```bash
# 错误：网络连接失败或超时
# 解决：尝试设置代理后重试

# 方式 1：设置环境变量（当前会话）
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890
git push

# 方式 2：单次命令使用代理
http_proxy=http://127.0.0.1:7890 https_proxy=http://127.0.0.1:7890 git push

# 取消代理（当前会话）
unset http_proxy
unset https_proxy

# 错误：认证失败
# 解决：检查 SSH 密钥或凭据

# 错误：分支冲突
# 解决：先 pull，解决冲突后再推送
```

### PR 创建失败

```bash
# 错误：分支未推送
# 解决：先执行 git push

# 错误：gh 未安装
# 解决：安装 GitHub CLI
# macOS: brew install gh

# 错误：PR 已存在
# 解决：使用 uvx --from git+https://github.com/lazygophers/ccplugin pr update 更新现有 PR
```

## 参考资源

### 项目文档

- [插件 README](${CLAUDE_PLUGIN_ROOT}/README.md)
- [命令文档](${CLAUDE_PLUGIN_ROOT}/commands/)

### 官方文档

- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [Git 工作流](https://www.atlassian.com/git/tutorials/comparing-workflows)
- [Pull Request 最佳实践](https://github.blog/2015-01-21-how-to-write-the-perfect-pull-request/)
