"""
日志模块 - 基于 Rich 的简洁日志系统。

特性：
- 使用 Rich 库进行彩色输出和格式化
- 按小时自动分割日志文件 (YYYYMMDDHH.log)
- 自动清理超过 3 小时的旧日志
- 单实例设计，简洁的函数式 API
- 支持 DEBUG 模式下的控制台输出

使用示例：

    from ccplugin.lib.logging import info, debug, error, warn, enable_debug

    # 基础使用
    info("操作启动")
    error("发生错误")

    # 启用 DEBUG 模式
    enable_debug()
    debug("调试信息（输出到控制台）")
"""

from .manager import enable_debug, info, debug, error, warn, warning

__all__ = [
    'enable_debug',
    'info',
    'debug',
    'error',
    'warn',
    'warning',
]