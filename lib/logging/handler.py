"""
日志处理器模块 - 提供按小时分割的日志处理功能。
"""

import logging
import os
import glob
import time
from datetime import datetime, timedelta
from pathlib import Path


class HourlyRotatingFileHandler(logging.FileHandler):
    """
    按小时分割的日志处理器。

    每小时创建一个新的日志文件（格式：YYYYMMDDHH.log），
    自动删除超过 3 小时的日志文件。
    """

    def __init__(self, log_dir: str, level=logging.NOTSET):
        """
        初始化处理器。

        Args:
            log_dir: 日志文件目录
            level: 日志级别
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.level = level

        # 获取当前日志文件路径
        self.current_hour = self._get_current_hour()
        log_file = self.log_dir / f"{self.current_hour}.log"

        super().__init__(str(log_file), mode='a', encoding='utf-8')
        self.setLevel(level)

    def emit(self, record: logging.LogRecord) -> None:
        """
        发出日志记录。

        检查是否需要轮转文件，然后发出记录。
        """
        try:
            # 检查是否需要轮转文件
            current_hour = self._get_current_hour()
            if current_hour != self.current_hour:
                self._rotate_file(current_hour)

            # 调用父类方法发出日志
            super().emit(record)
        except Exception:
            self.handleError(record)

    def _get_current_hour(self) -> str:
        """获取当前小时的格式化字符串 (YYYYMMDDHH)。"""
        return datetime.now().strftime('%Y%m%d%H')

    def _rotate_file(self, new_hour: str) -> None:
        """
        轮转日志文件。

        Args:
            new_hour: 新小时的格式化字符串
        """
        # 关闭当前文件
        self.close()

        # 更新当前小时
        self.current_hour = new_hour

        # 打开新的日志文件
        log_file = self.log_dir / f"{new_hour}.log"
        self.baseFilename = str(log_file)
        self.stream = self._open()

        # 清理过期的日志文件
        self._cleanup_old_logs()

    def _cleanup_old_logs(self) -> None:
        """删除超过 3 小时的日志文件。"""
        log_files = sorted(glob.glob(str(self.log_dir / "*.log")))

        # 保留最新的 3 个文件
        if len(log_files) > 3:
            for old_log in log_files[:-3]:
                try:
                    os.remove(old_log)
                except OSError:
                    pass
