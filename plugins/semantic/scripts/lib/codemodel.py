#!/usr/bin/env python3
"""
代码模型引擎 - 支持代码专用嵌入模型

使用 sentence-transformers 加载代码专用模型，如 CodeT5、UniXcoder、GraphCodeBERT。
"""

from pathlib import Path
from typing import List, Union, Optional
import hashlib
import warnings


class CodeModelEngine:
    """代码专用模型引擎 - 使用 sentence-transformers"""

    MODELS = {
        # 代码嵌入模型（使用 sentence-transformers 兼容的模型）
        # 注意：这些是通用模型，对代码理解仍然有效
        "codet5+": "sentence-transformers/all-mpnet-base-v2",  # 最佳质量通用模型
        "codet5-base": "sentence-transformers/all-mpnet-base-v2",  # 基础版
        "codet5-small": "sentence-transformers/all-MiniLM-L6-v2",  # 小型快速版
        "codet5-large": "sentence-transformers/all-mpnet-base-v2",  # 大型版

        # UniXcoder 系列（直接使用 HuggingFace 模型）
        "unixcoder": "microsoft/unixcoder-base",
        "unixcoder-small": "microsoft/unixcoder-small",

        # GraphCodeBERT
        "graphcodebert": "microsoft/graphcodebert-base",

        # CodeBERT
        "codebert": "microsoft/codebert-base",

        # Code Parrot
        "codeparrot": "codeparrot/codeparrot",
    }

    def __init__(self, model_name: str, use_gpu: bool = True):
        self.model_name = self.MODELS.get(model_name, model_name)
        self.use_gpu = use_gpu
        self.model = None
        self.device = None
        self.dim = 768  # 默认维度

    def load(self) -> bool:
        """加载代码模型"""
        try:
            from sentence_transformers import SentenceTransformer
            import torch

            # 过滤 sentence-transformers 的警告
            warnings.filterwarnings("ignore", category=UserWarning)

            # 检测设备
            if self.use_gpu:
                if torch.cuda.is_available():
                    self.device = "cuda"
                elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                    self.device = "mps"
                else:
                    self.device = "cpu"
            else:
                self.device = "cpu"

            # 加载模型（自动下载）
            self.model = SentenceTransformer(self.model_name, device=self.device)
            self.dim = self.model.get_sentence_embedding_dimension()
            return True

        except ImportError:
            print("错误: 未安装 sentence-transformers")
            print("安装命令: uv pip install sentence-transformers")
            return False
        except Exception as e:
            print(f"错误: 模型加载失败: {e}")
            print(f"提示: 模型 '{self.model_name}' 可能正在从 HuggingFace 下载...")
            return False

    def encode(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """生成嵌入向量"""
        if not self.model:
            self.load()

        try:
            if isinstance(texts, str):
                texts = [texts]

            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False,
            )

            return embeddings.tolist()
        except Exception as e:
            print(f"错误: 嵌入生成失败: {e}")
            return []

    def encode_query(self, query: str) -> List[float]:
        """为查询生成嵌入"""
        embeddings = self.encode(query)
        return embeddings[0] if embeddings else []

    def get_dim(self) -> int:
        """获取向量维度"""
        return self.dim

    def is_loaded(self) -> bool:
        """检查模型是否已加载"""
        return self.model is not None


class HybridEmbeddingGenerator:
    """混合嵌入生成器 - FastEmbed + CodeModel"""

    def __init__(
        self,
        fastembed_model: str = "default",
        codemodel_model: Optional[str] = None,
        use_gpu: bool = True,
    ):
        from .embedding import EmbeddingGenerator

        # FastEmbed 引擎（快速）
        self.fastembed = EmbeddingGenerator(fastembed_model, use_gpu)

        # CodeModel 引擎（精准）
        self.codemodel = None
        if codemodel_model:
            self.codemodel = CodeModelEngine(codemodel_model, use_gpu)

        self.use_gpu = use_gpu

    def load(self) -> bool:
        """加载模型"""
        success = self.fastembed.load()
        if self.codemodel:
            success = success and self.codemodel.load()
        return success

    def encode_fast(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """FastEmbed 快速编码"""
        return self.fastembed.encode(texts)

    def encode_code(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """CodeModel 代码编码"""
        if not self.codemodel:
            return self.fastembed.encode(texts)
        return self.codemodel.encode(texts)

    def encode_query(self, query: str, use_codemodel: bool = False) -> List[float]:
        """查询编码 - 选择引擎"""
        if use_codemodel and self.codemodel:
            return self.codemodel.encode_query(query)
        return self.fastembed.encode_query(query)

    def get_dim(self) -> int:
        """获取向量维度"""
        if self.codemodel:
            return self.codemodel.get_dim()
        return self.fastembed.get_dim()

    def is_loaded(self) -> bool:
        """检查模型是否已加载"""
        loaded = self.fastembed.is_loaded()
        if self.codemodel:
            loaded = loaded and self.codemodel.is_loaded()
        return loaded
