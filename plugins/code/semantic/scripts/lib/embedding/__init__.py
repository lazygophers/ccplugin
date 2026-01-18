"""
Embedding Module
嵌入和向量化功能库

提供代码和文本的向量化功能，包括：
- EmbeddingGenerator - 文本向量生成
- CodeModelEngine - 代码专用嵌入模型
- 存储接口 - 向量存储和检索
"""

from .generator import EmbeddingGenerator, generate_code_id, truncate_code
from .code_model import CodeModelEngine
from .storage import LanceDBStorage

__all__ = [
    "EmbeddingGenerator",
    "CodeModelEngine",
    "LanceDBStorage",
    "generate_code_id",
    "truncate_code",
]
