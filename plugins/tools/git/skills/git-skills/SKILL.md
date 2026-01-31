---
name: git-skills
description: Git 操作技能 - 当用户需要进行 Git 提交、创建 PR、更新 PR 或管理 .gitignore 时自动激活。提供 Git 工作流指导、提交规范和 PR 最佳实践。
context: fork
agent: git:git
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

详见 [@commit-guidelines](${CLAUDE_PLUGIN_ROOT}/skills/git/commit-guidelines.md) 了解完整的提交规范指南。

**快速参考**：

遵循 Conventional Commits 规范，提交信息格式为：

```
<type>: <subject>
```

其中 `type` 包括：`feat`（新功能）、`fix`（缺陷修复）、`docs`（文档更新）、`style`（代码格式）、`refactor`（代码重构）、`test`（测试相关）、`chore`（构建/工具）。

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

## 与 Agent 配合

### git Agent

使用 Agents(git:git) 进行 Git 操作：

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
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
export ALL_PROXY=http://127.0.0.1:7890
git push

# 方式 2：单次命令使用代理
HTTP_PROXY=http://127.0.0.1:7890 HTTPS_PROXY=http://127.0.0.1:7890 git push

# 取消代理（当前会话）
unset HTTP_PROXY
unset HTTPS_PROXY
unset ALL_PROXY

# 错误：认证失败
# 解决：检查 SSH 密钥或凭据

# 错误：分支冲突
# 解决：先 pull，解决冲突后再推送
```

## 参考资源

### 本技能的分层文档

- 📋 [提交规范指南](./commit-guidelines.md) - Conventional Commits 格式、类型定义、提交粒度、最佳实践
- 📋 [PR 规范指南](./pr-guidelines.md) - PR 创建更新、质量标准、编写实践、常见问题、工作流示例
