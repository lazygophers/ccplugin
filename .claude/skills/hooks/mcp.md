# MCP 工具钩子

## MCP 工具命名

MCP 工具的钩子使用以下命名格式：

```
mcp__<server_name>__<tool_name>
```

### 示例

```
mcp__github__create_issue
mcp__filesystem__read_file
mcp__web-search__search
```

## 配置 MCP 工具钩子

### 基本格式

```json
{
  "PreToolUse": {
    "mcp__server__tool": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "确认使用 MCP 工具 ${pending_tool}：${pending_command}"
          }
        ]
      }
    ]
  }
}
```

### 完整示例

```json
{
  "PreToolUse": {
    "mcp__filesystem__*": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash scripts/validate-fs-access.sh \"${pending_path}\""
          }
        ]
      }
    ]
  },
  "PostToolUse": {
    "mcp__github__create_issue": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash scripts/log-github-issue.sh"
          }
        ]
      }
    ]
  }
}
```

## 通配符匹配

| 模式 | 匹配 |
|------|------|
| `mcp__server__tool` | 精确匹配 |
| `mcp__server__*` | server 下的所有工具 |
| `mcp__*__*` | 所有 MCP 工具 |

### 示例

```json
{
  "PreToolUse": {
    "mcp__github__*": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "确认使用 GitHub MCP 工具"
          }
        ]
      }
    ]
  },
  "PreToolUse": {
    "mcp__*__read*": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash scripts/log-read.sh"
          }
        ]
      }
    ]
  }
}
```

## 常见 MCP 服务器

| 服务器 | 工具前缀 |
|--------|----------|
| filesystem | `mcp__filesystem__` |
| github | `mcp__github__` |
| web-search | `mcp__web-search__` |
| web-reader | `mcp__web-reader__` |
| sequential-thinking | `mcp__sequential-thinking__` |

## 变量使用

MCP 工具钩子可使用以下变量：

| 变量 | 说明 |
|------|------|
| `${tool_name}` | 工具完整名称 |
| `${pending_command}` | 待执行的命令 |
| `${pending_args}` | 工具参数 |

```json
{
  "PreToolUse": {
    "mcp__github__create_issue": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "确认创建 GitHub Issue：${pending_command}"
          }
        ]
      }
    ]
  }
}
```

## 相关文档

- [事件类型](events.md)
- [配置格式](config.md)
- [钩子输入](input.md)
