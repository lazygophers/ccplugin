# 钩子完整示例

## 基础配置

### PreToolUse - Bash 命令确认

```json
{
  "PreToolUse": {
    "Bash": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "确认执行 Bash 命令\n\n命令: ${pending_command}\n\n此命令将直接在您的系统上执行，请确认。"
          }
        ]
      }
    ]
  }
}
```

### PostToolUse - 操作日志

```json
{
  "PostToolUse": {
    "Bash": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash scripts/log.sh \"${tool_name}\""
          }
        ]
      }
    ]
  }
}
```

对应的 `scripts/log.sh`：

```bash
#!/bin/bash
TOOL=$1
DATE=$(date -Iseconds)
echo "[$DATE] $TOOL" >> ~/.claude/audit.log
```

### SessionStart - 会话初始化

```json
{
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

## 完整安全配置

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
    ],
    "Edit": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "确认编辑文件：${pending_path}"
          }
        ]
      }
    ]
  },
  "PostToolUse": {
    "Bash": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash scripts/log.sh"
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

## 会话管理

```json
{
  "SessionStart": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "bash scripts/load-env.sh"
        }
      ]
    }
  ],
  "SessionEnd": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "bash scripts/save-session.sh"
        }
      ]
    }
  ],
  "Stop": [
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

## 危险命令拦截

```json
{
  "PreToolUse": {
    "Bash": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "危险命令检测\n\n命令: ${pending_command}\n\n此命令可能涉及删除操作，请确认您已备份重要数据。"
          }
        ]
      }
    ]
  }
}
```

## 多钩子组合

```json
{
  "PreToolUse": {
    "Bash": [
      {
        "hooks": [
          { "type": "prompt", "prompt": "确认执行" },
          { "type": "command", "command": "bash scripts/pre-check.sh" }
        ]
      }
    ]
  },
  "PostToolUse": {
    "Bash": [
      {
        "hooks": [
          { "type": "command", "command": "bash scripts/post-process.sh" },
          { "type": "command", "command": "bash scripts/notify.sh" }
        ]
      }
    ]
  }
}
```

## 插件钩子示例

### golang 插件 hooks.json

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "PLUGIN_NAME=golang uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py hooks"
          }
        ]
      }
    ]
  }
}
```

### Python 钩子脚本

```python
#!/usr/bin/env python3
import json
import sys

from lib import logging
from lib.hooks import load_hooks

def handle_hook() -> None:
    """处理 hook 模式：从 stdin 读取 JSON 并记录。"""
    try:
        hook_data = load_hooks()
        event_name = hook_data.get("hook_event_name")
        logging.info(f"接收到事件: {event_name}")

    except json.JSONDecodeError as e:
        logging.error(f"JSON 解析失败: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Hook 处理失败: {e}")
        sys.exit(1)
```

## MCP 工具钩子

```json
{
  "PreToolUse": {
    "mcp__filesystem__*": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash scripts/validate-fs.sh"
          }
        ]
      }
    ],
    "mcp__github__create_issue": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "确认创建 GitHub Issue"
          }
        ]
      }
    ]
  }
}
```

## Bash 脚本模板

### 日志记录

```bash
#!/bin/bash
INPUT=$(cat)
EVENT=$(echo "$INPUT" | jq -r '.hook_event_name')
TOOL=$(echo "$INPUT" | jq -r '.tool_name')
DATE=$(date -Iseconds)
echo "[$DATE] Event: $EVENT, Tool: $TOOL" >> ~/.claude/hooks.log
```

### 安全检查

```bash
#!/bin/bash
INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command')
if echo "$CMD" | grep -qE "rm -rf|sudo rm"; then
    echo "危险命令被阻止"
    exit 2
fi
exit 0
```

## Python 脚本模板

```python
#!/usr/bin/env python3
import json
import sys

def handle_hook():
    data = json.load(sys.stdin)
    event = data.get("hook_event_name", "")
    tool = data.get("tool_name", "")

    # 根据事件处理
    if event == "PreToolUse":
        pass
    elif event == "PostToolUse":
        pass

    return 0

if __name__ == "__main__":
    sys.exit(handle_hook())
```
