#!/usr/bin/env python3
"""
Python 代码解析器

使用 Python AST 模块解析 Python 代码，支持：
- 函数（包括异步函数）
- 类
- 装饰器
- 类型提示
"""

import ast
from pathlib import Path
from typing import List, Dict, Optional

from .base import CodeParser


class PythonParser(CodeParser):
    """Python 代码解析器"""

    def __init__(self):
        super().__init__("python")

    def parse_file(self, file_path: Path) -> List[Dict]:
        """解析 Python 文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            return self.parse_code(code, str(file_path))
        except Exception as e:
            print(f"警告: 解析 {file_path} 失败: {e}")
            return []

    def parse_code(self, code: str, file_path: str) -> List[Dict]:
        """解析 Python 代码"""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # 语法错误，返回空列表
            return []

        chunks = []

        # 遍历 AST
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                chunk = self._parse_function(node, code, file_path)
                if chunk:
                    chunks.append(chunk)
            elif isinstance(node, ast.AsyncFunctionDef):
                chunk = self._parse_function(node, code, file_path, async_func=True)
                if chunk:
                    chunks.append(chunk)
            elif isinstance(node, ast.ClassDef):
                chunk = self._parse_class(node, code, file_path)
                if chunk:
                    chunks.append(chunk)

        return chunks

    def _parse_function(
        self, node: ast.FunctionDef, code: str, file_path: str, async_func: bool = False
    ) -> Optional[Dict]:
        """解析函数定义"""
        lines = code.split("\n")

        # 获取函数代码
        start_line = node.lineno - 1
        end_line = node.end_lineno if hasattr(node, "end_lineno") else start_line + 1
        func_code = "\n".join(lines[start_line:end_line])

        return {
            "type": "function",
            "name": node.name,
            "code": func_code,
            "start_line": start_line + 1,
            "end_line": end_line + 1,
            "file_path": file_path,
            "language": "python",
            "metadata": {
                "async": async_func,
                "args": [arg.arg for arg in node.args.args],
                "decorators": [ast.unparse(d) for d in node.decorator_list],
            },
        }

    def _parse_class(self, node: ast.ClassDef, code: str, file_path: str) -> Optional[Dict]:
        """解析类定义"""
        lines = code.split("\n")

        start_line = node.lineno - 1
        end_line = node.end_lineno if hasattr(node, "end_lineno") else start_line + 1
        class_code = "\n".join(lines[start_line:end_line])

        return {
            "type": "class",
            "name": node.name,
            "code": class_code,
            "start_line": start_line + 1,
            "end_line": end_line + 1,
            "file_path": file_path,
            "language": "python",
            "metadata": {
                "bases": [ast.unparse(base) for base in node.bases],
                "decorators": [ast.unparse(d) for d in node.decorator_list],
            },
        }
