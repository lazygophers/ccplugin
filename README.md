# CCPlugin Market

> Claude Code 插件市场 - 提供高质量插件和开发模板

## 简介

CCPlugin Market 是一个为 Claude Code 提供插件的集中市场。我们提供了一系列经过验证的高质量插件，帮助开发者提高工作效率，覆盖项目管理、代码搜索、Git 操作、多语言开发等多个领域。

## 快速开始

### 一键安装（推荐）

使用 `uvx` 一键安装市场和插件：

```bash
# 安装市场和指定插件
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin <插件名>@ccplugin-market

# 示例：安装 Python 插件
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin python@ccplugin-market

# 示例：安装多个插件
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin python@ccplugin-market golang@ccplugin-market git@ccplugin-market
```

### 传统方式安装

```bash
# 1. 添加市场
claude plugin marketplace add lazygophers/ccplugin

# 2. 安装插件
claude plugin install <插件名>@ccplugin-market
```

### 在 Claude Code 中安装

```bash
# 方式 1: 直接安装插件（自动添加市场）
/plugin install python@ccplugin-market

# 方式 2: 先添加市场再安装
/plugin marketplace add lazygophers/ccplugin
/plugin install python@ccplugin-market
```

## 可用插件

### 工具插件

| 插件名称 | 描述 | 关键词 |
|---------|------|--------|
| `git` | Git 操作插件 - 提供完整的 Git 操作支持，包括提交管理、Pull Request 管理和 .gitignore 管理 | git, commit, pr, workflow |
| `deepresearch` | 深度研究插件 - 基于图思维框架的多智能体深度研究系统 | research, analysis, multi-agent |
| `version` | 版本号管理插件 - 提供 SemVer 版本管理，支持自动版本更新 | semver, versioning, automation |
| `env` | 环境处理插件 - 从 .env 文件加载环境变量并注入会话 | env, dotenv, config |
| `notify` | 系统通知插件 - 跨平台系统通知支持 | notification, macos, linux, windows |
| `memory` | 智能记忆插件 - 提供 URI 寻址的记忆存储和跨会话持久化 | memory, persistence, sqlite |

### 语言插件

| 插件名称 | 描述 | 关键词 |
|---------|------|--------|
| `python` | Python 开发插件 - 提供 Python 开发规范、最佳实践和代码智能支持 | python, pep8, type-hints, testing |
| `golang` | Golang 开发插件 - 提供 Golang 开发规范、最佳实践和 LSP 支持 | golang, go, gopls, best-practices |
| `typescript` | TypeScript 开发插件 - 提供 TypeScript 开发规范和类型安全支持 | typescript, ts, type-safety, strict-mode |
| `javascript` | JavaScript 开发插件 - 提供 ES2024-2025 开发规范 | javascript, js, es2024, async-await |
| `rust` | Rust 开发插件 - 提供 Rust 开发规范和所有权系统指导 | rust, ownership, async, memory-safety |
| `java` | Java 开发插件 - 提供 Java 21+ 开发规范和 Spring Boot 指导 | java, spring-boot, jvm, performance |
| `c` | C 开发插件 - 提供 C11/C17 开发规范和系统编程指导 | c, c11, system-programming, posix |
| `cpp` | C++ 开发插件 - 提供 C++17/23 开发规范和现代 C++ 指导 | cpp, c++17, stl, concurrency |
| `csharp` | C# 开发插件 - 提供 C# 12/.NET 8 开发规范 | csharp, .net8, linq, async-await |
| `flutter` | Flutter 开发插件 - 提供 Flutter 应用开发规范和状态管理指导 | flutter, dart, mobile, state-management |
| `markdown` | Markdown 开发插件 - 提供 Markdown 编写规范和技术文档指导 | markdown, documentation, technical-writing |
| `naming` | 命名规范插件 - 提供跨编程语言的统一命名规范指南 | naming, conventions, code-style |

### Office 插件

| 插件名称 | 描述 | 关键词 |
|---------|------|--------|
| `office-xlsx` | Excel 插件 - 提供 xlsx 文件读写、数据分析功能 | xlsx, excel, spreadsheet, mcp |
| `office-docx` | Word 插件 - 提供 docx 文件读写、段落格式化功能 | docx, word, document, mcp |
| `office-pptx` | PowerPoint 插件 - 提供 pptx 文件读写、幻灯片操作功能 | pptx, powerpoint, presentation, mcp |

### 主题插件

| 插件名称 | 描述 |
|---------|------|
| `style-glassmorphism` | 玻璃态设计风格 - 模糊、透明、分层效果 |
| `style-neumorphism` | 新拟态设计风格 - 柔和阴影、浮起效果 |
| `style-minimal` | 极简主义设计风格 - 留白、简洁排版 |
| `style-dark` | 暗黑模式设计风格 - 深色背景、高对比 |
| `style-neon` | 霓虹赛博设计风格 - 发光效果、高饱和色彩 |
| `style-retro` | 复古怀旧设计风格 - 80-90s 审美、温暖色调 |
| `style-brutalism` | 野兽派设计风格 - 原始边界、大胆排版 |
| `style-pastel` | 柔和粉彩设计风格 - 淡雅色彩、温柔质感 |
| `style-vibrant` | 充满活力设计风格 - 高对比、高饱和色彩 |
| `style-luxe` | 奢华高端设计风格 - 金色元素、精致排版 |
| `style-highcontrast` | 高对比无障碍设计风格 - WCAG AAA 标准 |
| `style-gradient` | 渐变艺术设计风格 - 流动渐变、色彩过渡 |
| `style-healing` | 治愈系极简实用风 - 莫兰迪配色、情感化温度 |

### 其他插件

| 插件名称 | 描述 | 关键词 |
|---------|------|--------|
| `llms` | llms.txt 标准插件 - 通过 Agent 自动生成符合 llms.txt 规范的文件 | llms.txt, documentation, standard |
| `template` | 插件开发模板 - 快速创建新插件的基础结构 | template, development |

## 安装示例

### 安装语言插件

```bash
# Python 开发
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin python@ccplugin-market

# Golang 开发
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin golang@ccplugin-market

# TypeScript 开发
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin typescript@ccplugin-market

# Rust 开发
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin rust@ccplugin-market
```

### 安装工具插件

```bash
# Git 操作
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin git@ccplugin-market

# 深度研究
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin deepresearch@ccplugin-market

# 智能记忆
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin memory@ccplugin-market
```

### 安装 Office 插件

```bash
# Excel 操作
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin office-xlsx@ccplugin-market

# Word 操作
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin office-docx@ccplugin-market

# PowerPoint 操作
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin office-pptx@ccplugin-market
```

## 环境要求

- **Python**: >= 3.11
- **uv**: Python 包管理器和执行器
- **Claude Code**: 最新版本

### 安装 uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 验证安装
uv --version
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
├── scripts/                # 脚本（可选）
│   └── script.py
├── README.md               # 插件文档
└── CHANGELOG.md            # 版本历史
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

### 项目文档

- [CLAUDE.md](CLAUDE.md) - 项目开发规范和指导
- [CHANGELOG.md](CHANGELOG.md) - 版本变更历史

## 插件缓存清理

```bash
# 预览将要删除的内容
uvx --from git+https://github.com/lazygophers/ccplugin.git@master clean --dry-run

# 实际执行清理
uvx --from git+https://github.com/lazygophers/ccplugin.git@master clean
```

## 常见问题

### 如何安装插件？

```bash
# 推荐：一键安装
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin python@ccplugin-market

# 或：传统方式
claude plugin marketplace add lazygophers/ccplugin
claude plugin install python@ccplugin-market
```

### 如何更新插件？

```bash
# 重新安装即可更新
uvx --from git+https://github.com/lazygophers/ccplugin.git@master install lazygophers/ccplugin python@ccplugin-market
```

### 如何开发新插件？

1. 复制模板：`cp -r plugins/template my-new-plugin`
2. 修改配置：编辑 `.claude-plugin/plugin.json`
3. 实现功能：添加命令、代理、技能
4. 测试插件：`/plugin install ./my-new-plugin`
5. 提交市场：更新 `marketplace.json` 并提交 PR

## 许可证

AGPL-3.0-or-later - 详见 [LICENSE](LICENSE)

## 贡献指南

我们欢迎社区贡献！

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/my-new-feature`
3. 提交更改：`git commit -m "Add some feature"`
4. 推送分支：`git push origin feature/my-new-feature`
5. 提交 Pull Request
