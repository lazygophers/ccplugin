#!/usr/bin/env python3
"""
代码解析器基类

定义所有解析器的通用接口。
"""

from pathlib import Path
from typing import List, Dict, Optional
from abc import ABC, abstractmethod


class CodeParser(ABC):
    """代码解析器基类"""

    def __init__(self, language: str):
        self.language = language

    @abstractmethod
    def parse_file(self, file_path: Path) -> List[Dict]:
        """解析单个文件

        Args:
            file_path: 文件路径

        Returns:
            解析结果列表，每个元素包含 type, name, code, start_line, end_line, file_path, language, metadata
        """
        pass

    def parse_code(self, code: str, file_path: str) -> List[Dict]:
        """解析代码字符串

        Args:
            code: 代码字符串
            file_path: 文件路径（用于元数据）

        Returns:
            解析结果列表
        """
        pass
