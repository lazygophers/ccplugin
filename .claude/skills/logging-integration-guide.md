---
name: logging-integration-guide
description: ccplugin 项目的日志集成指南 - 为所有插件脚本添加统一的日志系统，支持按小时分片、日志轮转和多渠道输出
---

# 日志集成指南

本指南说明如何为 ccplugin 项目的插件脚本集成统一的日志系统。

## 快速开始

### 方式1：使用便利函数（推荐）

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

# 使用便利函数自动设置 sys.path 和日志
from lib.logging import setup_sys_path, setup_logger

# 设置系统路径（必须在导入其他模块之前）
setup_sys_path(__file__)

# 初始化日志管理器
logger = setup_logger("my-plugin")

def main():
    logger.info("脚本启动")
    try:
        # 你的代码
        logger.info("操作完成")
    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### 方式2：手动设置（用于复杂场景）

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

# 手动设置系统路径
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent.parent
if not (project_root / "lib").exists():
    # 向上查找直到找到 lib 目录
    current = script_dir
    for _ in range(5):
        if (current / "lib").exists():
            project_root = current
            break
        current = current.parent

sys.path.insert(0, str(project_root))

# 导入并初始化日志
from lib.logging import get_logger

logger = get_logger("my-plugin")

def main():
    logger.info("脚本启动")
    # ...

if __name__ == "__main__":
    main()
```

## 日志系统特性

### 日志文件位置

所有日志都写入到统一的目录：`~/.lazygophers/ccplugin/log/`

日志文件格式：`YYYYMMDDHH.log`（按小时分片）
- 例如：`2026010212.log`（2026-01-02 12点）

### 软连接

自动创建和维护软连接 `log.log` 指向最新的日志文件，方便快速访问：

```bash
# 查看最新日志
tail -f ~/.lazygophers/ccplugin/log/log.log
```

### 日志保留策略

- 最多保留3小时的日志
- 超过3小时的日志自动删除
- 新的小时边界时自动清理

### 输出规则

**文件输出**（`~/.lazygophers/ccplugin/log/`）：
- INFO 级别及以上（INFO, WARNING, ERROR）
- 不输出 DEBUG 日志

**控制台输出**（仅当 enable_console=True）：
- INFO 级别及以上（INFO, WARNING, ERROR）
- 不输出 DEBUG 日志

**MCP 相关脚本**：
- 仅输出到文件（enable_console=False）

### 日志格式

统一格式：`[YYYY-MM-DD HH:MM:SS.mmm] [LEVEL] [plugin-name] message`

示例：
```
[2026-01-02 12:34:56.123] [INFO] [version] 版本已更新: 1.0.0 → 1.0.1
[2026-01-02 12:34:57.456] [ERROR] [version] 无法写入版本文件: /path/.version - Permission denied
```

## 日志记录规范

### DEBUG 级别

- 仅用于开发调试
- 仅输出到控制台（不写入文件）
- 用于追踪执行流程

```python
logger.debug(f"读取配置文件: {config_file}")
logger.debug(f"解析参数: {parsed_args}")
```

### INFO 级别

- 记录关键操作和结果
- 同时输出到文件和控制台
- 用于追踪脚本执行过程

```python
logger.info("脚本启动")
logger.info(f"版本已更新: {old_version} → {new_version}")
logger.info("操作完成")
```

### WARNING 级别

- 记录需要关注的情况
- 同时输出到文件和控制台
- 表示可能的问题但不中断执行

```python
logger.warning(".version 文件未提交到 git")
logger.warning(f"配置文件不存在: {config_file}，使用默认配置")
```

### ERROR 级别

- 记录错误信息
- 同时输出到文件和控制台
- **仅记录错误信息本身，不记录完整 traceback**

```python
logger.error(f"无法读取版本文件: {version_file} - {error_message}")
logger.error("版本格式解析失败: invalid-version")
logger.error(f"hooks 不允许手动设置版本")
```

## 常见使用场景

### 场景1：CLI 脚本

```python
#!/usr/bin/env python3
"""版本管理脚本"""
from lib.logging import setup_sys_path, setup_logger

setup_sys_path(__file__)
logger = setup_logger("version")

def main():
    try:
        logger.info(f"version 脚本启动，参数: {sys.argv[1:]}")
        
        if command == "bump":
            logger.info(f"开始更新版本，级别: {level}")
            # 执行版本更新
            logger.info(f"版本已更新: {old_version} → {new_version}")
            
    except ValueError as e:
        logger.error(f"版本格式错误: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("脚本被用户中断")
        sys.exit(130)
    except Exception as e:
        logger.error(f"脚本执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### 场景2：Hook 脚本

Hook 脚本仅输出到文件（不输出到控制台）：

```python
#!/usr/bin/env python3
"""停止 hook 处理脚本"""
from lib.logging import setup_sys_path, setup_logger

setup_sys_path(__file__)
logger = setup_logger("stop-hook", enable_console=False)

def main():
    try:
        logger.info("Stop hook 启动")
        # 处理 hook
        logger.info("Stop hook 处理完成")
    except Exception as e:
        logger.error(f"Stop hook 处理失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### 场景3：MCP 服务器

MCP 服务器仅输出到文件：

```python
#!/usr/bin/env python3
"""MCP 服务器"""
from lib.logging import setup_sys_path, setup_logger

setup_sys_path(__file__)
logger = setup_logger("semantic-mcp", enable_console=False)

async def main():
    try:
        logger.info("MCP 服务器启动")
        # MCP 服务器代码
    except Exception as e:
        logger.error(f"MCP 服务器错误: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

## API 参考

### LogManager 类

```python
from lib.logging import get_logger

logger = get_logger("plugin-name", enable_console=True)
```

#### 方法

- `logger.debug(message)` - 记录调试信息（仅控制台）
- `logger.info(message)` - 记录信息（文件 + 控制台）
- `logger.warning(message)` - 记录警告（文件 + 控制台）
- `logger.error(message)` - 记录错误（文件 + 控制台）
- `logger.exception(message)` - 记录异常（仅文件）

#### 参数

- `plugin_name` (str) - 插件名称，用于日志标识
- `enable_console` (bool) - 是否输出到控制台（默认 True）

### 便利函数

```python
from lib.logging import setup_sys_path, setup_logger

# 自动设置系统路径
project_root = setup_sys_path(__file__, max_levels=5)

# 快速创建日志管理器
logger = setup_logger("plugin-name", enable_console=True)
```

## 最佳实践

### DO ✅

- 在脚本开头立即初始化日志
- 为主要操作记录 INFO 级别日志
- 为异常情况记录 ERROR 或 WARNING 日志
- 在 try-except 块中使用 logger.error
- 为不同的操作使用不同的日志消息
- 记录关键参数和结果

### DON'T ❌

- 不要使用 print() 代替日志记录
- 不要记录敏感信息（密码、令牌等）
- 不要在文件日志中包含 DEBUG 信息
- 不要忽略异常，至少要记录 logger.error
- 不要在 hook 脚本中输出到控制台
- 不要记录过于详细的 traceback（仅记录错误信息本身）

## 故障排除

### 日志文件没有被创建

检查：
1. 目录权限：`~/.lazygophers/ccplugin/log/` 是否可写
2. sys.path 是否正确设置
3. lib 模块是否存在

### 日志没有输出到控制台

原因可能：
1. 脚本是 hook 或 MCP 服务器，日志仅输出到文件
2. enable_console 被设置为 False
3. 日志级别过高（仅 INFO 和以上会输出）

### 软连接不存在

日志系统在第一次写入时自动创建软连接。如果不存在：
1. 确保脚本已经执行过至少一次
2. 检查 `~/.lazygophers/ccplugin/log/` 目录是否存在
3. 检查是否有权限创建软连接

## 相关文档

- [插件 Skills 编写规范](.claude/skills/plugin-skills-authoring.md)
- [项目 CLAUDE.md](CLAUDE.md)
- [项目 README.md](README.md)
