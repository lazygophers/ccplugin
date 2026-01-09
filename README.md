# CCPlugin Market

> Claude Code 插件市场 - 提供高质量插件和开发模板

## 简介

CCPlugin Market 是一个为 Claude Code 提供插件的集中市场。我们提供了一系列经过验证的高质量插件，帮助开发者提高工作效率。

## 可用插件

| 插件名称 | 描述 | 版本 | 标签 |
|---------|------|------|------|
| `task` | 项目任务管理插件 - 使用 SQLite 存储任务，支持 Markdown 导入导出，完整的项目任务跟踪解决方案 | 0.0.7 | task, todo, project, management, sqlite |
| `semantic` | 语义搜索插件 - 基于向量嵌入的自然语言代码搜索，支持中英文混合查询和多语言代码理解 | 0.0.7 | semantic, search, vector, embedding, nlp, code-search |
| `git` | Git 操作插件 - 提供完整的 Git 操作支持，包括提交管理、Pull Request 管理和 .gitignore 管理 | 0.0.7 | git, commit, pr, pull-request, gitignore, version-control, workflow |
| `template` | 插件开发模板 - 提供标准的插件结构和示例代码 | - | template, development |

## 快速开始

### 环境要求

- **Python**: >= 3.12
- **uv**: Python 包管理器和执行器（强制使用）
- **Claude Code**: 最新版本

### 安装 uv（如未安装）

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 验证安装
uv --version
```

### 安装插件

```bash
# 从本地目录安装
/plugin install ./plugins/task
/plugin install ./plugins/semantic
/plugin install ./plugins/git

# 或从 GitHub 安装
/plugin install https://github.com/lazygophers/ccplugin/tree/master/plugins/task
```

### 使用插件

```bash
# 任务管理
/task add "项目初始化"
/task list

# 语义搜索
/semantic init
/semantic index
/semantic search "如何读取文件"

# Git 操作
/commit-all "feat: 初始化项目"
/create-pr
```

## 核心插件

### Task 插件

项目任务管理插件，使用 SQLite 存储任务，支持 Markdown 导出。

**功能特性**：
- ✅ 任务管理：创建、更新、删除任务
- ✅ 状态跟踪：pending、in_progress、completed、blocked、cancelled
- ✅ 任务类型：feature、bug、refactor、test、docs、config
- ✅ 验收标准：为每个任务定义验收标准
- ✅ 依赖关系：支持前置依赖和父子任务
- ✅ SQLite 存储：轻量级，无需额外依赖
- ✅ Markdown 导出：便于版本控制和分享

**快速开始**：
```bash
# 安装插件
/plugin install ./plugins/task

# 创建第一个任务
/task add "项目初始化"

# 查看任务
/task list
/task stats
```

**详细文档**: [plugins/task/README.md](plugins/task/README.md)

### Semantic 插件

基于向量嵌入的智能代码搜索插件，支持多编程语言、多模型、GPU 加速。

**功能特性**：
- 🔍 语义搜索：使用自然语言查询代码
- 🚀 混合引擎：FastEmbed + CodeModel + Symbol 三层融合
- 🌐 多语言支持：支持 19 种编程语言
- 🎯 语言特定优化：针对不同语言的解析策略、分块大小、模型推荐
- 🤖 多模型支持：BGE、Jina、GTE、CodeT5 等最新嵌入模型
- ⚡ GPU 加速：支持 CUDA 加速
- 🗄️ LanceDB 存储：轻量级向量数据库
- 📊 增量索引：支持增量更新索引

**快速开始**：
```bash
# 安装插件
/plugin install ./plugins/semantic

# 初始化
/semantic init

# 建立索引
/semantic index

# 搜索代码
/semantic search "如何读取文件"
```

**详细文档**: [plugins/semantic/README.md](plugins/semantic/README.md)

### Git 插件

Git 仓库管理插件，提供完整的 Git 操作支持。

**功能特性**：
- 📝 提交管理：提交所有变更、提交暂存区变更
- 🔀 Pull Request 管理：创建 PR、更新 PR、PR 模板
- 🙈 忽略文件管理：智能更新 .gitignore
- 👥 子代理：git-developer、git-reviewer

**快速开始**：
```bash
# 安装插件
/plugin install ./plugins/git

# 更新 .gitignore
/update-ignore

# 提交所有变更
/commit-all "feat: 初始化项目"

# 创建 PR
/create-pr
```

**详细文档**: [plugins/git/README.md](plugins/git/README.md)

## 插件开发

### 使用模板创建新插件

```bash
# 复制模板
cp -r plugins/template my-new-plugin

# 修改配置
cd my-new-plugin/.claude-plugin
vi plugin.json

# 实现功能
cd ../commands  # 添加命令
cd ../agents    # 添加代理
cd ../skills    # 添加技能
```

### 插件结构

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json         # 插件清单（必需）
├── commands/               # 自定义命令
│   └── my-command.md
├── agents/                 # 子代理
│   └── my-agent.md
├── skills/                 # 技能
│   └── my-skill/
│       └── SKILL.md
├── hooks/                  # 钩子（可选）
│   └── hooks.json
├── scripts/                # 脚本（可选）
│   └── script.py
├── README.md               # 插件文档（推荐）
└── CHANGELOG.md            # 版本历史（推荐）
```

### 编程语言规范

**强制要求**：
- ✅ **Python（首选）** - 用于复杂逻辑、数据处理、API 调用
- ✅ **Bash（次选）** - 用于系统操作、文件处理、快速脚本
- ✅ **Markdown/JSON（必需）** - 用于配置和定义

**Python 执行规范（强制）**：

⚠️ **必须使用 uv 管理和执行 Python**

- ✅ **使用 uv**：`uv run script.py` 或 `uv pip install ...`
- ❌ **禁止直接执行**：`python3 script.py` 或 `python script.py`

**原因**：
- uv 提供快速的依赖管理和虚拟环境
- 确保依赖隔离和版本一致性
- 避免全局 Python 环境污染

**正确用法**：
```bash
# 执行 Python 脚本
uv run scripts/my_script.py

# 安装依赖
uv pip install requests

# 同步依赖
uv sync
```

**错误用法**：
```bash
# ❌ 不要这样
python3 scripts/my_script.py
python scripts/my_script.py
./scripts/my_script.py
```

### 提交插件

1. Fork 本仓库
2. 在 `plugins/` 目录下创建插件
3. 更新 `marketplace.json`
4. 提交 Pull Request

## 文档

### 开发文档

- [插件开发指南](docs/plugin-development.md) - 完整的插件开发教程
- [API 参考](docs/api-reference.md) - 完整的 API 参考
- [最佳实践](docs/best-practices.md) - 开发最佳实践
- [支持的语言](docs/supported-languages.md) - 插件开发语言选择指南
- [编译型语言指南](docs/compiled-languages-guide.md) - Go/Rust 等编译型语言使用指南

### 项目文档

- [CLAUDE.md](CLAUDE.md) - 项目开发规范和指导
- [CHANGELOG.md](CHANGELOG.md) - 版本变更历史

## 常见问题

### 如何安装插件？

```bash
# 从本地目录安装
/plugin install ./plugins/task

# 从 GitHub 安装
/plugin install https://github.com/lazygophers/ccplugin/tree/master/plugins/task
```

### 如何开发新插件？

1. 复制模板：`cp -r plugins/template my-new-plugin`
2. 修改配置：编辑 `.claude-plugin/plugin.json`
3. 实现功能：在 `commands/`、`agents/`、`skills/` 添加内容
4. 测试插件：`/plugin install ./my-new-plugin`
5. 提交市场：更新 `marketplace.json` 并提交 PR

### 为什么强制使用 uv？

uv 提供快速的依赖管理和虚拟环境，确保依赖隔离和版本一致性，避免全局 Python 环境污染。

### 插件数据存储在哪里？

每个插件的数据存储在项目目录的 `.lazygophers/ccplugin/<plugin-name>/` 目录下，自动被 `.gitignore` 忽略。

## 许可证

AGPL-3.0-or-later - 详见 [LICENSE](LICENSE)

## 联系方式

- 作者: lazygophers
- 邮箱: admin@lazygophers.dev
- 仓库: https://github.com/lazygophers/ccplugin
