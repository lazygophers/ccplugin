"""
RichLoggerManager - 基于 Rich 的单实例日志管理器。

提供简洁的日志 API，支持按小时分割日志文件，
自动清理过期日志，并支持彩色控制台输出。
"""

import glob
import inspect
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from rich.console import Console

from lib.utils.env import get_project_plugins_dir


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
        self.log_dir = os.path.join(get_project_plugins_dir(), "log")
        os.makedirs(self.log_dir, exist_ok=True)

        # 创建主控制台（文件输出）
        # 设置 width=99999 防止长消息自动换行
        self.file_console = Console(
            file=open(str(self._get_log_file()), "a", encoding="utf-8"),
            force_terminal=False,
            legacy_windows=False,
            width=99999,
        )

        # 创建控制台输出器（默认关闭）
        self.console_console: Optional[Console] = Console(force_terminal=True, width=99999)
        self.debug_enabled = False
        self._last_hour = self._get_current_hour()

        # 初始化时清理旧日志文件
        self._cleanup_old_logs()

        # 初始化时创建软连接
        self._update_symlink()

    def enable_debug(self) -> None:
        """启用 DEBUG 模式（同时输出到控制台）。"""
        self.debug_enabled = True

    def disable_debug(self) -> None:
        """禁用 DEBUG 模式。"""
        self.debug_enabled = False

    def info(self, message: str) -> None:
        """记录 INFO 级别日志。"""
        self._log("INFO", message, "blue")

    def debug(self, message: str) -> None:
        """记录 DEBUG 级别日志（仅在 DEBUG 模式显示）。"""
        caller_info = self._get_caller_info(skip=4)
        formatted = f"[cyan]DEBUG[/cyan] [{datetime.now().strftime("%H:%M:%S")}] [dim]{caller_info}[/dim] {message}"

        if self.debug_enabled:
            if self.console_console:
                self.console_console.print(formatted)

        # 始终写入文件
        self.file_console.print(formatted)

    def error(self, message: str) -> None:
        """记录 ERROR 级别日志。"""
        self._log("ERROR", message, "red")

    def warn(self, message: str) -> None:
        """记录 WARNING 级别日志。"""
        self._log("WARNING", message, "yellow")

    def _get_caller_info(self, skip: int = 2) -> str:
        """
        获取调用者的文件位置信息。

        Args:
            skip: 跳过的调用栈层级数

        Returns:
            格式化的文件位置信息，如 "filename.py:123"
        """
        try:
            stack = inspect.stack()
            frame = stack[skip]
            filename = os.path.basename(frame.filename)
            lineno = frame.lineno
            return f"{filename}:{lineno}"
        except (IndexError, AttributeError):
            return "unknown:0"

    def _log(self, level: str, message: str, color: str) -> None:
        """
        内部日志记录函数。

        Args:
            level: 日志级别标签
            message: 日志消息
            color: 颜色标签
        """
        from lib.utils.env import Env
        formatted = f"[{Env.get_app_name()}][{color}]{level}[/{color}] [{datetime.now().strftime("%M:%S")}] [dim]{self._get_caller_info(skip=4)}[/dim] {message}"

        # 写入文件
        self._write_to_file(formatted)

        # 如果启用 DEBUG 或需要输出到控制台
        if self.debug_enabled:
            if self.console_console:
                self.console_console.print(formatted)
        elif level in ("ERROR"):
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
            self._update_symlink()

        # 写入日志
        self.file_console.print(message)

        # 刷新文件缓冲区，确保日志立即写入
        if hasattr(self.file_console, "file") and self.file_console.file:
            self.file_console.file.flush()

    def _get_current_hour(self) -> str:
        """获取当前小时的格式化字符串 (YYYYMMDDHH)。"""
        return datetime.now().strftime("%Y%m%d%H")

    def _get_log_file(self) -> Path:
        """获取当前小时的日志文件路径。"""
        hour = self._get_current_hour()
        return Path(self.log_dir) / f"{hour}.log"

    def _cleanup_old_logs(self) -> None:
        """删除超过 3 小时的日志文件，保留最新 3 个。"""
        log_files = sorted(glob.glob(str(Path(self.log_dir) / "*.log")))

        if len(log_files) > 3:
            for old_log in log_files[:-3]:
                try:
                    os.remove(old_log)
                except OSError:
                    pass

    def _update_symlink(self) -> None:
        """更新软连接，使 log.log 指向当前小时的日志文件。"""
        symlink_path = Path(self.log_dir) / "log.log"
        current_log_file = self._get_log_file()

        try:
            # 如果软连接已存在，删除它
            if symlink_path.is_symlink():
                symlink_path.unlink()

            # 创建新的软连接
            symlink_path.symlink_to(current_log_file.name)
        except (OSError, FileNotFoundError):
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