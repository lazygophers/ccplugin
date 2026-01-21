"""
日志模块 - 提供统一的日志管理功能。

特性：
- 按小时自动分割日志文件 (YYYYMMDDHH.log)
- 自动清理超过 3 小时的旧日志
- 支持全局日志级别配置
- 支持 DEBUG 模式下的控制台输出
- 简洁的 API 接口

使用示例：

    # 基础使用
    from lib.logging import get_logger
    logger = get_logger(__name__)
    logger.info("操作成功")
    logger.error("发生错误")

    # 启用 DEBUG 模式（同时输出到控制台）
    logger = get_logger(__name__, debug=True)

    # 全局配置
    from lib.logging import setup_logging
    setup_logging(
        log_dir="./logs",
        level=logging.DEBUG,
        enable_console=True
    )
"""

import logging
from .setup_utils import setup_logging, get_logger, set_level
from .handler import HourlyRotatingFileHandler

__all__ = [
    'setup_logging',
    'get_logger',
    'set_level',
    'HourlyRotatingFileHandler',
]
