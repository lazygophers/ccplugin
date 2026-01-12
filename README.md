# CCPlugin Market

> Claude Code 插件市场 - 提供高质量插件和开发模板

## 简介

CCPlugin Market 是一个为 Claude Code 提供插件的集中市场。我们提供了一系列经过验证的高质量插件，帮助开发者提高工作效率，覆盖项目管理、代码搜索、Git 操作、多语言开发等多个领域。

## 可用插件

| 插件名称 | 描述 | 版本 | 标签 |
|---------|------|------|------|
| `task` | 项目任务管理插件 - 使用 SQLite 存储任务，支持 Markdown 导入导出，完整的项目任务跟踪解决方案 | 0.0.11 | task, todo, project, management, sqlite |
| `semantic` | 语义搜索插件 - 基于向量嵌入的自然语言代码搜索，支持中英文混合查询和多语言代码理解 | 0.0.11 | semantic, search, vector, embedding, nlp, code-search |
| `git` | Git 操作插件 - 提供完整的 Git 操作支持，包括提交管理、Pull Request 管理和 .gitignore 管理 | 0.0.11 | git, commit, pr, pull-request, gitignore, version-control, workflow |
| `golang` | Golang 开发插件 - 提供 Golang 开发规范、最佳实践和代码智能支持 | 0.0.11 | golang, go, development, coding-style, best-practices, testing, debugging, performance |
| `python` | Python 开发插件 - 提供 Python 开发规范、最佳实践和代码智能支持 | 0.0.11 | python, py, development, coding-style, best-practices, pep8, type-hints, testing, debugging |
| `typescript` | TypeScript 开发插件 - 提供 TypeScript 开发规范、最佳实践和代码智能支持 | 0.0.11 | typescript, ts, development, type-safety, strict-mode, vitest, pnpm, coding-style |
| `javascript` | JavaScript 开发插件 - 提供 JavaScript（ES2024-2025）开发规范、最佳实践和代码智能支持 | 0.0.11 | javascript, js, es2024, es2025, development, async-await, esm, vitest, vite, pnpm |
| `vue` | Vue 3 开发插件 - 提供 Vue 3 开发规范、最佳实践和代码智能支持 | 0.0.11 | vue, vue3, composition-api, pinia, vite, vitest, development, coding-style |
| `react` | React 18+ 开发插件 - 提供现代 React 开发规范、最佳实践和代码智能支持 | 0.0.11 | react, react18, hooks, zustand, redux, nextjs, vite, vitest, development, coding-style |
| `nextjs` | Next.js 16+ 全栈开发插件 - 提供 App Router、Server Components、Route Handlers 和现代全栈开发规范 | 0.0.11 | nextjs, next, fullstack, app-router, server-components, route-handlers, ppr, turbopack |
| `antd` | Ant Design 5.x 企业级 UI 组件库插件 - 提供设计系统、组件库、主题定制、表单管理和完整的企业应用开发规范 | 0.0.11 | antd, ant-design, ui-components, design-system, form, table, enterprise, react, typescript |
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
/plugin install ./plugins/golang
/plugin install ./plugins/python
/plugin install ./plugins/typescript
/plugin install ./plugins/javascript
/plugin install ./plugins/vue
/plugin install ./plugins/react
/plugin install ./plugins/nextjs
/plugin install ./plugins/antd

# 或从 GitHub 安装
/plugin install https://github.com/lazygophers/ccplugin/tree/master/plugins/task
/plugin install https://github.com/lazygophers/ccplugin/tree/master/plugins/semantic
/plugin install https://github.com/lazygophers/ccplugin/tree/master/plugins/git
```

### 使用插件

```bash
# 任务管理
/task add "项目初始化"
/task list
/task stats

# 语义搜索
/semantic init
/semantic index
/semantic search "如何读取文件"

# Git 操作
/commit-all "feat: 初始化项目"
/update-ignore
/create-pr

# 语言开发支持（自动激活）
# 当你编写 Python 代码时，python 插件会自动激活
# 当你编写 Go 代码时，golang 插件会自动激活
# 当你编写 TypeScript/React 代码时，相应插件会自动激活
```

## 核心插件

### Task 插件

项目任务管理插件，使用 SQLite 存储任务，支持 Markdown 导入导出，完整的项目任务跟踪解决方案。

**功能特性**：
- ✅ 任务管理：创建、更新、删除任务
- ✅ 状态跟踪：pending、in_progress、completed、blocked、cancelled
- ✅ 任务类型：feature、bug、refactor、test、docs、config
- ✅ 验收标准：为每个任务定义验收标准
- ✅ 依赖关系：支持前置依赖和父子任务
- ✅ SQLite 存储：轻量级，无需额外依赖
- ✅ Markdown 导出：便于版本控制和分享
- ✅ 任务统计：提供任务完成情况和进度统计

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
- 📤 Push 管理：支持推送代码到远程仓库

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

### 语言与框架插件

CCPlugin Market 提供了一系列语言和框架开发插件，帮助开发者遵循最佳实践和编码规范：

#### Golang 插件
- 📋 提供 Golang 开发规范和最佳实践
- 🧪 测试、调试和性能优化指导
- 🎯 代码智能支持和自动补全
- 🔧 基于 lazygophers 生态的最佳实践

#### Python 插件
- 📋 遵循 PEP 8 规范和行业最佳实践
- 🎯 类型提示和代码智能支持
- 🧪 测试、调试和性能优化指导
- 🔧 现代化 Python 开发工具链支持

#### TypeScript 插件
- 📋 TypeScript 开发规范和最佳实践
- 🎯 严格模式和类型安全指导
- 🧪 Vitest 测试框架支持
- 🔧 pnpm 包管理工具支持

#### JavaScript 插件
- 📋 现代化 JavaScript（ES2024-2025）开发规范
- 🎯 异步编程和 ESM 模块系统指导
- 🧪 Vitest 测试框架支持
- 🔧 Vite 构建工具和 pnpm 包管理支持

#### Vue 插件
- 📋 Vue 3 开发规范和最佳实践
- 🎯 Composition API 深度指导
- 🧪 Pinia 状态管理和 Vitest 测试支持
- 🔧 Vite 构建工具支持

#### React 插件
- 📋 React 18+ 开发规范和最佳实践
- 🎯 Hooks 深度指导和函数组件标准
- 🧪 Zustand/Redux 状态管理和 Vitest 测试支持
- 🔧 Next.js 集成和 Vite 构建工具支持

#### Next.js 插件
- 📋 Next.js 16+ 全栈开发规范
- 🎯 App Router 和 Server Components 指导
- 🧪 PPR、Server Actions 和数据缓存支持
- 🔧 Turbopack 构建工具支持

#### Ant Design 插件
- 📋 Ant Design 5.x 企业级 UI 组件库规范
- 🎯 设计系统和组件使用最佳实践
- 🧪 表单管理和表格组件深度指导
- 🔧 Next.js 无缝集成支持

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
/plugin install ./plugins/semantic
/plugin install ./plugins/git

# 从 GitHub 安装
/plugin install https://github.com/lazygophers/ccplugin/tree/master/plugins/task
```

### 如何开发新插件？

1. 复制模板：`cp -r plugins/template my-new-plugin`
2. 修改配置：编辑 `.claude-plugin/plugin.json`
3. 实现功能：
   - 在 `commands/` 目录下添加自定义命令
   - 在 `agents/` 目录下添加子代理
   - 在 `skills/` 目录下添加技能
4. 测试插件：`/plugin install ./my-new-plugin`
5. 提交市场：更新 `marketplace.json` 并提交 PR

### 为什么强制使用 uv？

uv 提供快速的依赖管理和虚拟环境，确保依赖隔离和版本一致性，避免全局 Python 环境污染。uv 的执行速度比传统的 pip 和 virtualenv 快数倍，能够显著提高开发效率。

### 插件数据存储在哪里？

每个插件的数据存储在项目目录的 `.lazygophers/ccplugin/<plugin-name>/` 目录下，自动被 `.gitignore` 忽略。

### 如何更新插件？

插件会随着 Claude Code 的更新自动更新，或者您可以手动重新安装插件来获取最新版本：

```bash
/plugin install ./plugins/task --force
```

### 支持哪些编程语言？

CCPlugin Market 支持多种编程语言，包括：
- Python
- Go
- TypeScript
- JavaScript
- Vue
- React
- Next.js
- Ant Design
- 以及更多...

## 许可证

AGPL-3.0-or-later - 详见 [LICENSE](LICENSE)

## 联系方式

- 作者: lazygophers
- 邮箱: admin@lazygophers.dev
- 仓库: https://github.com/lazygophers/ccplugin
- 问题反馈: https://github.com/lazygophers/ccplugin/issues

## 贡献指南

我们欢迎社区贡献！如果您想为 CCPlugin Market 贡献代码或插件，请遵循以下步骤：

1. Fork 本仓库
2. 创建您的特性分支：`git checkout -b feature/my-new-feature`
3. 提交您的更改：`git commit -m "Add some feature"`
4. 推送到分支：`git push origin feature/my-new-feature`
5. 提交 Pull Request

请确保您的代码符合我们的开发规范，并通过所有测试。
