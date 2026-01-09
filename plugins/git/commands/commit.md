---
name: Git 智能提交
description: 基于当前暂存变更自动生成高质量提交信息并提交
allowed-tools: Bash(git:*)
---

## 知识库

**code-review-standards**：代码质量检查标准，确保提交质量

## 当前 Git 状态

- 当前分支：!`git branch --show-current`
- 文件状态：!`git status --short`
- 暂存文件：!`git diff --staged --name-status`
- 变更统计：!`git diff --staged --stat`
- 最近提交：!`git log --oneline -5`

## Git 忽略检查

### 敏感文件检查

!`git diff --staged --name-only | grep -E '\.(env|secret|key|pem|p12|pfx|jks|keystore)$|credentials|config\.json|\.npmrc|\.pypirc|id_rsa|\.aws/|\.ssh/' || echo "✓ 未发现敏感文件"`

### 不适合提交的文件检查

!`git diff --staged --name-only | grep -E '\.(log|tmp|temp|cache|bak|swp|swo|DS_Store)$|node_modules/|\.idea/|\.vscode/|__pycache__/|\.pytest_cache/|\.coverage|coverage/|dist/|build/|target/|\.next/|out/|\.nuxt/|\.output/|\.venv/|venv/|env/|\.egg-info/|\.tox/' || echo "✓ 未发现临时/构建文件"`

### 大文件检查

提示：检查暂存区是否有>10MB文件。如有，考虑使用Git LFS或外部存储。

## 任务

基于暂存变更，生成高质量git commit并提交。

### 提交信息格式

```text
类型(范围): 简洁描述

[可选的详细说明]
```

**类型**：feat（新功能）| fix（Bug修复）| refactor（重构）| docs（文档）| test（测试）| chore（构建/工具/依赖）

### 要求

**标题**：≤50字符，简体中文，描述意图（为什么改）非变更内容（改了什么）

**详细说明**：如需要，空行后添加

**文件检查**：如"Git忽略检查"发现问题，必须先移除：

- 敏感文件：`.env*`, `*.secret`, `*.key`, `*.pem`, `*.p12`, `*.pfx`, `id_rsa`, `credentials`, `config.json`, `.npmrc`, `.aws/`, `.ssh/`
- 临时/构建：`*.log`, `*.tmp`, `*.temp`, `*.cache`, `*.bak`, `*.swp`, `.DS_Store`, `.idea/`, `.vscode/` (项目配置除外), `node_modules/`, `__pycache__/`, `.venv/`, `dist/`, `build/`, `target/`, `.next/`, `out/`
- 大文件：>10MB 应使用Git LFS或外部存储

**移除命令**：`git reset HEAD <文件>` | 更新`.gitignore`

### 执行步骤

1. 检查大文件（观察`git diff --staged --stat`）
2. 如有未暂存文件需提交：`git add <files>`
3. 生成提交信息
4. 提交：`git commit -m "提交信息"`
5. 验证：`git status`
