#!/usr/bin/env python3
"""
嵌入生成器 - 生成代码和查询的向量嵌入

使用 FastEmbed 库，轻量快速、支持 GPU 加速。
参考: https://github.com/qdrant/fastembed
"""

from pathlib import Path
from typing import List, Union, Optional
import hashlib
import warnings


class FastEmbedModel:
    """FastEmbed 模型实现"""

    def __init__(self, model_name: str, use_gpu: bool = True):
        self.model_name = model_name
        self.use_gpu = use_gpu
        self.model = None
        self.dim = 384  # 默认维度

    def load(self):
        """加载 FastEmbed 模型"""
        try:
            from fastembed import TextEmbedding

            # 过滤 fastembed 的警告
            warnings.filterwarnings("ignore", category=UserWarning, message=".*mean pooling instead of CLS embedding.*")

            # 设置 GPU 提供商
            providers = None
            if self.use_gpu:
                try:
                    import fastembed_gpu

                    providers = ["CUDAExecutionProvider"]
                except ImportError:
                    # fastembed-gpu 未安装，使用 CPU
                    pass

            # 加载模型
            self.model = TextEmbedding(
                model_name=self.model_name,
                providers=providers,
            )

            # 获取维度
            embeddings = list(self.model.embed(["test"]))
            if embeddings:
                self.dim = len(embeddings[0])

            return True
        except ImportError:
            print("错误: 未安装 fastembed")
            print("安装命令: uv pip install fastembed")
            return False
        except Exception as e:
            print(f"错误: 模型加载失败: {e}")
            return False

    def encode(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """生成嵌入向量"""
        if not self.model:
            self.load()

        try:
            # 确保输入是列表
            if isinstance(texts, str):
                texts = [texts]

            # 生成嵌入
            embeddings = list(self.model.embed(texts))

            # 转换为列表
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            print(f"错误: 嵌入生成失败: {e}")
            return []

    def get_dim(self) -> int:
        """获取向量维度"""
        return self.dim


class EmbeddingGenerator:
    """嵌入生成器 - 统一接口"""

    MODELS = {
        # ========== BGE 系列（推荐） ==========
        "bge-small-en": "BAAI/bge-small-en-v1.5",  # 384维，英文
        "bge-small-zh": "BAAI/bge-small-zh-v1.5",  # 512维，中文
        "bge-base-en": "BAAI/bge-base-en-v1.5",  # 768维，英文
        "bge-large-en": "BAAI/bge-large-en-v1.5",  # 1024维，英文高精度

        # ========== Jina 系列 ==========
        "jina-small-en": "jinaai/jina-embeddings-v2-small-en",  # 512维
        "jina-base-en": "jinaai/jina-embeddings-v2-base-en",  # 768维
        "jina-base-de": "jinaai/jina-embeddings-v2-base-de",  # 768维，德语
        "jina-code": "jinaai/jina-embeddings-v2-base-code",  # 768维，多语言代码

        # ========== Snowflake Arctic 系列 ==========
        "arctic-embed-xs": "snowflake/snowflake-arctic-embed-xs",  # 384维，极轻量
        "arctic-embed-s": "snowflake/snowflake-arctic-embed-s",  # 384维，轻量
        "arctic-embed-m": "snowflake/snowflake-arctic-embed-m",  # 768维
        "arctic-embed-m-long": "snowflake/snowflake-arctic-embed-m-long",  # 768维，长文本
        "arctic-embed-l": "snowflake/snowflake-arctic-embed-l",  # 1024维，高精度

        # ========== Nomic 系列（多模态） ==========
        "nomic-embed-text": "nomic-ai/nomic-embed-text-v1",  # 768维
        "nomic-embed-text-1.5": "nomic-ai/nomic-embed-text-v1.5",  # 768维
        "nomic-embed-text-Q": "nomic-ai/nomic-embed-text-v1.5-Q",  # 768维，量化版

        # ========== Sentence Transformers 系列 ==========
        "all-minilm-l6-v2": "sentence-transformers/all-MiniLM-L6-v2",  # 384维，极轻量
        "paraphrase-multilingual-mpnet": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",  # 768维，多语言
        "paraphrase-multilingual-MiniLM": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",  # 384维，多语言

        # ========== E5 系列（多语言） ==========
        "multilingual-e5-small": "intfloat/multilingual-e5-small",  # 384维
        "multilingual-e5-large": "intfloat/multilingual-e5-large",  # 1024维，多语言高精度

        # ========== GTE 系列 ==========
        "gte-large": "thenlper/gte-large",  # 1024维

        # ========== MXBAI 系列 ==========
        "mxbai-embed-large": "mixedbread-ai/mxbai-embed-large-v1",  # 1024维

        # ========== CLIP 系列（多模态） ==========
        "clip-vit-b-32": "Qdrant/clip-ViT-B-32-text",  # 512维，多模态

        # ========== 兼容性别名 ==========
        "default": "BAAI/bge-small-en-v1.5",  # 384维，默认
        "bge-small-en-v1.5": "BAAI/bge-small-en-v1.5",
        "bge-base-en-v1.5": "BAAI/bge-base-en-v1.5",
    }

    def __init__(self, model_id: str = "default", use_gpu: bool = True):
        self.model_id = model_id
        self.use_gpu = use_gpu
        self.model_name = self.MODELS.get(model_id, model_id)
        self.model = None

    def load(self) -> bool:
        """加载模型"""
        if self.model:
            return True

        self.model = FastEmbedModel(self.model_name, self.use_gpu)
        return self.model.load()

    def encode(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """生成嵌入向量"""
        if not self.model:
            self.load()

        return self.model.encode(texts)

    def encode_query(self, query: str) -> List[float]:
        """为查询生成嵌入（可选特殊处理）"""
        embeddings = self.encode(query)
        return embeddings[0] if embeddings else []

    def get_dim(self) -> int:
        """获取向量维度"""
        if self.model:
            return self.model.get_dim()

        # 默认维度映射
        dims = {
            "default": 384,
            "bge-small-en": 384,
            "bge-small-zh": 512,
            "bge-base-en": 768,
            "bge-large-en": 1024,
            "jina-small-en": 512,
            "jina-base-en": 768,
            "jina-base-de": 768,
            "jina-code": 768,
            "arctic-embed-xs": 384,
            "arctic-embed-s": 384,
            "arctic-embed-m": 768,
            "arctic-embed-m-long": 768,
            "arctic-embed-l": 1024,
            "nomic-embed-text": 768,
            "nomic-embed-text-1.5": 768,
            "all-minilm-l6-v2": 384,
            "paraphrase-multilingual-mpnet": 768,
            "multilingual-e5-small": 384,
            "multilingual-e5-large": 1024,
            "gte-large": 1024,
            "mxbai-embed-large": 1024,
            "clip-vit-b-32": 512,
        }
        return dims.get(self.model_id, 384)

    def is_loaded(self) -> bool:
        """检查模型是否已加载"""
        return self.model is not None


def generate_code_id(file_path: str, start_line: int, code_type: str) -> str:
    """生成代码块唯一 ID"""
    content = f"{file_path}:{start_line}:{code_type}"
    hash_obj = hashlib.md5(content.encode())
    return hash_obj.hexdigest()[:16]


def truncate_code(code: str, max_length: int = 8192) -> str:
    """截断代码以适应模型最大长度"""
    # 粗略估计：1 token ≈ 4 字符
    max_chars = max_length * 4
    if len(code) <= max_chars:
        return code
    return code[:max_chars]
