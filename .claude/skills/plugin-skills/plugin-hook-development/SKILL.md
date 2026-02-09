---
name: plugin-hook-development
description: 插件钩子开发指南 - 当用户需要为插件添加事件驱动的钩子时使用。覆盖 hooks.json 配置、事件类型和脚本集成。先完成脚本开发。
context: fork
agent: hook
---

# 插件钩子开发指南

## 前置条件

在开发插件钩子前，请先完成：
- [插件脚本开发](plugin-script-development/SKILL.md)

## hooks.json 格式

```
hooks/
└── hooks.json              # 钩子配置
```

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "ToolPattern",
        "hooks": [
          {
            "type": "command",
            "command": "PLUGIN_NAME=myplugin uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py hooks"
          }
        ]
      }
    ]
  }
}
```

## 事件类型

| 事件 | 触发时机 |
|------|----------|
| `SessionStart` | 会话开始时 |
| `SessionEnd` | 会话结束时 |
| `PreToolUse` | 工具使用前 |
| `PostToolUse` | 工具使用后 |

## 脚本集成

### Python 钩子脚本

```python
# scripts/hooks.py
import json
import sys

from lib import logging
from lib.hooks import load_hooks

def handle_hook() -> None:
    """处理钩子模式：从 stdin 读取 JSON 并记录。"""
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

### main.py 集成

```python
# scripts/main.py
@click.group()
def main(): pass

@main.command()
def hooks():
    """MCP server mode"""
    from scripts.hooks import handle_hook
    handle_hook()
```

## 相关技能

- [plugin-script-development](plugin-script-development/SKILL.md) - 插件脚本开发
- [hooks](../../hooks/SKILL.md) - 钩子系统
