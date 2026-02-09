---
name: plugin-command-development
description: 插件命令开发指南 - 当用户需要为插件添加自定义命令时使用。覆盖命令 YAML frontmatter、参数处理、交互模式和文件引用。
context: fork
agent: command
---

# 插件命令开发指南

## 命令文件结构

```
commands/
└── my-command.md           # 命令文件
```

## YAML frontmatter

```yaml
---
name: my-command
description: 命令简短描述
mode: auto
---

# 命令说明

## 用法

`/my-command <param>`

## 参数

| 参数 | 说明 |
|------|------|
| `param` | 参数描述 |
```

### frontmatter 字段

| 字段 | 说明 | 必需 |
|------|------|------|
| `name` | 命令名称（用于 `/name` 调用） | 是 |
| `description` | 命令描述 | 是 |
| `mode` | 执行模式：`auto` / `interactive` / `restricted` | 否 |

### mode 说明

| 模式 | 说明 |
|------|------|
| `auto` | 自动执行，无需用户确认 |
| `interactive` | 交互式执行，可使用 `AskUserQuestion` |
| `restricted` | 限制模式，需要用户确认 |

## 参数处理

### 方式1：直接参数

```yaml
---
name: greet
description: 向用户问好
---
Hello, ${user_name}!
```

### 方式2：交互式输入

在命令内容中使用 `AskUserQuestion`：

```markdown
# 个性化问候

请问你的名字是什么？

<question>
{
  "header": "名字",
  "question": "请输入你的名字",
  "options": [
    {"label": "Alice", "description": "女性英文名"},
    {"label": "Bob", "description": "男性英文名"}
  ]
}
</question>
```

## 文件引用

引用项目或插件文件：

```
${CLAUDE_PROJECT_DIR}/path/to/file
${CLAUDE_PLUGIN_ROOT}/scripts/main.py
```

## 插件中注册命令

在 `plugin.json` 中引用：

```json
{
  "commands": [
    "./commands/my-command.md"
  ]
}
```

## 相关技能

- [plugin-development](plugin-development/SKILL.md) - 插件开发
- [plugin-skill-development](plugin-skill-development/SKILL.md) - 插件技能开发
