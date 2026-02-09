# 钩子配置格式

## 标准结构

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "ToolPattern",
        "hooks": [
          {
            "type": "command",
            "command": "your-command-here",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

## 字段说明

### type（必需）

钩子执行类型：

```json
{ "type": "command" }
{ "type": "prompt" }
```

### command（command 类型必需）

要执行的 bash 命令：

```json
{
  "type": "command",
  "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/check.sh"
}
```

### prompt（prompt 类型必需）

发送给 LLM 的提示：

```json
{
  "type": "prompt",
  "prompt": "评估是否应继续：$ARGUMENTS"
}
```

### timeout（可选）

超时时间（秒），默认 60 秒：

```json
{
  "type": "command",
  "command": "bash scripts/long-running.sh",
  "timeout": 120
}
```

### matcher（部分事件必需）

工具名称匹配模式：

```json
{
  "matcher": "Write|Edit"
}
```

## 完整示例

```json
{
  "PreToolUse": {
    "Bash": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "确认执行命令：${pending_command}"
          }
        ]
      }
    ],
    "Write": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "确认写入文件：${pending_path}"
          }
        ]
      }
    ]
  },
  "PostToolUse": {
    "Edit|Write": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/format.sh"
          }
        ]
      }
    ]
  },
  "SessionStart": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "bash scripts/init.sh"
        }
      ]
    }
  ]
}
```

## 配置位置

| 位置 | 用途 |
|------|------|
| `~/.claude/settings.json` | 用户级设置 |
| `.claude/settings.json` | 项目设置 |
| `.claude/settings.local.json` | 本地项目设置 |
| 插件 `.claude-plugin/plugin.json` 的 `hooks` 字段 | 插件 hooks |

## 项目特定脚本

使用 `$CLAUDE_PROJECT_DIR` 引用项目中的脚本：

```json
{
  "PostToolUse": {
    "Write|Edit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/check-style.sh"
          }
        ]
      }
    ]
  }
}
```

## 环境变量

| 变量 | 说明 |
|------|------|
| `$CLAUDE_PROJECT_DIR` | 项目根目录 |
| `$CLAUDE_ENV_FILE` | SessionStart 持久化文件 |
| `$CLAUDE_CODE_REMOTE` | 远程环境标识 |
