# 插件钩子

## 插件钩子概述

插件可以通过 `.claude-plugin/plugin.json` 中的 `hooks` 字段定义钩子,使用 `${CLAUDE_PLUGIN_ROOT}` 环境变量引用插件根目录。

## 插件钩子配置

### plugin.json hooks 字段格式

```json
{
  "name": "plugin-name",
  "version": "0.0.1",
  "description": "插件描述",
  "author": {...},
  "homepage": "...",
  "repository": "...",
  "license": "AGPL-3.0-or-later",
  "keywords": [...],
  "commands": [...],
  "agents": [...],
  "skills": "./skills/",
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

### 环境变量

| 变量 | 说明 |
|------|------|
| `${CLAUDE_PLUGIN_ROOT}` | 插件根目录路径 |
| `PLUGIN_NAME` | 插件名称（用于日志识别） |

## 钩子脚本开发

### Python 钩子脚本

插件钩子通常使用 Python 脚本处理：

```python
# scripts/hooks.py
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

### 读取钩子输入

```python
import json
import sys

def handle_hook():
    # 从 stdin 读取 JSON
    hook_data = json.load(sys.stdin)

    event_name = hook_data.get("hook_event_name")
    session_id = hook_data.get("session_id")
    tool_name = hook_data.get("tool_name")
    tool_input = hook_data.get("tool_input", {})

    # 处理不同事件
    if event_name == "SessionStart":
        source = hook_data.get("source")
        # 初始化逻辑
    elif event_name == "PreToolUse":
        # 验证逻辑
        pass
    elif event_name == "PostToolUse":
        # 后处理逻辑
        pass
```

## golang 插件示例

### 目录结构

```
golang/
├── scripts/
│   ├── main.py              # CLI 入口
│   └── hooks.py             # 钩子处理脚本
└── .claude-plugin/
    └── plugin.json          # 包含 hooks 配置
```

### plugin.json (hooks 字段)

```json
{
  "name": "golang",
  "version": "0.0.1",
  "description": "Golang 开发支持",
  "author": {...},
  "homepage": "...",
  "repository": "...",
  "license": "AGPL-3.0-or-later",
  "keywords": ["golang", "go"],
  "commands": [],
  "agents": [],
  "skills": "./skills/",
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

### hooks.py

```python
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

        # 根据事件类型处理
        if event_name == "SessionStart":
            _handle_session_start(hook_data)
        elif event_name == "PreToolUse":
            _handle_pre_tool_use(hook_data)

    except json.JSONDecodeError as e:
        logging.error(f"JSON 解析失败: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Hook 处理失败: {e}")
        sys.exit(1)

def _handle_session_start(data):
    """处理会话开始事件。"""
    source = data.get("source", "unknown")
    logging.info(f"会话开始，来源: {source}")

def _handle_pre_tool_use(data):
    """处理工具使用前事件。"""
    tool_name = data.get("tool_name", "unknown")
    logging.info(f"即将使用工具: {tool_name}")
```

## 插件钩子事件

插件可响应的事件：

| 事件 | 说明 |
|------|------|
| `SessionStart` | 会话开始时 |
| `SessionEnd` | 会话结束时 |
| `PreToolUse` | 工具使用前 |
| `PostToolUse` | 工具使用后 |

## 相关文档

- [事件类型](events.md)
- [配置格式](config.md)
- [钩子输入](input.md)
