---
name: plugin-organization-skills
description: CCPlugin 插件组织规范 - 定义插件的标准目录结构、配置文件、元数据和最佳实践
---

# CCPlugin 插件组织规范

## 快速导航

| 章节 | 内容 | 适用场景 |
|------|------|---------|
| **核心理念** | 设计原则、目录结构标准 | 快速入门 |
| **标准结构** | 完整的插件目录模板 | 创建新插件 |
| **元数据配置** | plugin.json 规范 | 插件配置 |
| **组件规范** | agents/commands/skills/hooks | 功能开发 |
| **命名约定** | 文件、目录、命名规范 | 命名参考 |
| **最佳实践** | 设计原则、常见模式 | 质量保证 |
| **快速模板** | 最小/完整插件模板 | 快速开始 |

## 核心理念

CCPlugin 插件生态追求**模块化、可发现、可维护**，通过标准化的目录结构和配置文件，使插件易于开发、安装和使用。

**三个支柱：**

1. **模块化** - 清晰的功能分离，agents/commands/skills/hooks 各司其职
2. **可发现** - 通过 plugin.json 声明元数据，Claude Code 自动发现和加载
3. **可维护** - 标准化的结构和命名，降低维护成本

## 版本要求

- **CCPlugin**: >= 0.0.90
- **Claude Code**: >= 1.0.0
- **Python**: >= 3.11（如插件包含 Python 代码）

## 强制规范

- ✅ **必须包含** `.claude-plugin/plugin.json`
- ✅ **必须包含** `pyproject.toml`（Python 插件）
- ✅ **必须使用** 标准目录结构
- ✅ **必须遵循** 命名约定
- ✅ **必须提供** README.md 文档

## 标准插件结构

### 完整结构模板

```
plugin-name/
├── .claude-plugin/             # 插件元数据目录（必需）
│   └── plugin.json            # 插件清单文件（必需）
│
├── scripts/                    # Python 代码目录（Python 插件必需）
│   ├── __init__.py            # 包初始化文件
│   ├── main.py                # CLI 入口
│   ├── <module>.py            # 业务逻辑模块
│   ├── hooks.py               # Hook 处理器
│   └── mcp.py                 # MCP 服务器
│
├── commands/                   # Claude Code 命令定义（可选）
│   ├── command-name.md        # 命令文档
│   └── ...
│
├── agents/                     # 子代理定义（可选）
│   ├── agent-name.md          # 代理配置
│   └── ...
│
├── skills/                     # 技能规范目录（可选）
│   ├── skill-name/            # 技能目录
│   │   └── SKILL.md           # 技能入口文件
│   └── ...
│
├── hooks/                      # Hook 配置目录（可选）
│   └── hooks.json             # Hook 事件配置
│
├── .mcp.json                  # MCP 服务器配置（可选）
├── .lsp.json                  # LSP 服务器配置（可选）
│
├── __init__.py                # 插件根包（可选）
├── pyproject.toml             # Python 项目配置（必需）
├── uv.lock                    # 依赖锁定文件（自动生成）
├── README.md                  # 插件文档（推荐）
└── CHANGELOG.md               # 版本变更记录（推荐）
```

### 简化结构（无 Python 代码）

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json            # 仅声明 agents/skills
│
├── agents/                    # 子代理定义
│   └── *.md
│
├── skills/                    # 技能规范
│   └── skill-name/SKILL.md
│
└── README.md                  # 插件文档
```

## 元数据配置

### plugin.json 规范

**必需字段：**

```json
{
  "name": "plugin-name",
  "version": "0.0.91",
  "description": "插件简短描述",
  "author": {
    "name": "作者名",
    "email": "email@example.com",
    "url": "https://github.com/user"
  },
  "homepage": "https://github.com/user/repo",
  "repository": "https://github.com/user/repo",
  "license": "AGPL-3.0-or-later"
}
```

**可选字段：**

```json
{
  "keywords": ["keyword1", "keyword2"],
  "commands": ["./commands/*.md"],
  "agents": ["./agents/*.md"],
  "skills": "./skills/",
  "mcpServers": "./.mcp.json",
  "lspServers": "./.lsp.json"
}
```

**字段说明：**

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `name` | string | ✅ | 插件唯一标识，小写字母、数字、连字符 |
| `version` | string | ✅ | 语义化版本号（major.minor.patch） |
| `description` | string | ✅ | 插件简短描述，建议 50-100 字 |
| `author` | object | ✅ | 作者信息，包含 name/email/url |
| `homepage` | string | ✅ | 项目主页 URL |
| `repository` | string | ✅ | 代码仓库 URL |
| `license` | string | ✅ | 开源协议标识（SPDX 格式） |
| `keywords` | array[] | ❌ | 搜索关键词 |
| `commands` | array[] | ❌ | 命令文件路径列表（glob 模式） |
| `agents` | array[] | ❌ | 代理文件路径列表（glob 模式） |
| `skills` | string | ❌ | 技能目录路径 |
| `mcpServers` | string | ❌ | MCP 配置文件路径 |
| `lspServers` | string | ❌ | LSP 配置文件路径 |

## 组件规范

### Commands（命令）

**目录结构：**
```
commands/
├── show.md                    # 命令文档
├── info.md
└── bump.md
```

**命令文档格式：**
```markdown
---
name: show
description: 显示版本信息
---

# 显示版本

显示当前项目的版本号。

**用法：**
```
/version show
```
```

**plugin.json 引用：**
```json
{
  "commands": [
    "./commands/show.md",
    "./commands/info.md"
  ]
}
```

### Agents（代理）

**目录结构：**
```
agents/
├── dev.md                     # 开发专家代理
├── test.md                    # 测试专家代理
└── debug.md                   # 调试专家代理
```

**代理文档格式：**
```markdown
---
name: dev
description: Python 开发专家
auto-activate: always:true
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# Python 开发专家

你是 Python 开发专家，专注于...

## 能力
- ...
```

**plugin.json 引用：**
```json
{
  "agents": [
    "./agents/dev.md",
    "./agents/test.md"
  ]
}
```

### Skills（技能）

**目录结构：**
```
skills/
├── python/                    # 技能目录
│   ├── SKILL.md               # 技能入口文件（必需）
│   ├── type-hints.md          # 子文档（可选）
│   └── testing.md
└── golang/
    ├── SKILL.md
    └── patterns/
        └── design-patterns.md
```

**技能入口格式：**
```markdown
---
name: python
description: Python 开发规范和最佳实践
---

# Python 开发规范

## 快速导航

| 文档 | 内容 | 适用场景 |
|------|------|---------|
| **SKILL.md** | 核心规范、命名约定 | 快速入门 |
| [type-hints.md](type-hints.md) | 类型提示使用指南 | 类型标注 |
```

**plugin.json 引用：**
```json
{
  "skills": "./skills/"
}
```

### Hooks（钩子）

**目录结构：**
```
hooks/
└── hooks.json                 # Hook 配置文件
```

**hooks.json 格式：**
```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "PLUGIN_NAME=plugin-name uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py hooks"
          }
        ]
      }
    ]
  }
}
```

**可用事件：**

| 事件 | 触发时机 | 用途 |
|------|----------|------|
| `SessionStart` | 会话开始时 | 初始化、环境检查 |
| `UserPromptSubmit` | 用户提交提示前 | 验证、预处理 |
| `SessionEnd` | 会话结束时 | 清理、日志记录 |

### MCP Servers

**目录结构：**
```
.mcp.json                     # MCP 配置文件（插件根目录）
```

**.mcp.json 格式：**
```json
{
  "mcpServers": {
    "server-name": {
      "command": "uv",
      "args": [
        "run",
        "${CLAUDE_PLUGIN_ROOT}/scripts/main.py",
        "mcp"
      ],
      "env": {
        "PLUGIN_NAME": "plugin-name"
      }
    }
  }
}
```

**环境变量：**

| 变量 | 说明 | 示例 |
|------|------|------|
| `CLAUDE_PLUGIN_ROOT` | 插件根目录（自动设置） | `/path/to/plugins/plugin-name` |
| `PLUGIN_NAME` | 插件名称（需在配置中设置） | `python` |

**plugin.json 引用：**
```json
{
  "mcpServers": "./.mcp.json"
}
```

### LSP Servers

**目录结构：**
```
.lsp.json                     # LSP 配置文件（插件根目录）
```

**.lsp.json 格式：**
```json
{
  "go": {
    "command": "gopls",
    "args": ["serve"],
    "extensionToLanguage": {
      ".go": "go"
    }
  },
  "python": {
    "command": "pylsp",
    "args": [],
    "extensionToLanguage": {
      ".py": "python"
    }
  }
}
```

**plugin.json 引用：**
```json
{
  "lspServers": "./.lsp.json"
}
```

## 命名约定

### 插件命名

**命名模式：**
```
{category}-{name}          # 功能类插件
code-{language}            # 语言支持插件
frame-{framework}          # 框架支持插件
tools-{tool}               # 工具类插件
```

**示例：**
```
version/                   # 版本管理插件
task/                      # 任务管理插件
code-python/               # Python 开发插件
code-golang/               # Golang 开发插件
frame-vue/                 # Vue 框架插件
tools-semantic/            # 语义搜索工具插件
```

### 文件命名

**约定：**

| 类型 | 约定 | 示例 |
|------|------|------|
| Python 模块 | `lowercase_with_underscores.py` | `main.py`, `hooks.py` |
| 命令文档 | `kebab-case.md` | `show-version.md`, `init-repo.md` |
| 代理文档 | `lowercase.md` | `dev.md`, `debug.md` |
| 技能目录 | `lowercase` | `python/`, `golang/` |
| 技能入口 | `SKILL.md`（大写） | `python/SKILL.md` |
| 配置文件 | `.name.json` | `.mcp.json`, `.lsp.json` |

### 变量命名

**环境变量：**
```bash
PLUGIN_NAME                 # 插件名称
CLAUDE_PLUGIN_ROOT          # 插件根目录（自动设置）
```

## 最佳实践

### 设计原则

| 原则 | 说明 | 示例 |
|------|------|------|
| **单一职责** | 一个插件专注一个功能领域 | version/ 仅负责版本管理 |
| **模块化** | 功能分离到 agents/skills/commands | 开发专家在 dev.md，测试规范在 skills/ |
| **声明式配置** | 使用 JSON/TOML 声明元数据 | plugin.json、.mcp.json |
| **文档优先** | 每个组件都有清晰的文档 | README.md + 命令/代理/技能文档 |
| **向后兼容** | 避免破坏性变更 | 使用语义化版本 |

### 文件组织

**推荐：**
```
plugin-name/
├── .claude-plugin/plugin.json   # 元数据
├── commands/                    # 用户接口
├── agents/                      # 专家代理
├── skills/                      # 编码规范
├── scripts/                     # 实现代码
├── hooks/hooks.json             # 事件集成
└── README.md                    # 用户文档
```

**避免：**
- ❌ 混合不同语言的代码在同一个插件
- ❌ 在 commands 中实现复杂逻辑（应在 agents/skills）
- ❌ 硬编码路径（使用环境变量）
- ❌ 缺少 README.md 文档

### 文档规范

**README.md 必需包含：**
```markdown
# Plugin Name

简短描述插件的功能。

## 功能特性

- 功能 1
- 功能 2

## 安装

```bash
/plugin install ./plugins/plugin-name
```

## 使用

### 命令

```bash
/plugin-command description
```

### Agents

| Agent | 说明 |
|-------|------|
| dev | 开发专家 |

### Skills

技能自动激活，详见 `skills/` 目录。

## 配置

可选配置项说明。

## 开发

开发指南和贡献指南。
```

## 快速模板

### 最小插件（仅 agents/skills）

**plugin.json:**
```json
{
  "name": "my-plugin",
  "version": "0.0.1",
  "description": "我的插件",
  "author": {
    "name": "Your Name",
    "email": "you@example.com",
    "url": "https://github.com/you"
  },
  "homepage": "https://github.com/you/my-plugin",
  "repository": "https://github.com/you/my-plugin",
  "license": "AGPL-3.0-or-later",
  "agents": ["./agents/dev.md"],
  "skills": "./skills/"
}
```

**README.md:**
```markdown
# My Plugin

我的插件说明。

## 安装

```bash
/plugin install ./plugins/my-plugin
```
```

### Python 插件（完整功能）

**目录结构：**
```
my-python-plugin/
├── .claude-plugin/plugin.json
├── scripts/
│   ├── __init__.py
│   └── main.py
├── commands/
│   └── run.md
├── pyproject.toml
└── README.md
```

**plugin.json:**
```json
{
  "name": "my-python-plugin",
  "version": "0.0.1",
  "description": "我的 Python 插件",
  "author": {
    "name": "Your Name",
    "email": "you@example.com",
    "url": "https://github.com/you"
  },
  "homepage": "https://github.com/you/my-python-plugin",
  "repository": "https://github.com/you/my-python-plugin",
  "license": "AGPL-3.0-or-later",
  "commands": ["./commands/run.md"],
  "mcpServers": "./.mcp.json"
}
```

**pyproject.toml:**
```toml
[project]
name = "my-python-plugin"
version = "0.0.1"
requires-python = ">=3.11"
dependencies = ["click>=8.3.1", "lib"]

[tool.uv.sources.lib]
git = "https://github.com/lazygophers/ccplugin"
subdirectory = "lib"
rev = "master"
```

**main.py:**
```python
from lib import logging
import click

@click.group()
def main():
    """My Plugin"""
    pass

@main.command()
def run():
    """Run the plugin"""
    click.echo("Hello from my plugin!")

if __name__ == "__main__":
    main()
```

## 参考资源

### 示例插件

| 插件 | 类型 | 特点 |
|------|------|------|
| `version/` | Python + Hooks | 完整的 Python 插件示例 |
| `code/python/` | Language + Skills | 语言插件参考 |
| `code/golang/` | Language + LSP | LSP 集成示例 |
| `task/` | Python + Agents | 代理使用示例 |
| `template/` | Plugin Template | 新插件模板 |

### 相关文档

- [Python 脚本组织规范](../python-script-organization/SKILL.md)
- [lib 共享库](https://github.com/lazygophers/ccplugin/tree/master/lib)
- [Claude Code 文档](https://docs.anthropic.com/)

### 工具链

- **uv**: Python 包管理器
- **Click**: CLI 框架
- **Rich**: 终端美化输出
- **pydantic**: 数据验证
