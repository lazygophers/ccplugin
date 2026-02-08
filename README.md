# CCPlugin Market

> Claude Code 插件市场 - 提供高质量插件和开发模板

## 简介

CCPlugin Market 是一个为 Claude Code 提供插件的集中市场。我们提供了一系列经过验证的高质量插件，帮助开发者提高工作效率，覆盖项目管理、代码搜索、Git 操作、多语言开发等多个领域。

## 可用插件

### 顶层插件

| 插件名称   | 描述                                                                                          | 版本   | 标签                                    |
| ---------- | --------------------------------------------------------------------------------------------- | ------ | --------------------------------------- |
| `task`     | 完整的项目任务管理插件 - 支持开发计划创建、任务执行、进度追踪、依赖管理。基于SQLite数据库存储 | 0.0.93 | task-skills, todo, project, management, sqlite |
| `llms`     | llms.txt 标准插件 - 通过 Agent 自动生成符合 llms.txt 规范的文件                               | 0.0.93 | llms-skills, documentation, standards          |
| `notify`   | 系统通知插件 - 通过系统通知向用户实时提示会话状态变更、权限请求等重要事件                     | 0.0.93 | notify, notification, system            |
| `version`  | 版本号管理插件 - 提供 SemVer 版本管理，支持自动版本更新和手动版本设置                         | -      | version, semver, management             |
| `template` | 插件开发模板 - 快速创建新插件的基础结构                                                       | 0.0.93 | template, development                   |

### 工具插件 (tools/)

| 插件名称       | 描述                                                                                        | 版本   | 标签                                                      |
| -------------- | ------------------------------------------------------------------------------------------- | ------ | --------------------------------------------------------- |
| `deepresearch` | 深度研究插件 - 基于图思维框架的多智能体深度研究系统。支持多领域深度调查、引用验证、知识合成 | 0.0.93 | deepresearch, research, agent, knowledge                  |
| `git`          | Git 操作插件 - 提供 Git 仓库管理命令，包括提交、PR 管理、推送和 .gitignore 管理             | 0.0.93 | git-skills, commit, pr, pull-request, gitignore, version-control |
| `semantic`     | 代码语义搜索插件 - 基于向量嵌入的智能代码搜索。支持多编程语言、多模型、GPU加速              | 0.0.93 | semantic-skills, search, vector, embedding, code-search          |

### 语言插件 (languages/)

| 插件名称     | 描述                                                                                   | 版本   | 标签                                                        |
| ------------ | -------------------------------------------------------------------------------------- | ------ | ----------------------------------------------------------- |
| `golang`     | Golang 开发插件 - 提供 Golang 开发规范、最佳实践和代码智能支持                         | 0.0.93 | golang-skills, go, development, coding-style, best-practices       |
| `python`     | Python 开发插件 - 提供 Python 开发规范、最佳实践和代码智能支持                         | 0.0.93 | python-skills, py, development, coding-style, pep8, best-practices |
| `typescript` | TypeScript 开发插件 - 提供 TypeScript 开发规范、最佳实践和代码智能支持                 | 0.0.93 | typescript-skills, ts, development, type-safety, strict-mode       |
| `javascript` | JavaScript 开发插件 - 提供 JavaScript（ES2024-2025）开发规范、最佳实践和代码智能支持   | 0.0.93 | javascript-skills, js, es2024, es2025, development, async-await    |
| `flutter`    | Flutter 开发插件 - 提供 Flutter 应用开发规范、设计系统应用、状态管理指导和代码智能支持 | 0.0.93 | flutter-skills, dart, mobile, development, best-practices          |
| `naming`     | 命名规范插件 - 提供跨编程语言的统一命名规范指南                                        | 0.0.93 | naming-skills, coding-style, conventions, best-practices           |

### 框架插件 (frame/)

#### Golang 框架

| 插件名称   | 描述                                                                 | 版本   | 标签                                    |
| ---------- | -------------------------------------------------------------------- | ------ | --------------------------------------- |
| `fasthttp` | fasthttp-skills 高性能 HTTP 库插件 - 基于零拷贝和对象复用的高性能 HTTP 服务 | 0.0.93 | fasthttp-skills, http, performance, go         |
| `gin`      | Gin Web 框架插件 - 基于 httprouter 的高性能 Web 开发                 | 0.0.93 | gin-skills, web, framework, go                 |
| `go-zero`  | go-zero 微服务框架插件 - 云原生 Go 微服务开发                        | 0.0.93 | go-zero, microservice, cloud-native, go |
| `gofiber`  | Go Fiber Web 框架插件 - 基于 fasthttp-skills 的高性能 Web 开发              | 0.0.93 | fiber, web, framework, fasthttp-skills, go     |
| `gorm`     | GORM ORM 库插件 - 完整的 Go ORM 开发规范和最佳实践                   | 0.0.93 | gorm-skills, orm, database, go                 |
| `gorm-gen` | gorm-gen-skills 代码生成工具插件 - 类型安全的 GORM 代码生成                 | 0.0.93 | gorm-gen-skills, code-generation, orm, go      |
| `lrpc`     | lrpc 高性能 RPC 框架插件 - 基于fasthttp的轻量级 RPC 框架             | 0.0.93 | lrpc, rpc, framework, go                |

#### JavaScript/TypeScript 框架

| 插件名称 | 描述                                                             | 版本   | 标签                                   |
| -------- | ---------------------------------------------------------------- | ------ | -------------------------------------- |
| `react`  | React 18+ 开发插件 - 现代 React 开发规范、Hooks、状态管理        | 0.0.93 | react-skills, react18, hooks, frontend        |
| `vue`    | Vue 3 开发插件 - Vue 3 开发规范、Composition API、Pinia          | 0.0.93 | vue-skills, vue3, composition-api, frontend   |
| `nextjs` | Next.js 16+ 全栈开发插件 - App Router、Server Components         | 0.0.93 | nextjs-skills, fullstack, app-router, react-skills   |
| `antd`   | Ant Design 5.x 企业级 UI 组件库插件 - 设计系统、组件库、主题定制 | 0.0.93 | antd-skills, ant-design, ui-components, react-skills |

## 快速开始

### 环境要求

- **Python**: >= 3.11
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
# 顶层插件
/plugin install task@ccplugin-market
/plugin install llms@ccplugin-market
/plugin install notify@ccplugin-market
/plugin install version@ccplugin-market

# 工具插件
/plugin install deepresearch@ccplugin-market
/plugin install git@ccplugin-market
/plugin install semantic@ccplugin-market

# 语言插件
/plugin install golang@ccplugin-market
/plugin install python@ccplugin-market
/plugin install typescript@ccplugin-market
/plugin install javascript@ccplugin-market
/plugin install flutter@ccplugin-market
/plugin install naming@ccplugin-market

# 框架插件 - Golang
/plugin install gin@ccplugin-market
/plugin install gorm@ccplugin-market
/plugin install fasthttp@ccplugin-market
/plugin install go-zero@ccplugin-market
/plugin install gofiber@ccplugin-market
/plugin install gorm-gen@ccplugin-market
/plugin install lrpc@ccplugin-market

# 框架插件 - JavaScript/TypeScript
/plugin install react@ccplugin-market
/plugin install vue@ccplugin-market
/plugin install nextjs@ccplugin-market
/plugin install antd@ccplugin-market

# 主题插件
/plugin install style-glassmorphism@ccplugin-market
/plugin install style-neumorphism@ccplugin-market
/plugin install style-minimal@ccplugin-market
/plugin install style-dark@ccplugin-market
/plugin install style-neon@ccplugin-market
/plugin install style-retro@ccplugin-market
/plugin install style-brutalism@ccplugin-market
/plugin install style-pastel@ccplugin-market
/plugin install style-vibrant@ccplugin-market
/plugin install style-luxe@ccplugin-market
/plugin install style-highcontrast@ccplugin-market
/plugin install style-gradient@ccplugin-market
/plugin install style-healing@ccplugin-market
```

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

## 插件缓存清理

### 清理旧插件版本

如果 `~/.claude/plugins/cache/` 目录中积累了很多旧版本的插件，可以使用 `clean` 命令自动清理：

```bash
# 预览将要删除的内容（不实际删除）
clean --dry-run
clean -d

# 实际执行清理
clean

# 或通过 uvx 远程执行
uvx --from git+https://github.com/lazygophers/ccplugin clean
uvx --from git+https://github.com/lazygophers/ccplugin clean --dry-run
```

这个命令会：

- 扫描 `~/.claude/plugins/cache/` 目录下所有市场的插件版本
- 为每个插件保留最新版本，删除所有旧版本
- 输出清理的详细信息和释放的空间

#### 选项

| 选项            | 说明                                 |
| --------------- | ------------------------------------ |
| `--dry-run, -d` | 仅预览将要删除的内容，不执行实际删除 |
| `--help, -h`    | 显示帮助信息                         |

## 常见问题

### 如何安装插件？

```bash
# 从市场安装（推荐）
/plugin install task@ccplugin-market
/plugin install semantic@ccplugin-market
/plugin install git@ccplugin-market
/plugin install python@ccplugin-market
/plugin install golang@ccplugin-market

# 或从本地目录安装（开发时使用）
/plugin install ./plugins/task
/plugin install ./plugins/tools/semantic
```

### 如何开发新插件？

1. 复制模板：`cp -r plugins/template my-new-plugin`
2. 修改配置：编辑 `.claude-plugin/plugin.json`
3. 实现功能：
    - 在 `commands/` 目录下添加自定义命令
    - 在 `agents/` 目录下添加子代理
    - 在 `skills/` 目录下添加技能
    - 在 `hooks/` 目录下添加钩子（可选）
    - 在 `scripts/` 目录下添加脚本（可选）
    - 在 `README.md` 中添加插件文档（推荐）
    - 在 `AGENT.md` 中添加子代理文档（推荐,用于插件的系统提示词注入）
4. 测试插件：`/plugin install ./my-new-plugin` 或 `/plugin install my-new-plugin@ccplugin-market`
5. 提交市场：更新 `marketplace.json` 并提交 PR

### 为什么强制使用 uv？

uv 提供快速的依赖管理和虚拟环境，确保依赖隔离和版本一致性，避免全局 Python 环境污染。uv 的执行速度比传统的 pip 和 virtualenv 快数倍，能够显著提高开发效率。

### 插件数据存储在哪里？

每个插件的数据存储在项目目录的 `.lazygophers/ccplugin/<plugin-name>/` 目录下，自动被 `.gitignore` 忽略。

### 如何更新插件？

插件会随着 Claude Code 的更新自动更新，或者您可以手动重新安装插件来获取最新版本：

```bash
/plugin install task@ccplugin-market --force
```

## 许可证

AGPL-3.0-or-later - 详见 [LICENSE](LICENSE)

## 贡献指南

我们欢迎社区贡献！如果您想为 CCPlugin Market 贡献代码或插件，请遵循以下步骤：

1. Fork 本仓库
2. 创建您的特性分支：`git checkout -b feature/my-new-feature`
3. 提交您的更改：`git commit -m "Add some feature"`
4. 推送到分支：`git push origin feature/my-new-feature`
5. 提交 Pull Request

请确保您的代码符合我们的开发规范，并通过所有测试。
