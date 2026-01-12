"""
Parsers Module
代码解析器库

提供标准化的代码解析接口和多语言解析器实现，包括：
- 解析器基类和接口定义
- Tree-Sitter通用解析器
- 语言特定的解析器
"""

from pathlib import Path
from typing import List, Dict, Optional

from .base import CodeParser
from .python_parser import PythonParser
from .javascript_parser import JavaScriptParser
from .golang_parser import GoParser
from .java_parser import JavaParser
from .rust_parser import RustParser
from .kotlin_parser import KotlinParser
from .flutter_parser import DartParser
from .simple_parser import SimpleParser
from .tree_sitter_base import TreeSitterParser


def parse_file(file_path: Path, language: str) -> List[Dict]:
    """根据语言类型解析代码文件

    Args:
        file_path: 代码文件路径
        language: 编程语言名称

    Returns:
        解析结果列表，每个元素包含 type, name, code, start_line, end_line, file_path, language, metadata
    """
    file_path = Path(file_path)

    # 根据语言类型选择相应的解析器
    parser_map = {
        "python": PythonParser,
        "javascript": JavaScriptParser,
        "typescript": JavaScriptParser,
        "go": GoParser,
        "java": JavaParser,
        "rust": RustParser,
        "kotlin": KotlinParser,
        "dart": DartParser,
    }

    parser_class = parser_map.get(language.lower(), SimpleParser)
    parser = parser_class(language)

    try:
        chunks = parser.parse_file(file_path)
        # 确保每个 chunk 都有正确的字段
        for chunk in chunks:
            if "file_path" not in chunk:
                chunk["file_path"] = str(file_path)
            if "language" not in chunk:
                chunk["language"] = language
        return chunks
    except Exception:
        return []


__all__ = [
    "CodeParser",
    "TreeSitterParser",
    "parse_file",
    "PythonParser",
    "JavaScriptParser",
    "GoParser",
    "JavaParser",
    "RustParser",
    "KotlinParser",
    "DartParser",
    "SimpleParser",
]
