"""
RichLoggerManager - 基于 Rich 的单实例日志管理器。

提供简洁的日志 API，支持按小时分割日志文件，
自动清理过期日志，并支持彩色控制台输出。
"""

import sys
import glob
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from rich.console import Console
from rich.logging import RichHandler

from lib.utils.env import base_dir, app_name


class RichLoggerManager:
    """
    Rich 日志管理器（单实例）。

    特性：
    - 按小时自动分割日志文件 (YYYYMMDDHH.log)
    - 自动删除超过 3 小时的旧日志文件
    - 彩色控制台输出
    - 简洁的 API
    """

    _instance: Optional["RichLoggerManager"] = None

    def __new__(cls):
        """实现单例模式。"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初始化日志管理器。"""
        if self._initialized:
            return

        self._initialized = True
        self.log_dir = os.path.join(base_dir, "log")
        os.makedirs(self.log_dir, exist_ok=True)

        # 创建主控制台（文件输出）
        self.file_console = Console(
            file=open(str(self._get_log_file()), "a", encoding="utf-8"),
            force_terminal=False,
            legacy_windows=False,
        )

        # 创建控制台输出器（默认关闭）
        self.console_console: Optional[Console] = None
        self.debug_enabled = False
        self._last_hour = self._get_current_hour()

    def enable_debug(self) -> None:
        """启用 DEBUG 模式（同时输出到控制台）。"""
        self.debug_enabled = True
        if self.console_console is None:
            self.console_console = Console(force_terminal=True)

    def disable_debug(self) -> None:
        """禁用 DEBUG 模式。"""
        self.debug_enabled = False
        if self.console_console is not None:
            self.console_console = None

    def info(self, message: str) -> None:
        """记录 INFO 级别日志。"""
        self._log("ℹ️  INFO", message, "blue")

    def debug(self, message: str) -> None:
        """记录 DEBUG 级别日志（仅在 DEBUG 模式显示）。"""
        if self.debug_enabled:
            self._log("🐛 DEBUG", message, "cyan")
        else:
            # 仅写入文件
            self.file_console.print(f"[cyan]🐛 DEBUG[/cyan] {message}")

    def error(self, message: str) -> None:
        """记录 ERROR 级别日志。"""
        self._log("❌ ERROR", message, "red")

    def warn(self, message: str) -> None:
        """记录 WARNING 级别日志。"""
        self._log("⚠️  WARNING", message, "yellow")

    def _log(self, level: str, message: str, color: str) -> None:
        """
        内部日志记录函数。

        Args:
            level: 日志级别标签
            message: 日志消息
            color: 颜色标签
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        app_prefix = f"[{app_name}] " if app_name else ""
        formatted = f"{app_prefix}[{color}]{level}[/{color}] [{timestamp}] {message}"

        # 写入文件
        self._write_to_file(formatted)

        # 如果启用 DEBUG 或需要输出到控制台
        if self.debug_enabled and level in ("🐛 DEBUG", "ℹ️  INFO"):
            if self.console_console:
                self.console_console.print(formatted)
        elif level in ("❌ ERROR", "⚠️  WARNING"):
            if self.console_console:
                self.console_console.print(formatted)

    def _write_to_file(self, message: str) -> None:
        """
        写入日志文件。

        检查是否需要轮转到新文件，然后写入日志。
        """
        current_hour = self._get_current_hour()

        # 检查是否需要轮转文件
        if self._last_hour != current_hour:
            self._last_hour = current_hour
            # 关闭旧文件
            if hasattr(self.file_console, "file") and self.file_console.file:
                self.file_console.file.close()

            # 打开新文件
            new_file = open(str(self._get_log_file()), "a", encoding="utf-8")
            self.file_console.file = new_file
            self._cleanup_old_logs()

        # 写入日志
        self.file_console.print(message)

    def _get_current_hour(self) -> str:
        """获取当前小时的格式化字符串 (YYYYMMDDHH)。"""
        return datetime.now().strftime("%Y%m%d%H")

    def _get_log_file(self) -> Path:
        """获取当前小时的日志文件路径。"""
        hour = self._get_current_hour()
        return self.log_dir / f"{hour}.log"

    def _cleanup_old_logs(self) -> None:
        """删除超过 3 小时的日志文件，保留最新 3 个。"""
        log_files = sorted(glob.glob(str(self.log_dir / "*.log")))

        if len(log_files) > 3:
            for old_log in log_files[:-3]:
                try:
                    os.remove(old_log)
                except OSError:
                    pass


# 创建全局单实例
_logger = RichLoggerManager()


def enable_debug() -> None:
    """启用 DEBUG 模式（同时输出到控制台）。"""
    _logger.enable_debug()


def info(message: str) -> None:
    """记录 INFO 级别日志。"""
    _logger.info(message)


def debug(message: str) -> None:
    """记录 DEBUG 级别日志（仅在 DEBUG 模式显示到控制台）。"""
    _logger.debug(message)


def error(message: str) -> None:
    """记录 ERROR 级别日志。"""
    _logger.error(message)


def warn(message: str) -> None:
    """记录 WARNING 级别日志。"""
    _logger.warn(message)

def set_app(app_name: str) -> None:
    """
    注册应用名称。

    Args:
        app_name: 应用名称（如 'version'、'task' 等）
    """
    _logger.set_app_name(app_name)