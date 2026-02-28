# 命令系统

Git 插件提供五个核心命令，覆盖提交、PR 和忽略文件管理。

## 命令列表

| 命令 | 描述 | 用法 |
|------|------|------|
| `/commit-all` | 提交所有变更 | `/commit-all "message"` |
| `/commit` | 提交暂存区变更 | `/commit "message"` |
| `/update-ignore` | 更新 .gitignore | `/update-ignore` |
| `/create-pr` | 创建 Pull Request | `/create-pr` |
| `/update-pr` | 更新 Pull Request | `/update-pr <number>` |

## /commit-all - 提交所有变更

### 功能

提交所有变更，包括未跟踪和已修改的文件。

### 用法

```bash
/commit-all "feat: 添加用户认证功能"
```

### 执行流程

1. 检查工作区状态
2. 添加所有文件到暂存区
3. 生成符合规范的提交信息
4. 执行提交

### 适用场景

- 快速提交所有变更
- 初始化项目提交
- 小型功能开发完成

## /commit - 提交暂存区变更

### 功能

仅提交暂存区的变更，不包括未暂存的修改。

### 用法

```bash
# 先暂存文件
git add src/auth.py

# 提交暂存区
/commit "feat: 添加用户登录功能"
```

### 执行流程

1. 检查暂存区状态
2. 验证提交信息格式
3. 执行提交

### 适用场景

- 精确控制提交内容
- 分批提交功能
- 代码审查准备

## /update-ignore - 更新 .gitignore

### 功能

根据未提交的文件智能更新 .gitignore。

### 用法

```bash
/update-ignore
```

### 自动识别

| 类型 | 模式 |
|------|------|
| 日志文件 | `*.log` |
| 环境变量 | `*.env`, `.env.local` |
| 依赖目录 | `node_modules/`, `__pycache__/` |
| 临时文件 | `*.swp`, `.DS_Store` |
| 构建产物 | `dist/`, `build/`, `*.pyc` |
| IDE 配置 | `.idea/`, `.vscode/` |

### 执行流程

1. 扫描未跟踪文件
2. 识别应忽略的模式
3. 更新 .gitignore
4. 显示变更摘要

## /create-pr - 创建 Pull Request

### 功能

基于当前分支变更自动生成 PR。

### 用法

```bash
# 确保分支已推送到远程
git push -u origin feature-branch

# 创建 PR
/create-pr
```

### 生成的 PR 内容

```markdown
## Summary

简要描述本次变更的目的和内容。

## Changes

- 添加用户认证模块
- 实现登录/注册功能
- 添加单元测试

## Test Plan

- [ ] 运行单元测试
- [ ] 手动测试登录流程
- [ ] 验证错误处理
```

### 执行流程

1. 分析分支变更
2. 生成 PR 标题
3. 生成 PR 描述
4. 创建 PR

## /update-pr - 更新 Pull Request

### 功能

根据完整变更更新 PR 描述。

### 用法

```bash
# 添加新提交
git add .
/commit "feat: 添加密码重置功能"
git push

# 更新 PR
/update-pr 123
```

### 执行流程

1. 获取 PR 信息
2. 分析完整变更
3. 更新 PR 描述
4. 显示更新内容

## 提交信息规范

### Conventional Commits

```
<type>: <subject>

<body>

<footer>
```

### 类型（type）

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | feat: 添加用户认证功能 |
| `fix` | 缺陷修复 | fix: 修复登录超时问题 |
| `docs` | 文档更新 | docs: 更新 API 文档 |
| `style` | 代码格式 | style: 统一代码缩进 |
| `refactor` | 代码重构 | refactor: 优化数据库查询 |
| `test` | 测试相关 | test: 添加单元测试 |
| `chore` | 构建/工具 | chore: 更新依赖版本 |

### 示例

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
