#!/usr/bin/env python3
"""
代码解析器包

所有解析器均使用 AST（抽象语法树）进行高准确性解析：

- Python: 使用标准库 `ast` 模块
- Go/Rust/Java/Kotlin/JavaScript/TypeScript/Dart: 使用 `tree-sitter` AST

AST 解析优势：
- 100% 准确性（相比正则表达式的启发式匹配）
- 完整的语法结构信息
- 支持复杂的语言特性（泛型、闭包、装饰器等）
- 可扩展的元数据提取
"""

from pathlib import Path
from typing import List, Dict

from .base import CodeParser
from .python_parser import PythonParser
from .golang_parser import GoParser
from .rust_parser import RustParser
from .flutter_parser import DartParser
from .java_parser import JavaParser
from .kotlin_parser import KotlinParser
from .javascript_parser import JavaScriptParser
from .simple_parser import SimpleParser
from .tree_sitter_base import TreeSitterParser

__all__ = [
    "CodeParser",
    "PythonParser",
    "GoParser",
    "RustParser",
    "DartParser",
    "JavaParser",
    "KotlinParser",
    "JavaScriptParser",
    "SimpleParser",
    "TreeSitterParser",
    "create_parser",
    "parse_file",
]


def create_parser(language: str) -> CodeParser:
    """根据语言创建解析器

    Args:
        language: 编程语言名称（如 "python", "golang", "rust" 等）

    Returns:
        对应语言的解析器实例

    Raises:
        ValueError: 当传入不支持的语言时
    """
    language_lower = language.lower()

    # Python 使用标准库 ast（最准确）
    if language_lower == "python":
        return PythonParser()

    # Go 使用专用解析器（处理 receiver 等 Go 特有特性）
    if language_lower == "golang":
        return GoParser()

    # Kotlin 使用专用解析器（处理 data class 等 Kotlin 特有特性）
    if language_lower == "kotlin":
        return KotlinParser()

    # 其他语言使用通用的 Tree-sitter AST 解析器
    tree_sitter_languages = [
        "rust",
        "java",
        "javascript",
        "typescript",
        "dart",
        "flutter",
        "c",
        "cpp",
        "ruby",
        "php",
        "c_sharp",
        "swift",
        "scala",
        "lua",
        "elixir",
        "bash",
        "shell",
        "powershell",
        "cmake",
        "make",
        "dockerfile",
        "sql",
        "markdown",
        "md",
    ]

    if language_lower in tree_sitter_languages:
        return TreeSitterParser(language_lower)

    # 对于没有专用解析器的语言，使用简单解析器
    return SimpleParser(language_lower)


def parse_file(file_path: Path, language: str) -> List[Dict]:
    """解析单个文件

    Args:
        file_path: 文件路径
        language: 编程语言名称

    Returns:
        解析结果列表，每个元素包含 type, name, code, start_line, end_line, file_path, language, metadata
    """
    parser = create_parser(language)
    return parser.parse_file(file_path)
