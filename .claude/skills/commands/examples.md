# 命令示例集合

## 示例 1：简单命令

```yaml
---
name: hello
description: 向用户发送问候
---

# 向用户发送问候

Hello! 很高兴为您服务。

## 使用

直接输入：
```
/hello
```
```

## 示例 2：带参数命令

```yaml
---
name: add
description: 添加新任务
arguments:
  - name: description
    description: 任务描述
    required: true
  - name: priority
    description: 优先级
    required: false
    default: medium
    enum: [low, medium, high]
examples:
  - "/task add \"Complete report\""
  - "/task add \"Fix bug\" high"
---

# 添加新任务

将新任务添加到任务列表。

## 参数

- `description`: 任务描述（必需）
- `priority`: 优先级，可选值 [low, medium, high]，默认 medium

## 使用

```
/task add "Write documentation"
/task add "Fix critical bug" high
```
```

## 示例 3：带选项命令

```yaml
---
name: search
description: 搜索代码
arguments:
  - name: query
    description: 搜索关键词
    required: true
options:
  - name: type
    short: -t
    description: 搜索类型
    default: code
    enum: [code, file, symbol]
  - name: verbose
    short: -v
    description: 显示详细信息
    is_flag: true
examples:
  - "/search \"function_name\""
  - "/search \"class Foo\" -t symbol"
  - "/search \"TODO\" -v"
---

# 代码搜索

在代码库中搜索指定内容。

## 参数

- `query`: 搜索关键词（必需）

## 选项

- `-t`, `--type`: 搜索类型 [code, file, symbol]，默认 code
- `-v`, `--verbose`: 显示详细信息

## 使用

```
/search "auth_function"
/search "UserController" -t file
/search "FIXME" -v
```
```

## 示例 4：交互式命令

```yaml
---
name: create
description: 创建新项目
---

# 创建新项目

我将帮您创建一个新项目。

首先，请选择项目类型：

- [Web] Web 应用
- [CLI] 命令行工具
- [Lib] 库/包

请输入您的选择：
```

## 示例 5：复杂命令

```yaml
---
name: deploy
description: 部署应用到生产环境
arguments:
  - name: environment
    description: 部署环境
    required: true
    enum: [staging, production]
options:
  - name: force
    short: -f
    description: 强制部署（跳过确认）
    is_flag: false
    default: false
  - name: timeout
    short: -t
    description: 超时时间
    default: "30"
  - name: dry-run
    short: -n
    description: 演练模式（不实际部署）
    is_flag: true
examples:
  - "/deploy production"
  - "/deploy staging --force"
  - "/deploy production --timeout 60"
  - "/deploy production --dry-run"
---

# 部署应用到生产环境

将应用部署到指定环境。

## ⚠️ 危险操作

此命令会修改生产环境，请确认操作。

## 参数

- `environment`: 部署环境（必需），可选值 [staging, production]

## 选项

- `-f`, `--force`: 强制部署，跳过确认提示
- `-t`, `--timeout`: 超时时间，默认 30
- `-n`, `--dry-run`: 演练模式，仅显示操作计划

## 使用

```
/deploy staging
/deploy production --force
/deploy production --timeout 60
/deploy production --dry-run
```
```

## 示例 6：Git 提交命令（完整模板）

```yaml
---
name: commit
description: 提交更改到 Git 仓库
arguments:
  - name: message
    description: 提交信息（可选，不提供时自动生成）
    required: false
options:
  - name: all
    short: -a
    description: 提交所有更改
    is_flag: true
  - name: amend
    short: --amend
    description: 修正上次提交
    is_flag: true
examples:
  - "/commit"
  - "/commit \"feat: add new feature\""
  - "/commit \"fix: resolve bug\" -a"
  - "/commit --amend"
---

# 提交更改到 Git 仓库

基于当前暂存区的变更，生成符合 Conventional Commits 规范的提交信息，并安全提交代码。

## 工作流

1. **检查 Git 状态**：获取当前分支、暂存文件和变更统计
2. **安全检查**：检查暂存区是否包含敏感文件
3. **生成提交信息**：根据暂存变更内容生成提交信息
4. **执行提交**：使用 `git commit` 提交变更

## 参数

- `message`: 提交信息，可选
  - 遵循 Conventional Commits 规范
  - ≤50 字符
  - 支持中文描述

## 选项

- `-a`, `--all`: 提交所有更改
- `--amend`: 修正上次提交

## 使用

```bash
# 自动生成提交信息
gitadd src/
/commit

# 指定提交信息
gitadd src/auth/
/commit "feat: 添加用户认证"

# 提交所有更改
/commit "fix: 修复登录超时问题" -a

# 修正上次提交
/commit --amend
```

## 提交类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `feat` | 新功能 | feat: 添加用户登录功能 |
| `fix` | 缺陷修复 | fix: 修复登录超时问题 |
| `refactor` | 代码重构 | refactor: 优化数据库查询 |
| `docs` | 文档更新 | docs: 更新 API 文档 |
| `test` | 测试相关 | test: 添加单元测试 |
| `chore` | 构建/工具 | chore: 更新依赖版本 |
| `style` | 代码格式 | style: 统一代码缩进 |

## 检查清单

- [ ] 已使用 `git add` 添加需要提交的文件
- [ ] 检查暂存区内容是否正确
- [ ] 没有遗漏需要提交的重要文件
- [ ] 提交信息清晰准确

## 注意事项

### 敏感文件检查

禁止提交：
- `.env*`、`*.secret`、`*.key`、`*.pem`
- `credentials.json`、`.npmrc`、`.aws/`、`.ssh/`

如发现敏感文件，先移除：
```bash
git reset HEAD <file>
```

### 临时文件检查

禁止提交：
- `node_modules/`、`__pycache__/`、`.venv/`
- `dist/`、`build/`、`*.log`

### 文件大小检查

- 文件 > 10MB 时发出警告
- 考虑使用 Git LFS

## 失败处理

如提交失败：
1. 检查 pre-commit hooks 错误信息
2. 移除或修复不符合规范的内容
3. 重新提交
```
