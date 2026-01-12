#!/usr/bin/env python3
"""
简单代码解析器

基于行数的简单分块解析器，用于：
- 不需要复杂解析的语言
- 回退方案
"""

from pathlib import Path
from typing import List, Dict

from .base import CodeParser


class SimpleParser(CodeParser):
    """简单代码解析器 - 基于行数的分块"""

    def __init__(self, language: str, chunk_lines: int = 50):
        super().__init__(language)
        self.chunk_lines = chunk_lines

    def parse_file(self, file_path: Path) -> List[Dict]:
        """解析文件（简单分块）"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            return self.parse_code(code, str(file_path))
        except Exception as e:
            print(f"警告: 解析 {file_path} 失败: {e}")
            return []

    def parse_code(self, code: str, file_path: str) -> List[Dict]:
        """解析代码（简单分块）"""
        chunks = []
        lines = code.split("\n")

        for i in range(0, len(lines), self.chunk_lines):
            chunk_lines = lines[i : i + self.chunk_lines]
            chunk_code = "\n".join(chunk_lines)

            chunks.append(
                {
                    "type": "block",
                    "name": f"block_{i // self.chunk_lines + 1}",
                    "code": chunk_code,
                    "start_line": i + 1,
                    "end_line": i + len(chunk_lines),
                    "file_path": file_path,
                    "language": self.language,
                    "metadata": {},
                }
            )

        return chunks
