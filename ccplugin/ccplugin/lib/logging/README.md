# lib/logging - 基于 Rich 的日志系统

简洁、强大的日志管理模块，使用 Rich 库提供彩色输出和格式化，自动按小时分割日志文件。

## 特性

- ✅ **基于 Rich** - 彩色输出和优雅的格式化
- ✅ **按小时自动分割** - 日志文件自动按 `YYYYMMDDHH.log` 分割
- ✅ **自动清理过期日志** - 保留最新 3 个文件，自动删除过期文件
- ✅ **单实例设计** - 全局统一的日志管理器
- ✅ **简洁的 API** - 只有 5 个函数：`info()`, `debug()`, `error()`, `warn()`, `enable_debug()`
- ✅ **DEBUG 模式** - 启用后同时输出到文件和控制台，显示 DEBUG 级别日志

## 快速开始

### 基础使用

```python
from lib.logging import info, error, warn

# 记录不同级别的日志
info("应用启动成功")
warn("检测到潜在问题")
error("发生了一个错误")

# 所有日志自动保存到 ./lazygophers/ccplugin/log/YYYYMMDDHH.log
```

### DEBUG 模式

```python
from lib.logging import enable_debug, debug, info

# 启用 DEBUG 模式
enable_debug()

# 现在调试信息会同时输出到文件和控制台
debug("这是调试信息")
info("普通信息")
```

## API 参考

### `info(message: str)`

记录 INFO 级别日志。

```python
from lib.logging import info
info("操作完成")
```

### `debug(message: str)`

记录 DEBUG 级别日志。

仅在启用 DEBUG 模式时输出到控制台（始终写入文件）。

```python
from lib.logging import debug
debug("调试信息")
```

### `error(message: str)`

记录 ERROR 级别日志。

```python
from lib.logging import error
error("发生错误: 无法连接到服务器")
```

### `warn(message: str)`

记录 WARNING 级别日志。

```python
from lib.logging import warn
warn("内存使用率较高")
```

### `enable_debug()`

启用 DEBUG 模式。

在 DEBUG 模式下：
- 日志同时输出到**文件和控制台**
- 显示 **DEBUG** 级别的日志信息
- 使用彩色输出增强可读性

```python
from lib.logging import enable_debug
enable_debug()
```

## 日志格式

日志文件中的格式：

```
ℹ️  INFO [2026-01-21 14:30:00] 应用启动
⚠️  WARNING [2026-01-21 14:30:01] 这是一条警告
❌ ERROR [2026-01-21 14:30:02] 发生错误
🐛 DEBUG [2026-01-21 14:30:03] 调试信息
```

- **图标** - 日志级别的视觉标识
- **级别** - INFO, DEBUG, ERROR, WARNING
- **时间戳** - `[YYYY-MM-DD HH:MM:SS]` 格式
- **消息** - 日志内容

## 日志文件存储

日志默认保存在：

```
./lazygophers/ccplugin/log/
├── 2026012113.log   (2026-01-21 13:00-13:59)
├── 2026012114.log   (2026-01-21 14:00-14:59)
└── 2026012115.log   (2026-01-21 15:00-15:59)
```

**特点：**
- 文件命名：`YYYYMMDDHH.log`（年月日小时）
- 最多保留 **3 个**日志文件
- 旧文件**自动删除**

## 常见使用场景

### 场景 1: 脚本中的基础日志

```python
#!/usr/bin/env python3
from lib.logging import info, error

def main():
    info("脚本启动")
    try:
        # 执行操作
        info("操作完成")
    except Exception as e:
        error(f"发生错误: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
```

### 场景 2: 启用 DEBUG 模式进行调试

```python
#!/usr/bin/env python3
import sys
from lib.logging import info, debug, enable_debug

def main(debug_mode=False):
    if debug_mode:
        enable_debug()

    debug("这是调试信息")
    info("开始处理")

    # ...

if __name__ == "__main__":
    debug_mode = "--debug" in sys.argv
    main(debug_mode)
```

### 场景 3: Hook 脚本中的日志

```python
#!/usr/bin/env python3
from lib.logging import info, error

def process_hook():
    info("Hook 被触发")
    try:
        # 处理 Hook 事件
        info("处理完成")
    except Exception as e:
        error(f"Hook 处理失败: {e}")
        return 1
    return 0
```

## 日志查看

查看最新的日志：

```bash
# 查看最新日志文件
tail lazygophers/ccplugin/log/2026012114.log

# 实时跟踪日志
tail -f lazygophers/ccplugin/log/2026012114.log

# 查看所有日志
cat lazygophers/ccplugin/log/*.log
```

## 测试

运行单元测试：

```bash
uv run python3 -m unittest lib.tests.test_logging -v
```

测试覆盖：
- ✅ 所有日志级别函数
- ✅ DEBUG 模式启用
- ✅ 日志文件创建和格式
- ✅ 旧日志文件清理（保留 3 个）
- ✅ 单例模式
- ✅ API 可访问性

## 与 Python logging 的区别

| 特性 | lib.logging | Python logging |
|------|-----------|-----------------|
| 库 | Rich | 标准库 |
| API | 简洁函数式 | 复杂、冗长 |
| 输出格式 | 彩色、表情符号 | 纯文本 |
| 自动分割 | 按小时分割 | 按大小分割 |
| 单例 | 是（全局） | 否（多实例） |
| 行数 | ~200 | ~1000+ |

## 常见问题

**Q: 日志文件保存在哪里？**

A: `./lazygophers/ccplugin/log/` - 相对于当前工作目录。

**Q: 日志会占用很多磁盘空间吗？**

A: 不会。系统最多保留 3 个日志文件，超过的会自动删除。

**Q: 如何查看 DEBUG 日志？**

A: 调用 `enable_debug()` 启用 DEBUG 模式，DEBUG 日志会输出到控制台和文件。

**Q: 可以改变日志存储位置吗？**

A: 当前默认位置固定为 `./lazygophers/ccplugin/log/`。如需改变，请修改 `RichLoggerManager` 中的 `log_dir` 配置。

**Q: 日志文件会一直保留吗？**

A: 不会。只保留最新的 3 个日志文件，旧文件会自动删除。

## 集成检查清单

- [ ] 在脚本中导入：`from lib.logging import info, error, warn, debug, enable_debug`
- [ ] 在关键步骤记录日志：`info("step completed")`
- [ ] 在错误处理中使用 `error()`
- [ ] 必要时使用 `debug()` 和 `enable_debug()`
- [ ] 运行测试验证：`uv run python3 -m unittest lib.tests.test_logging -v`

## 架构设计

```
lib/logging/
├── __init__.py          → 导出简洁的 5 个 API 函数
├── manager.py           → RichLoggerManager 单例实现
│   ├── enable_debug()   → 启用控制台输出
│   ├── info()           → 记录 INFO 日志
│   ├── debug()          → 记录 DEBUG 日志
│   ├── error()          → 记录 ERROR 日志
│   ├── warn()           → 记录 WARNING 日志
│   ├── _write_to_file() → 写入日志文件
│   ├── _cleanup_old_logs() → 清理过期日志
│   └── ...
└── README.md            → 本文档
```

## 关键设计决策

1. **单实例模式** - 全局唯一的日志管理器，避免重复创建
2. **简洁 API** - 只导出 5 个必要的函数，易于学习和使用
3. **Rich 库** - 提供美观的彩色输出和格式化
4. **按小时分割** - 适合日常开发和调试，文件大小可控
5. **自动清理** - 保留最新 3 个文件，无需手动管理

## 许可证

与 ccplugin 项目相同。
