---
name: 更新 Git 忽略文件
description: 根据未提交文件智能更新 .gitignore
allowed-tools: Bash(git:*), Read, Write
---

## 知识库

**tooling-guide**：文件操作和工具选择规范

## 当前 Git 状态

- 未跟踪文件：!`git ls-files --others --exclude-standard`
- 文件状态：!`git status --short`

## 任务

分析未提交文件，识别应该忽略的文件类型，智能更新 .gitignore。

### 自动识别规则

**临时文件**：`*.log`, `*.tmp`, `*.temp`, `*.cache`, `*.bak`, `*.swp`, `*.swo`

**缓存目录**：`__pycache__/`, `.pytest_cache/`, `node_modules/`, `.venv/`, `venv/`

**环境文件**：`.env`, `.env.local`, `.env.*`, `*.secret`, `*.key`

**IDE 配置**：`.vscode/`, `.idea/`（项目配置除外）
**系统文件**：`.DS_Store`, `Thumbs.db`

**构建产物**：`dist/`, `build/`, `target/`, `.next/`, `out/`

**测试覆盖**：`.coverage`, `coverage/`, `htmlcov/`

### 执行步骤

1. 分析未跟踪文件
2. 识别应该忽略的文件类型
3. 检查 .gitignore 是否存在
4. 追加新规则（去重）
5. 清理已追踪的不需要的文件（如需要）：`git rm --cached <file>`
6. 提交更改：`git add .gitignore && git commit -m "chore: 更新 .gitignore"`

### 注意事项

- 确认不会忽略需要的文件
- 项目配置文件（如 .vscode/settings.json）可能需要保留
- 某些数据库文件可能需要版本控制
