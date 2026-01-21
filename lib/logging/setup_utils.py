"""
日志设置工具 - 提供日志配置的便捷接口。
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from .handler import HourlyRotatingFileHandler


# 全局日志记录器字典
_loggers = {}


def setup_logging(
    log_dir: Optional[str] = None,
    level: int = logging.INFO,
    enable_console: bool = False,
) -> None:
    """
    设置全局日志配置。

    Args:
        log_dir: 日志目录，默认为 ./lazygophers/ccplugin/log
        level: 日志级别，默认为 INFO
        enable_console: 是否同时输出到控制台，默认为 False
    """
    global _loggers

    if log_dir is None:
        # 默认使用相对于当前工作目录的路径
        log_dir = str(Path.cwd() / "lazygophers" / "ccplugin" / "log")

    # 更新所有已存在的 logger
    for logger in _loggers.values():
        # 移除旧的处理器
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        # 添加新的文件处理器
        file_handler = HourlyRotatingFileHandler(log_dir, level=level)
        file_handler.setFormatter(_get_formatter())
        logger.addHandler(file_handler)

        # 如果需要，添加控制台处理器
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(_get_formatter())
            logger.addHandler(console_handler)

        logger.setLevel(level)


def get_logger(
    name: str,
    debug: bool = False,
) -> logging.Logger:
    """
    获取日志记录器。

    Args:
        name: 日志记录器名称（通常为 __name__ 或模块名）
        debug: 是否启用 DEBUG 级别并输出到控制台

    Returns:
        配置好的 Logger 实例
    """
    global _loggers

    if name in _loggers:
        logger = _loggers[name]
    else:
        logger = logging.getLogger(name)
        _loggers[name] = logger

        # 设置默认日志目录
        log_dir = str(Path.cwd() / "lazygophers" / "ccplugin" / "log")

        # 添加文件处理器
        level = logging.DEBUG if debug else logging.INFO
        file_handler = HourlyRotatingFileHandler(log_dir, level=level)
        file_handler.setFormatter(_get_formatter())
        logger.addHandler(file_handler)

        # 如果启用 debug，同时输出到控制台
        if debug:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(_get_formatter())
            logger.addHandler(console_handler)

        logger.setLevel(level)

    return logger


def set_level(level: int) -> None:
    """
    设置所有日志记录器的级别。

    Args:
        level: 日志级别（logging.DEBUG, logging.INFO, 等）
    """
    for logger in _loggers.values():
        logger.setLevel(level)
        for handler in logger.handlers:
            handler.setLevel(level)


def _get_formatter() -> logging.Formatter:
    """
    获取日志格式化器。

    格式: 时间 级别 文件:行号 消息
    """
    fmt = '%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    datefmt = '%Y-%m-%d %H:%M:%S'
    return logging.Formatter(fmt, datefmt=datefmt)
