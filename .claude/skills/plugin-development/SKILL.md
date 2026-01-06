---
name: plugin-development
description: Claude Code 插件开发技能。当用户需要创建新插件、修改插件结构、实现插件功能或调试插件时自动激活。提供 plugin.json 格式、commands/agents/skills 规范、目录结构和最佳实践指导。
auto-activate: always:true
allowed-tools: Read, Write, Edit, Glob, Bash, TodoWrite
---

# Claude Code 插件开发

## 核心规范

### plugin.json 格式（必需）

每个插件必须有 `.claude-plugin/plugin.json` 清单文件：

```json
{
  "name": "plugin-name",           // 必需：kebab-case
  "version": "1.0.0",              // 推荐：语义化版本
  "description": "插件描述",        // 必需：清晰说明
  "author": {                      // 推荐
    "name": "作者名",
    "email": "email@example.com",
    "url": "https://github.com/author"
  },
  "keywords": ["tag1", "tag2"],    // 推荐：便于发现
  "commands": "./commands/",       // 可选
  "agents": "./agents/",           // 可选
  "skills": "./skills/"            // 可选
}
```

### 目录结构（强制）

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json         # 必需：插件清单
├── commands/               # 可选：自定义命令
├── agents/                 # 可选：子代理
├── skills/                 # 可选：技能
│   └── skill-name/
│       └── SKILL.md        # 必需：大写
├── hooks/                  # 可选：钩子
│   └── hooks.json
└── README.md               # 推荐：文档
```

**重要**：`commands/`、`agents/`、`skills/` 必须在插件根目录，不能放在 `.claude-plugin/` 内。

## Skills 规范

### SKILL.md 格式

```yaml
---
name: skill-name
description: 清晰描述技能用途和使用时机
auto-activate: always:true  # 可选
allowed-tools: Read, Grep   # 可选
model: sonnet               # 可选
---
# 技能名称

## 使用场景
描述何时自动激活。

## 指导原则
提供详细指令。
```

### Frontmatter 字段

| 字段 | 必需 | 描述 |
|------|------|------|
| `name` | 是 | 技能名称（小写、数字、连字符，最多64字符） |
| `description` | 是 | 用途和使用时机（最多1024字符） |
| `auto-activate` | 否 | 自动激活条件 |
| `allowed-tools` | 否 | 允许的工具列表 |
| `model` | 否 | 使用的模型 |

## Commands 规范

### 命令格式

```markdown
---
description: 简洁描述
argument-hint: [args]       # 可选
allowed-tools: Bash(*)      # 可选
model: sonnet               # 可选
---
# 命令名称

详细指令。
```

### 参数处理

- `$ARGUMENTS` - 捕获所有参数
- `$1`, `$2` - 位置参数

### Bash 命令

```markdown
---
allowed-tools: Bash(git add:*), Bash(git status:*)
---
## Context
- 当前状态: !`git status`
- 差异: !`git diff HEAD`
```

## Agents 规范

### 代理格式

```markdown
---
name: agent-name
description: 代理用途描述
tools: Read, Write, Bash     # 可选
model: sonnet                # 可选
permissionMode: default      # 可选
skills: skill1, skill2       # 可选
---
代理系统提示词。
```

### 配置字段

| 字段 | 必需 | 描述 |
|------|------|------|
| `name` | 是 | 唯一标识符（小写和连字符） |
| `description` | 是 | 用途描述 |
| `tools` | 否 | 工具列表 |
| `model` | 否 | 模型别名或 'inherit' |
| `permissionMode` | 否 | 权限模式 |
| `skills` | 否 | 自动加载的技能 |

## 开发工作流

### 创建新插件

1. 使用模板：
   ```bash
   cp -r plugins/template my-new-plugin
   ```

2. 修改配置：
   - 更新 `plugin.json`
   - 设置 name、description、author

3. 实现功能：
   - 在 `commands/` 添加命令
   - 在 `agents/` 添加代理
   - 在 `skills/` 添加技能

4. 本地测试：
   ```bash
   /plugin install ./my-new-plugin
   ```

### 命名规范

- **插件名称**：kebab-case（如 `my-awesome-plugin`）
- **技能名称**：小写、数字、连字符（如 `code-reviewer`）
- **代理名称**：小写和连字符（如 `security-auditor`）
- **命令名称**：简洁描述性（如 `format-code`）

### 版本管理

遵循语义化版本：`MAJOR.MINOR.PATCH`
- MAJOR：破坏性变更
- MINOR：新功能
- PATCH：Bug 修复

## 环境变量

- `${CLAUDE_PLUGIN_ROOT}` - 插件目录绝对路径
- `${CLAUDE_PLUGIN_LSP_LOG_FILE}` - LSP 日志路径

## 最佳实践

1. **清晰描述**：每个组件都要有清晰的 description
2. **模块化**：保持插件单一职责
3. **文档化**：为每个插件提供 README.md
4. **测试**：本地测试后再发布
5. **版本管理**：使用语义化版本
6. **关键词**：添加 relevant keywords 便于发现

## 常见问题

**Q: commands/agents/skills 可以放在 .claude-plugin/ 内吗？**
A: 不可以，必须在插件根目录。

**Q: plugin.json 哪些字段是必需的？**
A: 只有 `name` 是必需的，但强烈建议添加 `description` 和 `author`。

**Q: 如何调试插件？**
A: 使用 `/plugin install ./plugin-path` 本地安装测试。

## 参考资源

- [官方插件文档](https://code.claude.com/docs/en/plugins.md)
- [插件市场规范](https://code.claude.com/docs/en/plugin-marketplaces.md)
- [项目 CLAUDE.md](../CLAUDE.md)
