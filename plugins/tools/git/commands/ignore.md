---
description: 更新 Git 忽略文件 - 根据未提交文件智能更新 .gitignore
argument-hint: []
allowed-tools: Bash(git:*), Read, Write
model: haiku
---

# ignore

## 命令描述

智能分析项目中未跟踪的文件和目录，识别应该被忽略的文件类型（临时文件、缓存、环境配置等），自动更新 `.gitignore` 文件。

## 工作流描述

1. **扫描未跟踪文件**：列出当前工作目录中的所有未追踪文件
2. **分析文件类型**：识别应该被忽略的文件模式（临时、缓存、环境等）
3. **检查 .gitignore**：查看现有的忽略规则
4. **追加新规则**：将新的忽略规则添加到 .gitignore（去重）
5. **提交更改**：将 .gitignore 变更提交

## 命令执行方式

### 使用方法

```bash
# 使用 git 原生命令手动添加到 .gitignore
echo "*.log" >> .gitignore
echo ".env" >> .gitignore
```

### 执行时机

- 项目初始化后，需要配置基本的忽略规则
- 发现新的不应该被追踪的文件时
- 定期审查和更新 .gitignore 配置

### 执行参数

无参数，自动扫描并更新。

### 命令说明

- 自动识别常见的需要忽略的文件类型
- 避免重复添加规则
- 提示项目配置文件可能需要保留
- 支持自定义排除某些文件

## 相关Skills（可选）

参考 Git 操作技能：`@${CLAUDE_PLUGIN_ROOT}/skills/git/SKILL.md`

## 依赖脚本

```bash
# 使用 git 原生命令手动更新 .gitignore
```

## 示例

### 基本用法

```bash
# 手动编辑 .gitignore 文件
vim .gitignore

# 或使用 echo 追加规则
echo "*.log" >> .gitignore
```

### 完整工作流

```bash
# 1. 初始化项目
git init
git add README.md

# 2. 更新 .gitignore
echo "*.log" >> .gitignore
echo ".env" >> .gitignore

# 3. 提交配置
git add .gitignore
git commit -m "chore: 初始化 .gitignore 配置"
```

## 检查清单

在更新 .gitignore 前，确保满足以下条件：

- [ ] 已确认项目类型和依赖（Python、Node.js 等）
- [ ] 了解哪些文件或目录应该被忽略
- [ ] 确认项目配置文件（如 .vscode/settings.json）是否需要保留
- [ ] 有必要的数据库文件是否应该版本控制

## 注意事项

**自动识别的文件类型**：

| 文件类型 | 示例 | 说明 |
|---------|------|------|
| 临时文件 | `*.log`, `*.tmp`, `*.temp`, `*.cache`, `*.bak` | 日志和临时文件 |
| 临时目录 | `__pycache__/`, `.pytest_cache/`, `node_modules/` | 编程语言缓存 |
| 环境文件 | `.env`, `.env.local`, `.env.*`, `*.secret` | 敏感配置文件 |
| IDE 配置 | `.vscode/`, `.idea/` | 编辑器配置（谨慎处理） |
| 系统文件 | `.DS_Store`, `Thumbs.db` | 系统生成文件 |
| 构建产物 | `dist/`, `build/`, `target/`, `.next/` | 编译输出 |
| 测试覆盖 | `.coverage`, `coverage/`, `htmlcov/` | 测试报告 |
| 虚拟环境 | `.venv/`, `venv/`, `env/` | Python 虚拟环境 |

**特殊处理**：

- **项目配置**：某些 IDE 配置（`.vscode/settings.json` 等）可能需要版本控制
- **数据库文件**：某些本地数据库可能需要版本控制
- **密钥文件**：绝不提交私密密钥，使用 .gitignore 排除

## 其他信息

### .gitignore 规则语法

基础规则示例：

```gitignore
# 忽略所有 .log 文件
*.log

# 忽略整个目录
node_modules/
dist/

# 忽略特定文件
.env
credentials.json

# 忽略但保留特定文件
*.tmp
!important.tmp

# 通配符
*.{log,tmp,cache}
```

### 已追踪文件清理

如果需要移除已追踪的不需要的文件：

```bash
# 从 git 缓存移除文件（不删除本地文件）
git rm --cached <file>

# 从 git 缓存移除目录
git rm -r --cached <directory>

# 更新 .gitignore 后应用
git add .gitignore
git commit -m "chore: 更新 .gitignore 并移除已追踪文件"
```

### 常见场景

**Python 项目**：
```gitignore
__pycache__/
*.pyc
.venv/
venv/
dist/
build/
*.egg-info/
```

**Node.js 项目**：
```gitignore
node_modules/
npm-debug.log
.env
dist/
build/
```

**Java 项目**：
```gitignore
target/
.classpath
.project
.settings/
*.class
```

**通用配置**：
```gitignore
.DS_Store
Thumbs.db
.env
.env.local
*.log
```

### 最佳实践

1. **及时更新**：在项目初期就配置好 .gitignore
2. **分层管理**：根据项目类型添加特定的忽略规则
3. **避免过度忽略**：只忽略真正不需要的文件
4. **定期审查**：定期检查是否有遗漏的文件
5. **注释说明**：在 .gitignore 中注释说明各个规则的用途

### 与其他命令配合

```bash
# 1. 初始化忽略文件
echo "*.log" >> .gitignore

# 2. 提交配置
git add .gitignore
git commit -m "chore: 更新 .gitignore"

# 3. 推送到远程
git push
```
