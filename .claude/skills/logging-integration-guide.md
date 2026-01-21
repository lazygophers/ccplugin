---
name: logging-integration-guide
description: ccplugin 项目的日志集成指南 - 简洁的 5 函数 API，支持按小时自动分片、自动清理过期日志和单例模式
---

# 日志集成指南

本指南说明如何为 ccplugin 项目的插件脚本集成统一的日志系统。

## 快速开始

### 运行插件脚本

每个插件在自己的目录中运行，具有独立的虚拟环境：

```bash
# 导航到插件目录
cd plugins/version

# 运行脚本
uv run scripts/version.py show
uv run scripts/version.py --help
```

### 标准集成模板

在任何插件脚本中集成日志：

```python
#!/usr/bin/env python3
"""插件脚本示例"""
import sys
from pathlib import Path

# 第1步：设置 sys.path 来找到 lib 目录（可选，作为备份）
script_dir = Path(__file__).resolve().parent
plugin_dir = script_dir.parent
project_root = plugin_dir.parent.parent

lib_path = project_root / "lib"
if not lib_path.exists():
    # 如果找不到，向上查找（用于特殊目录结构）
    current = script_dir
    for _ in range(5):
        if (current / "lib").exists():
            project_root = current
            break
        current = current.parent

sys.path.insert(0, str(project_root))

# 第2步：导入日志函数
# lib 通过 pyproject.toml 中的 path 依赖自动安装在虚拟环境中
from lib.logging import info, debug, error, warn, enable_debug

def main():
    info("脚本启动")
    try:
        # 你的代码
        info("操作完成")
    except Exception as e:
        error(f"执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## 日志系统特性

### 日志文件位置

所有日志都写入到当前工作目录（通常是项目根目录）：`.lazygophers/ccplugin/log/`

日志文件格式：`YYYYMMDDHH.log`（按小时分片）
- 例如：`2026010212.log`（2026年1月2日12点）

### 日志保留策略

- 最多保留 3 个小时的日志文件
- 超过 3 个文件的日志自动删除
- 新的小时边界时自动清理（文件轮转时触发）

### 输出规则

**文件输出**（`.lazygophers/ccplugin/log/`）：
- 所有级别（INFO, DEBUG, WARNING, ERROR）
- 持久化存储

**控制台输出**：
- 仅当调用 `enable_debug()` 时，才输出 DEBUG 和 INFO 级别日志
- WARNING 和 ERROR 级别总是输出到控制台
- Hook 脚本和 MCP 服务器默认不输出到控制台

### 日志格式

统一格式：`[颜色][级别符号] [时间] 消息[/颜色]`

示例（文件中）：
```
ℹ️  INFO [2026-01-02 12:34:56] 版本已更新: 1.0.0 → 1.0.1
🐛 DEBUG [2026-01-02 12:34:57] 读取配置文件成功
⚠️  WARNING [2026-01-02 12:34:58] .version 文件未提交到 git
❌ ERROR [2026-01-02 12:34:59] 无法写入版本文件: Permission denied
```

## API 参考

### 导出函数

本模块只导出 5 个函数，采用全局单例模式：

#### `info(message: str) -> None`

记录信息级别日志，同时写入文件和控制台。

```python
info("脚本启动")
info(f"版本已更新: {old_version} → {new_version}")
```

#### `debug(message: str) -> None`

记录调试级别日志，仅在 DEBUG 模式下输出到控制台，总是写入文件。

```python
debug("读取配置文件成功")
debug(f"解析参数: {parsed_args}")
```

#### `warn(message: str) -> None`

记录警告级别日志，同时写入文件和控制台。

```python
warn(".version 文件未提交到 git")
warn(f"配置文件不存在: {config_file}，使用默认配置")
```

#### `error(message: str) -> None`

记录错误级别日志，同时写入文件和控制台。仅记录错误信息本身，不记录完整 traceback。

```python
error(f"无法读取版本文件: {version_file}")
error("版本格式解析失败: invalid-version")
```

#### `enable_debug() -> None`

启用 DEBUG 模式，使得 DEBUG 和 INFO 级别日志也输出到控制台。通常用于 `--debug` 命令行参数。

```python
if args.debug:
    enable_debug()
debug("DEBUG 模式已启用")
```

## 日志记录规范

### DEBUG 级别

- 仅用于开发调试
- 需要 `enable_debug()` 才能在控制台显示
- 总是写入日志文件
- 用于追踪执行流程

```python
debug(f"读取文件: {file_path}")
debug(f"解析参数完成: {parsed_dict}")
```

### INFO 级别

- 记录关键操作和结果
- 同时输出到文件和控制台
- 用于追踪脚本执行过程

```python
info("脚本启动")
info(f"版本已更新: {old_version} → {new_version}")
info("操作完成")
```

### WARNING 级别

- 记录需要关注的情况
- 同时输出到文件和控制台
- 表示可能的问题但不中断执行

```python
warn(".version 文件未提交到 git")
warn(f"配置文件不存在: {config_file}，使用默认值")
```

### ERROR 级别

- 记录错误信息
- 同时输出到文件和控制台
- **仅记录错误信息本身，不记录完整 traceback**

```python
error(f"无法读取版本文件: {version_file}")
error("版本格式解析失败: invalid-version")
error(f"hooks 不允许手动设置版本")
```

## 常见使用场景

### 场景1：CLI 脚本（带 --debug 参数）

运行方式：
```bash
cd plugins/version
uv run scripts/version.py --help
uv run scripts/version.py --debug
```

脚本代码（支持 --debug 选项）：
```python
#!/usr/bin/env python3
"""版本管理脚本"""
import sys
from pathlib import Path
import typer

# 设置 sys.path（可选，lib 通过 pyproject.toml 安装）
script_dir = Path(__file__).resolve().parent
plugin_dir = script_dir.parent
project_root = plugin_dir.parent.parent
lib_path = project_root / "lib"
if not lib_path.exists():
    current = script_dir
    for _ in range(5):
        if (current / "lib").exists():
            project_root = current
            break
        current = current.parent

sys.path.insert(0, str(project_root))

from lib.logging import enable_debug

def main(debug_mode: bool = typer.Option(False, "--debug", help="启用 DEBUG 模式")) -> None:
    """
    版本管理脚本。

    Args:
        debug_mode: 是否启用 DEBUG 模式
    """
    if debug_mode:
        enable_debug()

if __name__ == "__main__":
    typer.run(main)
```

### 场景2：Hook 脚本（无控制台输出）

运行方式（由 Claude Code 自动调用）：
```bash
# 在 hooks.json 中配置
"stop_hook": "cd plugins/notify && uv run scripts/stop_hook.py"
```

Hook 脚本自动只输出到文件，无需特殊配置：

```python
#!/usr/bin/env python3
"""停止 hook 处理脚本"""
import sys
import json
from pathlib import Path

# 设置 sys.path（可选，lib 通过 pyproject.toml 安装）
script_dir = Path(__file__).resolve().parent
plugin_dir = script_dir.parent
project_root = plugin_dir.parent.parent
lib_path = project_root / "lib"
if not lib_path.exists():
    current = script_dir
    for _ in range(5):
        if (current / "lib").exists():
            project_root = current
            break
        current = current.parent

sys.path.insert(0, str(project_root))

from lib.logging import info, error

def main():
    info("Stop hook 启动")
    try:
        # 从 stdin 读取 JSON
        hook_data = json.load(sys.stdin)

        # 处理 hook
        info("Stop hook 处理完成")
    except Exception as e:
        error(f"Stop hook 处理失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### 场景3：MCP 服务器（无控制台输出）

运行方式（由 Claude Code 自动启动）：
```bash
# MCP 服务器通过项目配置自动启动
# 每个插件的 MCP 服务器在其各自的虚拟环境中运行
```

MCP 服务器自动只输出到文件，无需特殊配置：

```python
#!/usr/bin/env python3
"""MCP 服务器"""
import sys
import asyncio
from pathlib import Path

# 设置 sys.path（可选，lib 通过 pyproject.toml 安装）
script_dir = Path(__file__).resolve().parent
plugin_dir = script_dir.parent
project_root = plugin_dir.parent.parent
lib_path = project_root / "lib"
if not lib_path.exists():
    current = script_dir
    for _ in range(5):
        if (current / "lib").exists():
            project_root = current
            break
        current = current.parent

sys.path.insert(0, str(project_root))

from lib.logging import info, error

async def main():
    info("MCP 服务器启动")
    try:
        # MCP 服务器代码
        info("MCP 服务器运行中...")
    except Exception as e:
        error(f"MCP 服务器错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

## 最佳实践

### DO ✅

- 在脚本开头立即设置 sys.path 和导入日志函数
- 为主要操作记录 INFO 级别日志
- 为异常情况记录 ERROR 或 WARN 日志
- 为 `--debug` 命令行参数调用 `enable_debug()`
- 记录关键参数和结果

### DON'T ❌

- 不要使用 `print()` 代替日志记录
- 不要记录敏感信息（密码、令牌等）
- 不要在错误日志中包含 traceback 细节
- 不要忽略异常，至少要调用 `error()`
- 不要设置日志级别或修改全局配置
- 不要尝试访问 RichLoggerManager 类（这是内部实现）

## 故障排除

### 日志文件没有被创建

检查：
1. 当前工作目录权限：`.lazygophers/ccplugin/log/` 是否可写
2. sys.path 是否正确设置（脚本是否能正确导入 lib）
3. 脚本是否至少调用过一次日志函数

### 日志没有输出到控制台

可能的原因：
1. 脚本是 hook 或 MCP 服务器，日志仅输出到文件
2. 没有调用 `enable_debug()`，所以 DEBUG 日志不显示
3. 只有 INFO、WARNING、ERROR 级别才会输出到控制台

**解决方案**：
- 对于 CLI 脚本：添加 `--debug` 参数并调用 `enable_debug()`
- 对于 Hook/MCP：日志只输出到文件，检查 `.lazygophers/ccplugin/log/` 目录

### ModuleNotFoundError: No module named 'lib'

原因：sys.path 设置不正确

**检查**：
1. 验证项目根目录存在 `lib/` 子目录
2. 检查 sys.path 设置是否正确计算了项目根目录
3. 对于特殊目录结构，增加向上搜索的范围（默认 5 级）

## 相关文档

- [lib/logging README](lib/logging/README.md) - API 详细文档
- [项目 CLAUDE.md](CLAUDE.md) - 项目整体文档
- [插件开发指南](plugins/code/README.md) - 插件开发最佳实践
