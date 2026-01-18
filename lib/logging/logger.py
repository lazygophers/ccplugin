"""
核心日志管理器实现。
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import threading


class LogManager:
    """日志管理器 - 处理日志分片、轮转和输出。"""

    # 日志级别常量
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR

    # 日志保留小时数
    RETENTION_HOURS = 3

    def __init__(self, plugin_name: str, enable_console: bool = True):
        """
        初始化日志管理器。

        Args:
            plugin_name: 插件名称（用于日志标识）
            enable_console: 是否输出到控制台
        """
        self.plugin_name = plugin_name
        self.enable_console = enable_console

        # 初始化日志目录
        self.log_dir = self._ensure_log_dir()

        # 创建 logger
        self.logger = logging.getLogger(plugin_name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()

        # 记录当前小时的日志文件
        self._current_hour: Optional[str] = None
        self._file_handler: Optional[logging.FileHandler] = None
        self._lock = threading.Lock()

        # 添加初始处理器
        self._rotate_if_needed()

    def _ensure_log_dir(self) -> Path:
        """确保日志目录存在。"""
        log_dir = Path.home() / ".lazygophers" / "ccplugin" / "log"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    def _get_hour_key(self) -> str:
        """获取当前小时的键（YYYYMMDDHH 格式）。"""
        return datetime.now().strftime("%Y%m%d%H")

    def _get_log_file_path(self, hour_key: str) -> Path:
        """获取指定小时的日志文件路径。"""
        return self.log_dir / f"{hour_key}.log"

    def _get_symlink_path(self) -> Path:
        """获取软连接路径。"""
        return self.log_dir / "log.log"

    def _rotate_if_needed(self) -> None:
        """检查是否需要轮转日志文件。"""
        with self._lock:
            current_hour = self._get_hour_key()

            # 检查是否跨小时
            if self._current_hour != current_hour:
                # 关闭旧的文件处理器
                if self._file_handler:
                    self._file_handler.close()
                    self.logger.removeHandler(self._file_handler)

                # 添加新的文件处理器
                self._current_hour = current_hour
                log_file = self._get_log_file_path(current_hour)
                self._add_file_handler(log_file)

                # 更新软连接
                self._update_symlink(log_file)

                # 清理过期日志
                self._cleanup_old_logs()

    def _add_file_handler(self, log_file: Path) -> None:
        """添加文件处理器。"""
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # 文件处理器 - 写所有级别（除 DEBUG）
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_formatter = logging.Formatter(
            '[%(asctime)s.%(msecs)03d] [%(levelname)s] [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)

        # 如果启用控制台输出，添加控制台处理器
        if self.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_formatter = logging.Formatter(
                '[%(asctime)s.%(msecs)03d] [%(levelname)s] [%(name)s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            console_handler.setLevel(logging.INFO)
            self.logger.addHandler(console_handler)

        self._file_handler = file_handler

    def _update_symlink(self, target_file: Path) -> None:
        """更新软连接指向最新日志文件。"""
        symlink_path = self._get_symlink_path()

        try:
            # 删除旧的软连接
            if symlink_path.exists() or symlink_path.is_symlink():
                symlink_path.unlink()

            # 创建新的软连接（相对路径）
            symlink_path.symlink_to(target_file.name)
        except (OSError, Exception) as e:
            self.logger.error(f"更新软连接失败: {e}")

    def _cleanup_old_logs(self) -> None:
        """清理超过保留小时数的旧日志。"""
        try:
            now = datetime.now()
            cutoff_hour = now.strftime("%Y%m%d%H")

            # 找出所有日志文件
            for log_file in self.log_dir.glob("*.log"):
                # 跳过软连接
                if log_file.is_symlink():
                    continue

                # 提取时间戳
                try:
                    hour_key = log_file.stem  # 去掉 .log 后缀
                    # 检查文件名格式是否为 YYYYMMDDHH
                    if len(hour_key) == 10 and hour_key.isdigit():
                        file_hour = datetime.strptime(hour_key, "%Y%m%d%H")
                        cutoff_time = datetime.strptime(cutoff_hour, "%Y%m%d%H")

                        # 计算时间差（小时）
                        hours_diff = (cutoff_time - file_hour).total_seconds() / 3600

                        if hours_diff >= self.RETENTION_HOURS:
                            log_file.unlink()
                except (ValueError, Exception):
                    # 跳过无法解析的文件
                    pass

        except Exception as e:
            self.logger.error(f"清理旧日志失败: {e}")

    def debug(self, message: str) -> None:
        """记录 DEBUG 级别日志（仅控制台）。"""
        self._rotate_if_needed()
        if self.enable_console:
            self.logger.debug(message)

    def info(self, message: str) -> None:
        """记录 INFO 级别日志（文件 + 控制台）。"""
        self._rotate_if_needed()
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """记录 WARNING 级别日志（文件 + 控制台）。"""
        self._rotate_if_needed()
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """记录 ERROR 级别日志（文件 + 控制台）。

        仅记录错误信息本身，不包含 traceback。
        """
        self._rotate_if_needed()
        self.logger.error(message)

    def exception(self, message: str) -> None:
        """记录异常信息（仅文件）。

        记录异常信息但不记录完整 traceback。
        仅输出到文件，不输出到控制台。
        """
        self._rotate_if_needed()

        # 临时降低日志级别以捕获异常
        # 创建一个不输出到控制台的临时处理器
        file_only_handler = self._file_handler
        if file_only_handler:
            # 直接写入文件，不通过标准 logger 以避免控制台输出
            try:
                import traceback
                exc_info = sys.exc_info()
                if exc_info[0]:
                    error_msg = traceback.format_exc()
                    file_only_handler.emit(
                        logging.LogRecord(
                            name=self.plugin_name,
                            level=logging.ERROR,
                            pathname='',
                            lineno=0,
                            msg=f"{message}\n{error_msg}",
                            args=(),
                            exc_info=None
                        )
                    )
            except Exception:
                pass


# 全局 logger 缓存
_loggers = {}
_lock = threading.Lock()


def get_logger(plugin_name: str, enable_console: bool = True) -> LogManager:
    """获取或创建一个日志管理器。

    Args:
        plugin_name: 插件名称
        enable_console: 是否输出到控制台

    Returns:
        LogManager 实例
    """
    with _lock:
        key = (plugin_name, enable_console)
        if key not in _loggers:
            _loggers[key] = LogManager(plugin_name, enable_console)
        return _loggers[key]
