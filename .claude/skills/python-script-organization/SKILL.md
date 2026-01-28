---
name: python-script-organization
description: Python 插件脚本组织规范 - 定义 CCPlugin 生态中 Python 脚本的标准组织结构、命名约定和最佳实践
---

# Python 脚本组织规范

## 快速导航

| 章节 | 内容 | 适用场景 |
|------|------|---------|
| **核心理念** | 强制规范、优先使用、目录结构 | 快速入门 |
| **目录结构** | 标准插件结构、Scripts 目录 | 创建新插件 |
| **命名约定** | 文件/代码/插件命名规范 | 日常编码 |
| **导入模式** | 标准导入顺序、共享库使用 | 模块导入 |
| **代码模式** | CLI/Hook/MCP 标准模式 | 功能实现 |
| **配置规范** | pyproject.toml、.mcp.json 等 | 项目配置 |
| **快速模板** | 最小/完整插件模板 | 快速开始 |

## 核心理念

CCPlugin Python 生态追求**标准化、可复用、可维护**，通过统一的代码组织结构和共享库，帮助开发者写出高质量的插件代码。

**三个支柱：**

1. **标准化** - 统一的目录结构、命名约定、代码模式
2. **可复用** - 通过共享库（lib）提供通用功能
3. **可维护** - 清晰的职责分离、完善的文档、标准的配置

## 版本与环境

- **Python 版本**：>= 3.12（强制）
- **包管理器**：uv（强制，不使用 pip）
- **CLI 框架**：Click（推荐）
- **共享库**：lib（强制依赖）

## 强制规范

- ✅ **必须使用 `uv run`** 执行 Python 脚本
- ✅ **必须使用共享库** `lib/logging`, `lib/hooks`
- ✅ **必须遵循 PEP 8** 命名约定
- ✅ **必须使用 Click** 框架构建 CLI
- ✅ **必须使用 `with_debug`** 装饰器添加 --debug 支持

## 目录结构

### 标准插件结构

```
plugin-name/
├── scripts/                    # Python 代码目录（必需）
│   ├── __init__.py            # 包初始化文件（必需，可为空）
│   ├── main.py                # CLI 入口（必需）
│   ├── <module>.py            # 业务逻辑模块
│   ├── hooks.py               # Hook 处理器（如需 hook 支持）
│   └── mcp.py                 # MCP 服务器（如需 MCP 支持）
│
├── commands/                   # Claude Code 命令定义（可选）
│   └── *.md                   # 命令文档
│
├── agents/                     # 子代理定义（可选）
│   └── *.md
│
├── skills/                     # 技能规范（可选）
│   └── **/
│
├── hooks/                      # Hook 配置（可选）
│   └── hooks.json
│
├── __init__.py                 # 插件根包（可选）
├── pyproject.toml             # 项目配置（必需）
├── .claude-plugin/plugin.json # 插件元数据（必需）
├── .mcp.json                  # MCP 配置（可选）
└── README.md                  # 插件文档（推荐）
```

### Scripts 目录详解

| 文件 | 职责 | 是否必需 |
|------|------|----------|
| `__init__.py` | 标识为 Python 包 | 是 |
| `main.py` | CLI 入口点，命令路由 | 是 |
| `<module>.py` | 核心业务逻辑模块 | 按需 |
| `hooks.py` | Hook 事件处理器 | 按需 |
| `mcp.py` | MCP 服务器实现 | 按需 |

**设计原则：**
- **单一职责**：每个文件只负责一个核心功能
- **入口分离**：CLI 命令定义与业务逻辑分离
- **最小化实现**：仅实现必要功能，避免过度设计

## 命名约定

### 文件命名

```bash
# Python 模块文件
lowercase_with_underscores.py    # ✅ 正确
camelCase.py                     # ❌ 错误
UPPERCASE.py                     # ❌ 错误

# 示例
main.py                          # CLI 入口
hooks.py                         # Hook 处理
version.py                       # 版本管理
mcp.py                           # MCP 服务器
```

### 代码命名

**函数命名：** `lowercase_with_underscores`
```python
# ✅ 正确
def handle_hook() -> None:
    """处理 hook 事件"""
    pass

def get_version() -> str:
    """获取版本号"""
    pass

def inc_major() -> None:
    """递增主版本号"""
    pass

# ❌ 错误
def HandleHook():                # 大写开头
def get_version():               # 混合风格
def incMajor():                  # 驼峰命名
```

**类命名：** `CapWords`（大驼峰）
```python
# ✅ 正确
class VersionMCPServer:
    """版本管理 MCP 服务器"""
    pass

class RichLoggerManager:
    """Rich 日志管理器"""
    pass

# ❌ 错误
class version_mcp_server:        # 下划线
class VersionMCP_Server:         # 混合风格
```

**常量命名：** `UPPERCASE_WITH_UNDERSCORES`
```python
# ✅ 正确
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
VERSION_FILEPATH = ".version"

# ❌ 错误
max_retries = 3                  # 小写
DefaultTimeout = 30              # 驼峰
```

**变量命名：** `lowercase_with_underscores`
```python
# ✅ 正确
version = "1.0.0"
request_id = 123
hook_event_name = "SessionStart"

# ❌ 错误
v = "1.0.0"                      # 过于简短
```

### 插件命名

**插件包名：** `{category}-{name}` 或 `code-{language}`
```
version/                         # 版本管理插件
task/                            # 任务管理插件
code-python/                     # Python 开发插件
code-golang/                     # Golang 开发插件
```

**技能目录名：** 与功能同名
```
skills/python/                   # Python 技能
skills/golang/                   # Golang 技能
skills/versioning/               # 版本管理技能
```

## 导入模式

### 标准导入顺序

```python
# 1. 标准库导入
import os
import sys
import json
import asyncio
from pathlib import Path
from functools import wraps

# 2. 第三方库导入
import click
import typer
from rich.console import Console

# 3. 共享库导入（来自 lib/）
from lib import logging
from lib.hooks import load_hooks
from lib.utils.env import get_project_dir

# 4. 本地模块导入（同目录）
from hooks import handle_hook
from version import get_version, init_version
from mcp import VersionMCPServer
```

### 共享库使用（强制）

**优先使用共享库，禁止重复实现：**

```python
# ✅ 正确：使用共享日志
from lib import logging
logging.info("消息")
logging.error("错误")

# ❌ 错误：直接使用标准库 logging
import logging
logging.info("消息")

# ✅ 正确：使用共享 Hook 工具
from lib.hooks import load_hooks
hook_data = load_hooks()

# ❌ 错误：自己实现 JSON 读取
import json
hook_data = json.load(sys.stdin)
```

**共享库可用模块：**
```python
from lib import logging              # 日志系统
from lib.hooks import load_hooks     # Hook 加载器
from lib.utils.env import get_project_dir      # 项目目录
from lib.utils.env import get_plugins_path     # 插件目录
```

### 导入规范

```python
# ✅ 正确：显式导入
from lib import logging

# ❌ 避免：通配符导入
from lib import *

# ✅ 正确：每个导入单独一行
import os
import sys

# ❌ 避免：一行多导入
import os, sys

# ✅ 正确：绝对导入
from lib import logging
from hooks import handle_hook

# ⚠️ 谨慎：相对导入（仅用于包内部）
from . import version
from .hooks import handle_hook
```

## 代码结构模式

### CLI 入口模式（main.py）

**标准结构：**

```python
"""
插件 CLI 入口
"""
from lib import logging
import click
from functools import wraps

# 导入本地模块
from hooks import handle_hook
from mcp import VersionMCPServer


def with_debug(func):
    """装饰器：为所有命令添加 --debug 参数支持"""
    @wraps(func)
    @click.option("--debug", "debug_mode", is_flag=True, help="启用 DEBUG 模式")
    def wrapper(debug_mode: bool, *args, **kwargs):
        if debug_mode:
            logging.enable_debug()
        return func(*args, **kwargs)
    return wrapper


@click.group()
@click.pass_context
def main(ctx) -> None:
    """插件描述"""
    pass


@main.command()
@with_debug
def info() -> None:
    """显示信息命令"""
    click.echo("Info")


@main.command()
@with_debug
def hooks_cmd() -> None:
    """Hook 模式：从 stdin 读取 JSON"""
    handle_hook()


@main.command()
def mcp() -> None:
    """MCP 服务器模式：启动 MCP 服务器"""
    import asyncio
    server = VersionMCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
```

**模式要点：**
- 使用 Click 框架构建 CLI
- `@click.group()` 定义命令组
- `@with_debug` 装饰器统一添加 debug 支持
- 命令命名使用小写+下划线（`hooks_cmd` 避免 `hooks` 关键字冲突）

### 业务逻辑模块模式

**纯函数设计：**

```python
"""
核心业务逻辑模块
"""
import os
from lib import logging
from lib.utils.env import get_project_dir

# 模块级常量
VERSION_FILEPATH = ".version"


def get_version() -> str:
    """获取当前版本号

    Returns:
        当前版本号字符串
    """
    try:
        with open(os.path.join(get_project_dir(), VERSION_FILEPATH), 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "0.0.1.0"


def init_version() -> None:
    """初始化版本文件"""
    if os.path.exists(os.path.join(get_project_dir(), VERSION_FILEPATH)):
        return

    logging.info("初始化版本文件")

    with open(os.path.join(get_project_dir(), VERSION_FILEPATH), "w") as f:
        f.write('0.0.1.0')


def inc_major() -> None:
    """递增主版本号，其余级别重置为 0"""
    with open(os.path.join(get_project_dir(), VERSION_FILEPATH), 'r') as f:
        version = f.read().strip()

    parts = version.split('.')
    parts[0] = str(int(parts[0]) + 1)
    parts[1] = '0'
    parts[2] = '0'
    parts[3] = '0'
    new_version = '.'.join(parts)

    logging.info(f"更新主版本号为 {new_version}")

    with open(os.path.join(get_project_dir(), VERSION_FILEPATH), 'w') as f:
        f.write(new_version)
```

**模式要点：**
- 无状态，纯函数设计
- 单一职责，每个函数只做一件事
- 使用模块级常量配置
- 统一的文件操作模式（读 → 解析 → 修改 → 写回）

### Hook 处理器模式（hooks.py）

**标准实现：**

```python
"""
Hook 事件处理器
"""
import sys
from lib import logging
from lib.hooks import load_hooks


def handle_hook() -> None:
    """处理 hook 模式：从 stdin 读取 JSON 并路由"""
    try:
        # 1. 加载 Hook 数据
        hook_data = load_hooks()
        event_name = hook_data.get("hook_event_name")

        # 2. 事件路由
        if event_name == "SessionStart":
            logging.info(f"接收到事件: {event_name}")
            # 执行初始化逻辑
        elif event_name == "UserPromptSubmit":
            logging.info(f"接收到事件: {event_name}")
            # 执行提交前逻辑
        else:
            logging.warn(f"未知事件: {event_name}")

        # 3. 返回响应
        print('{"continue": true}')

    except Exception as e:
        logging.error(f"Hook 处理失败: {e}")
        sys.exit(1)
```

**模式要点：**
- 使用 `lib.hooks.load_hooks()` 读取 stdin
- 基于事件名称路由
- 统一的异常处理
- 返回 JSON 控制流程

### MCP 服务器模式（mcp.py）

**异步服务器实现：**

```python
"""
MCP 服务器实现
"""
import asyncio
import json
import sys

from lib import logging
from version import get_version, init_version, inc_major, inc_minor, inc_patch


class VersionMCPServer:
    """版本管理 MCP 服务器"""

    def __init__(self):
        self.tools = self._register_tools()

    def _register_tools(self):
        """注册所有可用的工具"""
        return {
            "get_version": {
                "name": "get_version",
                "description": "获取当前版本号",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            # ... 更多工具
        }

    async def handle_request(self, request: dict) -> dict:
        """处理 MCP 请求"""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        try:
            if method == "tools/list":
                return await self._tools_list()
            elif method == "tools/call":
                return await self._tools_call(params, request_id)
            elif method == "initialize":
                return await self._initialize(params)
            else:
                logging.warn(f"Unknown method: {method}")
                return {
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    },
                    "id": request_id
                }
        except Exception as e:
            logging.error(f"Request handling error: {e}")
            return {
                "error": {
                    "code": -32603,
                    "message": str(e)
                },
                "id": request_id
            }

    async def run(self):
        """启动 MCP 服务器（stdio 模式）"""
        logging.info("MCP server starting")

        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                if not line:
                    break

                line = line.strip()
                if not line:
                    continue

                try:
                    request = json.loads(line)
                    response = await self.handle_request(request)

                    if "id" in request and "id" not in response:
                        response["id"] = request["id"]
                    if "jsonrpc" not in response:
                        response["jsonrpc"] = "2.0"

                    await self._write_response(response)

                except json.JSONDecodeError as e:
                    logging.error(f"JSON decode error: {e}")

            except Exception as e:
                logging.error(f"Server loop error: {e}")

    async def _write_response(self, response: dict):
        """写入响应到 stdout"""
        try:
            json_str = json.dumps(response, ensure_ascii=False)
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: print(json_str, flush=True)
            )
        except Exception as e:
            logging.error(f"Failed to write response: {e}")
```

**模式要点：**
- 异步设计（`async/await`）
- JSON-RPC 2.0 协议
- stdio 通信
- 完整的异常处理和日志

## 配置文件规范

### pyproject.toml

```toml
[project]
name = "plugin-name"              # 插件名称
version = "0.0.91"                # 语义化版本
requires-python = ">=3.12"        # 最低 Python 版本
dependencies = [
    "click>=8.3.1",               # 依赖项
    "lib",                        # 共享库（必需）
]

[tool.uv.sources.lib]
git = "https://github.com/lazygophers/ccplugin"
subdirectory = "lib"              # 引用 monorepo 中的 lib
rev = "master"

[project.scripts]
# CLI 命令别名（可选）
version = "main:main"
```

### .mcp.json

```json
{
  "mcpServers": {
    "server-name": {
      "command": "uv",
      "args": [
        "run",
        "${CLAUDE_PLUGIN_ROOT}/scripts/main.py",
        "mcp"
      ],
      "env": {
        "PLUGIN_NAME": "plugin-name"
      }
    }
  }
}
```

### hooks/hooks.json

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "PLUGIN_NAME=plugin-name uv run --directory ${CLAUDE_PLUGIN_ROOT} ./scripts/main.py hooks"
          }
        ]
      }
    ]
  }
}
```

### .claude-plugin/plugin.json

```json
{
  "name": "plugin-name",
  "version": "0.0.91",
  "description": "插件描述",
  "commands": ["./commands/*.md"],
  "agents": ["./agents/*.md"],
  "skills": "./skills/",
  "mcpServers": "./.mcp.json"
}
```

## 最佳实践

### 代码组织

| 原则 | 说明 |
|------|------|
| **单一职责** | 一个文件一个职责，一个函数一个功能 |
| **依赖倒置** | 依赖抽象（共享库），不依赖具体实现 |
| **DRY** | 复用共享库，避免重复实现 |
| **配置分离** | 配置与代码分离 |

### 错误处理

```python
# ✅ 正确：捕获具体异常
try:
    hook_data = load_hooks()
except json.JSONDecodeError as e:
    logging.error(f"JSON 解析失败: {e}")
    sys.exit(1)
except Exception as e:
    logging.error(f"处理失败: {e}")
    sys.exit(1)

# ❌ 避免：裸 except
try:
    hook_data = load_hooks()
except:
    pass
```

### 日志规范

```python
# ✅ 正确：使用共享日志
from lib import logging

logging.info("信息消息")
logging.warn("警告消息")
logging.error("错误消息")
logging.enable_debug()  # 启用调试模式

# ❌ 避免：直接使用标准库
import logging
logging.info("消息")
```

### 执行规范

```bash
# ✅ 正确：使用 uv run
uv run scripts/main.py info
uv run scripts/main.py hooks
uv run scripts/main.py mcp

# ❌ 错误：直接使用 python
python3 scripts/main.py info
python scripts/main.py info
./scripts/main.py info
```

## 快速模板

### 最小插件模板

**main.py:**
```python
from lib import logging
import click


@click.group()
def main():
    """插件描述"""
    pass


@main.command()
def info():
    """显示信息"""
    click.echo("Plugin info")


if __name__ == "__main__":
    main()
```

**pyproject.toml:**
```toml
[project]
name = "my-plugin"
version = "0.0.1"
requires-python = ">=3.12"
dependencies = ["click>=8.3.1", "lib"]

[tool.uv.sources.lib]
git = "https://github.com/lazygophers/ccplugin"
subdirectory = "lib"
rev = "master"
```

### 完整插件模板

包含 CLI、Hook、MCP 支持的完整结构，参考 `plugins/version/`。

## 参考资源

- **示例插件**: `plugins/version/`, `plugins/code/golang/`, `plugins/code/python/`
- **共享库**: `lib/logging/`, `lib/hooks/`, `lib/utils/`
- **Click 文档**: https://click.palletsprojects.com/
- **PEP 8**: https://peps.python.org/pep-0008/
