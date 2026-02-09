# 钩子事件类型

## 事件概览

| 事件 | 类别 | 时机 | 匹配器 |
|------|------|------|--------|
| `PreToolUse` | 工具 | 工具使用前 | 需要 |
| `PostToolUse` | 工具 | 工具使用后 | 需要 |
| `PermissionRequest` | 权限 | 权限请求时 | 需要 |
| `Notification` | 通知 | 发送通知时 | 需要 |
| `UserPromptSubmit` | 会话 | 用户提交前 | 不需要 |
| `Stop` | 会话 | 停止响应时 | 不需要 |
| `SubagentStop` | 子进程 | 子进程停止时 | 不需要 |
| `PreCompact` | 压缩 | 上下文压缩前 | 需要 |
| `SessionStart` | 会话 | 会话开始时 | 需要 |
| `SessionEnd` | 会话 | 会话结束时 | 不需要 |

## PreToolUse

**时机：** 工具创建参数之后、处理调用之前

**用途：** 验证、确认、拦截工具调用

**匹配器：** Bash, Write, Edit, Read, Grep, Glob 等

```json
{
  "PreToolUse": {
    "Bash": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash scripts/validate.sh"
          }
        ]
      }
    ]
  }
}
```

## PostToolUse

**时机：** 工具成功完成后立即

**用途：** 日志、通知、后处理

**匹配器：** 与 PreToolUse 相同

```json
{
  "PostToolUse": {
    "Write": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash scripts/format.sh"
          }
        ]
      }
    ]
  }
}
```

## PermissionRequest

**时机：** 向用户显示权限对话框时

**用途：** 自动允许或拒绝权限请求

```json
{
  "PermissionRequest": {
    "Bash": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash scripts/auto-approve.sh"
          }
        ]
      }
    ]
  }
}
```

## Notification

**时机：** Claude Code 发送通知时

**匹配器类型：**

| 匹配器 | 说明 |
|--------|------|
| `permission_prompt` | 权限请求 |
| `idle_prompt` | 空闲提示（60+ 秒后） |
| `auth_success` | 身份验证成功 |
| `elicitation_dialog` | MCP 工具输入请求 |

```json
{
  "Notification": [
    {
      "matcher": "permission_prompt",
      "hooks": [
        {
          "type": "command",
          "command": "bash scripts/permission-alert.sh"
        }
      ]
    }
  ]
}
```

## UserPromptSubmit

**时机：** 用户提交提示时，在 Claude 处理之前

**用途：** 添加上下文、验证、阻止提示

```json
{
  "UserPromptSubmit": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "bash scripts/validate-prompt.sh"
        }
      ]
    }
  ]
}
```

## Stop

**时机：** 主 Claude Code agent 完成响应时

**注意：** 如果停止是由于用户中断，不运行

```json
{
  "Stop": [
    {
      "hooks": [
        {
          "type": "prompt",
          "prompt": "评估是否应停止：$ARGUMENTS"
        }
      ]
    }
  ]
}
```

## SubagentStop

**时机：** Claude Code subagent 完成响应时

```json
{
  "SubagentStop": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "bash scripts/sync-results.sh"
        }
      ]
    }
  ]
}
```

## PreCompact

**时机：** Claude Code 即将运行压缩操作之前

**匹配器：**

| 匹配器 | 说明 |
|--------|------|
| `manual` | 从 `/compact` 调用 |
| `auto` | 自动压缩（上下文已满） |

```json
{
  "PreCompact": [
    {
      "matcher": "manual",
      "hooks": [
        {
          "type": "command",
          "command": "bash scripts/prepare-compact.sh"
        }
      ]
    }
  ]
}
```

## SessionStart

**时机：** Claude Code 启动或恢复会话时

**匹配器：**

| 匹配器 | 说明 |
|--------|------|
| `startup` | 从启动调用 |
| `resume` | 从 `--resume` 调用 |
| `clear` | 从 `/clear` 调用 |
| `compact` | 从压缩调用 |

```json
{
  "SessionStart": [
    {
      "matcher": "startup",
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

### 持久化环境变量

SessionStart hooks 可使用 `CLAUDE_ENV_FILE` 环境变量：

```bash
#!/bin/bash
if [ -n "$CLAUDE_ENV_FILE" ]; then
  echo 'export NODE_ENV=production' >> "$CLAUDE_ENV_FILE"
fi
```

## SessionEnd

**时机：** Claude Code 会话结束时

**结束原因（reason 字段）：**

| 值 | 说明 |
|------|------|
| `clear` | 使用 /clear 清除 |
| `logout` | 用户已注销 |
| `prompt_input_exit` | 提示输入时退出 |
| `other` | 其他原因 |

```json
{
  "SessionEnd": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "bash scripts/cleanup.sh"
        }
      ]
    }
  ]
}
```

## 工具匹配器速查

| 匹配器 | 工具 |
|--------|------|
| `Task` | Subagent 任务 |
| `Bash` | Shell 命令 |
| `Glob` | 文件模式匹配 |
| `Grep` | 内容搜索 |
| `Read` | 文件读取 |
| `Edit` | 文件编辑 |
| `Write` | 文件写入 |
| `WebFetch` | Web 获取 |
| `WebSearch` | Web 搜索 |
| `mcp__server__tool` | MCP 工具 |
