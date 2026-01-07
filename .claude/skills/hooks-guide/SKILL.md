---
name: hooks-guide
description: Claude Code Hooks 指南技能。当用户需要使用 hooks 配置、定义事件钩子或在特定事件触发执行操作时自动激活。提供 hooks 格式、可用事件、钩子配置和最佳实践指导。
auto-activate: always:true
allowed-tools: Read, Write, Edit, Bash
---

# Claude Code Hooks 指南

## Hooks 概述

Hooks 允许插件在特定事件发生时自动执行命令或脚本。

## Hooks 配置

### hooks.json 格式

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "ToolName|Pattern",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/script.sh",
            "env": {
              "VAR": "value"
            }
          }
        ]
      }
    ]
  }
}
```

### 配置位置

1. **插件内**：`hooks/hooks.json`
2. **plugin.json 内联**：
   ```json
   {
     "hooks": {
       "SessionStart": [...]
     }
   }
   ```

## 可用事件

### 生命周期事件

| 事件 | 描述 |
|------|------|
| `SessionStart` | 会话开始时触发 |
| `SessionEnd` | 会话结束时触发 |
| `Stop` | 停止时触发 |

### 工具事件

| 事件 | 描述 |
|------|------|
| `PreToolUse` | 工具使用前触发 |
| `PostToolUse` | 工具使用后触发 |

### 交互事件

| 事件 | 描述 |
|------|------|
| `PermissionRequest` | 权限请求时触发 |
| `UserPromptSubmit` | 用户提交提示时触发 |

### 代理事件

| 事件 | 描述 |
|------|------|
| `SubagentStart` | 子代理启动时触发 |
| `SubagentStop` | 子代理停止时触发 |

### 通知事件

| 事件 | 描述 |
|------|------|
| `Notification` | 通知时触发 |

### 系统事件

| 事件 | 描述 |
|------|------|
| `PreCompact` | 压缩前触发 |

## Hook 配置详解

### matcher 字段

匹配工具名称或模式：

```json
{
  "matcher": "Write|Edit",              // 匹配 Write 或 Edit
  "matcher": "Bash(*)",                 // 匹配所有 Bash 工具
  "matcher": "Bash(git:*)",             // 匹配 git 命令
  "matcher": "*",                       // 匹配所有工具
}
```

### type 字段

钩子类型：

- `command`: 执行命令
- `function`: 调用函数（未来支持）

### command 字段

要执行的命令：

```json
{
  "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format.sh"
}
```

### env 字段

环境变量：

```json
{
  "env": {
    "CLAUDE_PLUGIN_ROOT": "${CLAUDE_PLUGIN_ROOT}",
    "CUSTOM_VAR": "value"
  }
}
```

## 环境变量

### 可用变量

| 变量 | 描述 |
|------|------|
| `${CLAUDE_PLUGIN_ROOT}` | 插件目录绝对路径 |
| `${CLAUDE_PLUGIN_LSP_LOG_FILE}` | LSP 日志文件路径 |

## 常用场景

### 代码格式化

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format-code.sh"
          }
        ]
      }
    ]
  }
}
```

### Git 提交前检查

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash(git commit:*)",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/pre-commit.sh"
          }
        ]
      }
    ]
  }
}
```

### 会话启动

```json
{
  "hooks": {
    "SessionStart": [
      {
        "type": "command",
        "command": "echo 'Plugin session started'"
      }
    ]
  }
}
```

### 文件保存通知

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/notify-save.sh"
          }
        ]
      }
    ]
  }
}
```

## Hook 脚本示例

### format-code.sh

```bash
#!/bin/bash

# 代码格式化脚本
echo "Formatting code..."

# 检查文件类型
FILE="$1"
EXT="${FILE##*.}"

case "$EXT" in
  py)
    black "$FILE"
    ;;
  js|ts)
    prettier --write "$FILE"
    ;;
  go)
    go fmt "$FILE"
    ;;
esac
```

### pre-commit.sh

```bash
#!/bin/bash

# 提交前检查
echo "Running pre-commit checks..."

# 运行测试
npm test

# 运行 lint
npm run lint

# 检查通过
if [ $? -eq 0 ]; then
  echo "Pre-commit checks passed"
  exit 0
else
  echo "Pre-commit checks failed"
  exit 1
fi
```

### notify-save.sh

```bash
#!/bin/bash

# 文件保存通知
echo "File saved: $1"

# 发送通知（macOS）
osascript -e "display notification \"File saved: $1\" with title \"Claude Code\""
```

## 最佳实践

### 1. 性能优化

- 避免在 hooks 中执行耗时操作
- 使用异步命令
- 缓存结果

### 2. 错误处理

```bash
#!/bin/bash
set -euo pipefail  # 严格模式
trap 'echo "Error on line $LINENO"' ERR  # 错误捕获
```

### 3. 日志记录

```bash
#!/bin/bash
LOG_FILE="${CLAUDE_PLUGIN_ROOT}/logs/hooks.log"
echo "[$(date)] Hook executed" >> "$LOG_FILE"
```

### 4. 权限管理

```bash
#!/bin/bash
# 确保脚本可执行
chmod +x "$0"
```

## 调试 Hooks

### 启用日志

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Hook triggered: $EVENT_NAME' >> ${CLAUDE_PLUGIN_ROOT}/hooks.log"
          }
        ]
      }
    ]
  }
}
```

### 测试 Hooks

```bash
# 手动执行脚本
./scripts/format-code.sh test.py

# 检查权限
ls -la scripts/
```

## 常见问题

**Q: hooks 可以有多个吗？**
A: 可以，一个事件可以配置多个 hooks。

**Q: 如何禁用某个 hook？**
A: 删除或注释掉对应的配置。

**Q: hooks 执行失败会怎样？**
A: 不会阻止主要操作，但会记录错误。

**Q: 如何在 hooks 中获取上下文？**
A: 使用环境变量和命令参数。

## 参考资源

- [官方 Hooks 指南](https://code.claude.com/docs/en/hooks-guide.md)
- [plugin-development skill](../.claude/skills/plugin-development/SKILL.md)
