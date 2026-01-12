"""
Parsers Module
代码解析器库

提供标准化的代码解析接口和多语言解析器实现，包括：
- 解析器基类和接口定义
- Tree-Sitter通用解析器
- 语言特定的解析器
"""

__all__ = [
    "CodeParser",
    "TreeSitterParser",
]
