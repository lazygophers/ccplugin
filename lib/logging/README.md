# lib/logging - 日志管理模块

统一的日志管理模块，提供按小时自动分割、自动清理过期日志的功能。

## 特性

- ✅ **按小时自动分割**：日志文件按 `YYYYMMDDHH.log` 格式自动分割
- ✅ **自动清理过期日志**：自动删除超过 3 小时的旧日志文件
- ✅ **全局日志配置**：支持一次性配置所有日志记录器
- ✅ **DEBUG 模式**：支持 DEBUG 级别和控制台输出
- ✅ **简洁的 API**：易用的函数式接口

## 文件结构

```
lib/logging/
├── __init__.py          # 模块公共 API 导出
├── handler.py           # 按小时分割的文件处理器
├── setup_utils.py       # 日志设置工具和配置函数
└── README.md           # 本文件
```

## 基本使用

### 1. 简单日志记录

```python
from lib.logging import get_logger

# 获取日志记录器
logger = get_logger(__name__)

# 记录不同级别的日志
logger.debug("调试信息")      # 不显示（默认 INFO 级别）
logger.info("普通信息")       # 输出到文件
logger.warning("警告信息")    # 输出到文件
logger.error("错误信息")      # 输出到文件
```

### 2. DEBUG 模式

在 DEBUG 模式下，日志同时输出到**文件和控制台**，并显示 DEBUG 级别的日志：

```python
from lib.logging import get_logger

# 启用 DEBUG 模式
logger = get_logger(__name__, debug=True)

logger.debug("调试信息")    # 输出到控制台和文件
logger.info("普通信息")    # 输出到控制台和文件
```

### 3. 全局配置

配置所有日志记录器的输出方式：

```python
from lib.logging import setup_logging, get_logger
import logging

# 配置所有 logger：级别设为 DEBUG，启用控制台输出
setup_logging(
    log_dir="./my_logs",
    level=logging.DEBUG,
    enable_console=True
)

# 现有的 logger 会被更新
logger = get_logger("my_module")
logger.debug("现在会输出到控制台和文件")
```

### 4. 设置全局日志级别

```python
from lib.logging import get_logger, set_level
import logging

logger = get_logger("my_module")

# 后续设置全局级别，影响所有 logger
set_level(logging.DEBUG)
logger.debug("现在会显示")
```

## 日志格式

日志文件格式为：

```
2026-01-21 14:30:00 - INFO - module.py:42 - 消息内容
2026-01-21 14:30:01 - WARNING - handler.py:15 - 警告消息
2026-01-21 14:30:02 - ERROR - script.py:99 - 错误消息
```

字段说明：
- **时间**：`YYYY-MM-DD HH:MM:SS` 格式
- **级别**：`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **文件**：`filename.py:lineno` - 记录日志的文件和行号
- **消息**：日志消息内容

## 日志文件存储

日志文件默认存储在：

```
./lazygophers/ccplugin/log/
├── 2026012113.log   # 2026-01-21 13:00-13:59
├── 2026012114.log   # 2026-01-21 14:00-14:59
├── 2026012115.log   # 2026-01-21 15:00-15:59
└── ...
```

**特点**：
- 文件名格式：`YYYYMMDDHH.log`（年月日小时）
- 最多保留 3 个日志文件
- 自动删除超过 3 小时的旧日志

## API 参考

### `get_logger(name, debug=False)`

获取配置好的日志记录器。

**参数：**
- `name` (str)：日志记录器名称，通常使用 `__name__`
- `debug` (bool)：是否启用 DEBUG 模式，默认 False
  - `False`：仅写入文件，级别为 INFO
  - `True`：同时输出到控制台和文件，级别为 DEBUG

**返回值：**
- `logging.Logger`：配置好的日志记录器实例

**示例：**
```python
# 普通模式
logger = get_logger(__name__)

# DEBUG 模式
logger = get_logger(__name__, debug=True)
```

### `setup_logging(log_dir=None, level=logging.INFO, enable_console=False)`

全局配置日志系统。

**参数：**
- `log_dir` (str)：日志目录，默认为 `./lazygophers/ccplugin/log`
- `level` (int)：日志级别，默认 `logging.INFO`
- `enable_console` (bool)：是否输出到控制台，默认 False

**示例：**
```python
import logging
from lib.logging import setup_logging

# 配置所有 logger 为 DEBUG 级别并输出到控制台
setup_logging(
    log_dir="./logs",
    level=logging.DEBUG,
    enable_console=True
)
```

### `set_level(level)`

设置所有日志记录器的级别。

**参数：**
- `level` (int)：日志级别（`logging.DEBUG`, `logging.INFO`, 等）

**示例：**
```python
from lib.logging import set_level
import logging

set_level(logging.DEBUG)  # 所有 logger 显示 DEBUG 信息
```

### `HourlyRotatingFileHandler`

按小时分割的文件处理器（通常不需要直接使用）。

**特性：**
- 自动按小时创建新的日志文件
- 自动删除超过 3 小时的旧文件
- 与标准 `logging.FileHandler` 兼容

## 常见场景

### 场景 1：在插件脚本中集成日志

```python
#!/usr/bin/env python3
import sys
from pathlib import Path
from lib.logging import get_logger

# 获取日志记录器
logger = get_logger(__name__)

def main():
    logger.info("脚本启动")
    try:
        # 你的代码
        logger.info("操作完成")
    except Exception as e:
        logger.error(f"发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### 场景 2：Hook 脚本中的日志（仅写文件）

```python
#!/usr/bin/env python3
import sys
from pathlib import Path
from lib.logging import get_logger

# Hook 脚本通常只写日志文件，不输出到控制台
logger = get_logger("stop_hook")

def main():
    logger.info("Stop hook triggered")
    # ...

if __name__ == "__main__":
    main()
```

### 场景 3：需要 DEBUG 信息的脚本

```python
#!/usr/bin/env python3
import sys
from lib.logging import get_logger

def main(debug_mode=False):
    # 根据参数启用 DEBUG
    logger = get_logger(__name__, debug=debug_mode)

    logger.debug("调试信息，仅在 debug 模式显示")
    logger.info("普通信息，始终显示")

if __name__ == "__main__":
    # 检查 --debug 标记
    debug = "--debug" in sys.argv
    main(debug)
```

## 测试

运行单元测试：

```bash
uv run -m pytest lib/tests/test_logging.py -v
```

测试覆盖内容：
- ✅ 日志处理器创建和文件生成
- ✅ 日志格式验证
- ✅ 日志文件自动轮转
- ✅ 旧日志文件自动清理（保留最新 3 个）
- ✅ API 缓存和全局配置
- ✅ 日志级别控制

## 常见问题

**Q: 日志文件保存在哪里？**

A: 默认保存在项目目录的 `./lazygophers/ccplugin/log/` 目录下。可以通过 `setup_logging(log_dir="...")` 自定义。

**Q: 如何查看日志？**

A: 日志文件按小时命名（如 `2026012114.log`），可以直接用文本编辑器或命令行查看：
```bash
cat lazygophers/ccplugin/log/2026012114.log
```

**Q: 如何启用 DEBUG 日志和控制台输出？**

A: 使用 `debug=True` 参数或 `setup_logging(enable_console=True, level=logging.DEBUG)`。

**Q: 日志会占用很多磁盘空间吗？**

A: 不会。系统最多保留 3 个日志文件，旧文件会自动删除。

## 集成检查清单

- [ ] 在插件脚本中导入：`from lib.logging import get_logger`
- [ ] 创建 logger：`logger = get_logger(__name__)`
- [ ] 记录关键操作：`logger.info("operation...")`
- [ ] 记录错误：`logger.error("error message")`
- [ ] Hook 脚本使用 `debug=False`（仅文件）
- [ ] 普通脚本可选 `debug` 参数
- [ ] 运行测试验证：`pytest lib/tests/test_logging.py`
