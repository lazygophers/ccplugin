---
name: plugin-script-development
description: 插件脚本开发指南 - 当用户需要为插件开发 Python 脚本时使用。覆盖脚本目录结构、CLI 入口实现、Click 命令和脚本模块化。
context: fork
agent: script
---

# 插件脚本开发指南

## 脚本目录结构

```
scripts/
├── __init__.py
├── main.py                  # CLI 入口（必需）
├── hooks.py                 # 钩子处理（可选）
├── mcp.py                   # MCP 服务器（可选）
└── <module>.py              # 业务逻辑模块
```

## CLI 入口实现

### main.py 模板

```python
#!/usr/bin/env python3
"""插件 CLI 入口。"""

import click
from lib import logging


@click.group()
def main():
    """插件命令组。"""
    pass


@main.command()
def my_command():
    """我的命令说明。"""
    click.echo("执行我的命令")


@main.command()
def hooks():
    """钩子处理模式。"""
    from scripts.hooks import handle_hook
    handle_hook()


if __name__ == "__main__":
    main()
```

## Click 命令装饰器

| 装饰器 | 说明 |
|--------|------|
| `@click.group()` | 创建命令组 |
| `@click.command()` | 定义单个命令 |
| `@click.argument()` | 添加位置参数 |
| `@click.option()` | 添加选项参数 |

### 示例

```python
@main.command()
@click.argument("name")
@click.option("--verbose", "-v", is_flag=True, help="详细输出")
def greet(name, verbose):
    """问候用户。"""
    if verbose:
        logging.info(f"收到问候请求: {name}")
    click.echo(f"Hello, {name}!")
```

## 共享库使用

### 日志模块

```python
from lib import logging

logging.info("信息日志")
logging.error("错误日志")
logging.debug("调试日志")
```

### 钩子系统

```python
from lib.hooks import load_hooks

hook_data = load_hooks()
```

## 插件中注册脚本

脚本通过命令和钩子调用，无需在 plugin.json 中单独注册：

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py hooks"
          }
        ]
      }
    ]
  }
}
```

## 相关技能

- [plugin-development](plugin-development/SKILL.md) - 插件开发
- [plugin-hook-development](plugin-hook-development/SKILL.md) - 插件钩子开发
- [plugin-mcp-development](plugin-mcp-development/SKILL.md) - 插件 MCP 开发
