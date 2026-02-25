# Plugin Template

> 插件开发模板 - 快速创建新插件的基础结构

## 说明

这是一个插件开发模板，用于快速创建新的 Claude Code 插件。

## 使用方法

### 1. 复制模板

```bash
# 复制整个模板目录
cp -r plugins/template my-new-plugin

# 进入新插件目录
cd my-new-plugin
```

### 2. 修改配置

编辑 `.claude-plugin/plugin.json`：

```json
{
  "name": "my-new-plugin",
  "version": "0.0.1",
  "description": "我的插件描述",
  "author": {
    "name": "Your Name",
    "email": "you@example.com",
    "url": "https://github.com/yourusername"
  },
  "homepage": "https://github.com/yourusername/my-new-plugin",
  "repository": "https://github.com/yourusername/my-new-plugin",
  "license": "AGPL-3.0-or-later"
}
```

### 3. 添加组件

#### Command

在 `commands/` 创建 `.md` 文件：

```markdown
---
name: command-name
description: 命令简短描述
---

# 命令名称

命令详细说明。

**用法**：
```
/plugin-name command-name
```
```

#### Agent

在 `agents/` 创建 `.md` 文件：

```markdown
---
name: agent-name
description: Agent 简短描述
context: fork
allowed-tools:
  - Read
  - Write
  - Bash
---

# Agent 名称

你是 Agent 系统提示词...
```

#### Skill

在 `skills/` 创建目录和 `SKILL.md`：

```markdown
---
name: skill-name
description: Skill 简短描述
---

# Skill 名称

Skill 使用说明...
```

### 4. 安装测试

```bash
# 本地安装
/plugin install ./my-new-plugin

# 测试功能
/plugin-name command-name
```

## 目录结构

```
my-new-plugin/
├── .claude-plugin/
│   └── plugin.json          # 插件清单（必需）
├── scripts/                 # Python 脚本
│   ├── __init__.py
│   ├── main.py             # CLI 入口
│   ├── hooks.py            # Hook 处理器
│   └── mcp.py              # MCP 服务器
├── commands/               # 命令定义
├── agents/                 # 子代理定义
├── skills/                 # 技能定义
├── hooks/
│   └── hooks.json          # Hook 配置
├── .mcp.json               # MCP 配置
├── .lsp.json               # LSP 配置
├── pyproject.toml          # Python 配置
└── README.md               # 插件文档
```

## 编程语言规范

1. **Python（首选）** - 复杂逻辑、API 调用
2. **Bash（次选）** - 系统操作、快速脚本
3. **Markdown/JSON（必需）** - 配置文件

## 检查清单

- [ ] 修改 `plugin.json` 所有字段
- [ ] 实现 `scripts/main.py`
- [ ] 添加命令/代理/技能
- [ ] 编写 README.md
- [ ] 本地测试通过

## 参考资源

- [.claude/skills/plugin-development/](../.claude/skills/plugin-development/)
- [CLAUDE.md](../../CLAUDE.md)
