#!/usr/bin/env python3
"""
简化的语义搜索实现

使用 FAISS 或 numpy 进行向量搜索，无需复杂的数据库依赖。
"""

from pathlib import Path
from typing import List, Dict, Optional
import json
import hashlib
from datetime import datetime

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("警告: 未安装 numpy，运行: uv pip install numpy")

try:
    from fastembed import TextEmbedding
    FASTEMBED_AVAILABLE = True
except ImportError:
    FASTEMBED_AVAILABLE = False
    print("警告: 未安装 fastembed，运行: uv pip install fastembed")


class SimpleSemanticSearch:
    """简化的语义搜索 - 无需复杂数据库"""

    def __init__(self, config: Dict, data_path: Path):
        self.config = config
        self.data_path = data_path
        self.index_path = data_path / "semantic_index.json"
        self.vectors_path = data_path / "vectors.npy"

        # 存储结构
        self.documents = []  # 存储文档信息
        self.embeddings = None  # 存储向量矩阵
        self.embedding_model = None

        self._init_model()

    def _detect_hardware_acceleration(self) -> Dict[str, bool]:
        """检测可用的硬件加速

        Returns:
            包含硬件加速信息的字典:
            - apple_silicon: 是否为 Apple Silicon (M1/M2/M3)
            - nvidia_gpu: 是否有 NVIDIA GPU (CUDA)
            - mps_available: Metal Performance Shaders 是否可用
            - cuda_available: CUDA 是否可用
        """
        import platform
        result = {
            "apple_silicon": False,
            "nvidia_gpu": False,
            "mps_available": False,
            "cuda_available": False,
        }

        # 检测 Apple Silicon
        try:
            if platform.processor() == 'arm' or platform.machine() == 'arm64':
                result["apple_silicon"] = True
                # 尝试检测 MPS 是否可用
                try:
                    import torch
                    result["mps_available"] = torch.backends.mps.is_available()
                except ImportError:
                    pass
        except Exception:
            pass

        # 检测 NVIDIA GPU (CUDA)
        try:
            import torch
            result["cuda_available"] = torch.cuda.is_available()
            if result["cuda_available"]:
                result["nvidia_gpu"] = True
        except ImportError:
            pass

        return result

    def _enable_hardware_acceleration(self) -> str:
        """启用硬件加速

        Returns:
            启用的加速类型描述
        """
        import os
        acceleration_info = []

        hw_info = self._detect_hardware_acceleration()

        # Apple Silicon - Metal Performance Shaders (MPS)
        if hw_info["apple_silicon"]:
            if hw_info["mps_available"]:
                os.environ['ORT_ENABLE_MPS'] = '1'
                acceleration_info.append("Apple Silicon MPS 加速")
            else:
                acceleration_info.append("Apple Silicon (CPU 模式)")

        # NVIDIA GPU - CUDA
        if hw_info["nvidia_gpu"] and hw_info["cuda_available"]:
            # FastEmbed 会自动检测 CUDA
            acceleration_info.append("NVIDIA CUDA 加速")

        return " + ".join(acceleration_info) if acceleration_info else "CPU 模式"

    def _init_model(self):
        """初始化嵌入模型"""
        if not FASTEMBED_AVAILABLE:
            raise ImportError("需要安装 fastembed: uv add fastembed")

        # 模型名称映射（配置文件名称 -> FastEmbed 实际名称）
        model_mapping = {
            "multilingual-e5-large": "intfloat/multilingual-e5-large",
            "bge-large-en": "BAAI/bge-large-en-v1.5",
            "bge-base-en": "BAAI/bge-base-en-v1.5",
            "bge-small-en": "BAAI/bge-small-en-v1.5",
            "bge-small-zh": "BAAI/bge-small-zh-v1.5",
            "jina-base-en": "jinaai/jina-embeddings-v2-base-en",
            "jina-code": "jinaai/jina-embeddings-v2-base-code",
            "all-minilm-l6-v2": "sentence-transformers/all-MiniLM-L6-v2",
        }

        config_model = self.config.get("embedding_model", "bge-small-en")
        model_name = model_mapping.get(config_model, config_model)

        try:
            # 自动检测并启用硬件加速
            acceleration = self._enable_hardware_acceleration()
            if acceleration != "CPU 模式":
                print(f"✓ 硬件加速: {acceleration}")

            self.embedding_model = TextEmbedding(model_name)
            print(f"✓ 加载嵌入模型: {model_name}")
        except Exception as e:
            print(f"✗ 模型加载失败: {e}")
            print(f"提示: 尝试使用 'bge-small-en' 或 'all-minilm-l6-v2'")
            raise

    def index_file(self, file_path: Path, chunks: List[Dict]) -> bool:
        """索引单个文件的代码块"""
        try:
            # 提取文本内容
            texts = []
            for chunk in chunks:
                # 组合名称和代码，提高搜索准确度
                text = f"{chunk.get('name', '')} {chunk.get('code', '')}"
                texts.append(text)

            # 生成嵌入向量
            embeddings = list(self.embedding_model.embed(texts))

            # 存储到文档列表
            for chunk, embedding in zip(chunks, embeddings):
                doc = {
                    "id": self._generate_id(chunk),
                    "file_path": str(chunk.get("file_path", "")),
                    "language": chunk.get("language", ""),
                    "type": chunk.get("type", "block"),
                    "name": chunk.get("name", ""),
                    "code": chunk.get("code", ""),
                    "start_line": chunk.get("start_line", 0),
                    "end_line": chunk.get("end_line", 0),
                    "indexed_at": datetime.now().isoformat(),
                }
                self.documents.append(doc)

            # 添加到向量矩阵
            if self.embeddings is None:
                self.embeddings = np.array(embeddings)
            else:
                self.embeddings = np.vstack([self.embeddings, np.array(embeddings)])

            return True

        except Exception as e:
            print(f"警告: 索引文件失败 {file_path}: {e}")
            return False

    def save_index(self) -> bool:
        """保存索引到磁盘"""
        try:
            # 保存文档信息
            with open(self.index_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "documents": self.documents,
                    "count": len(self.documents),
                    "model": self.config.get("embedding_model", "unknown"),
                    "created_at": datetime.now().isoformat(),
                }, f, indent=2, ensure_ascii=False)

            # 保存向量矩阵
            if self.embeddings is not None and NUMPY_AVAILABLE:
                np.save(self.vectors_path, self.embeddings)

            print(f"✓ 索引已保存: {len(self.documents)} 个代码块")
            return True

        except Exception as e:
            print(f"✗ 保存索引失败: {e}")
            return False

    def load_index(self) -> bool:
        """从磁盘加载索引"""
        try:
            # 加载文档信息
            if not self.index_path.exists():
                return False

            with open(self.index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)

            self.documents = index_data.get("documents", [])

            # 加载向量矩阵
            if NUMPY_AVAILABLE and self.vectors_path.exists():
                self.embeddings = np.load(self.vectors_path)

            print(f"✓ 索引已加载: {len(self.documents)} 个代码块")
            return True

        except Exception as e:
            print(f"✗ 加载索引失败: {e}")
            return False

    def search(
        self,
        query: str,
        limit: int = 10,
        threshold: float = 0.7,
        language: Optional[str] = None,
    ) -> List[Dict]:
        """语义搜索"""
        if self.embeddings is None or len(self.documents) == 0:
            print("✗ 索引为空，请先建立索引")
            return []

        if not NUMPY_AVAILABLE:
            print("✗ 需要 numpy 进行向量搜索")
            return []

        try:
            # 生成查询向量
            query_embedding = list(self.embedding_model.embed([query]))[0]
            query_vector = np.array(query_embedding)

            # 计算余弦相似度
            similarities = self._cosine_similarity(query_vector, self.embeddings)

            # 添加相似度到文档
            results = []
            for doc, similarity in zip(self.documents, similarities):
                # 语言过滤
                if language and doc.get("language") != language:
                    continue

                # 相似度过滤
                if similarity < threshold:
                    continue

                result = doc.copy()
                result["similarity"] = float(similarity)
                results.append(result)

            # 按相似度排序
            results.sort(key=lambda x: x["similarity"], reverse=True)

            return results[:limit]

        except Exception as e:
            print(f"✗ 搜索失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> np.ndarray:
        """计算余弦相似度"""
        # 归一化
        vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-8)
        vec2_norm = vec2 / (np.linalg.norm(vec2, axis=1, keepdims=True) + 1e-8)

        # 点积
        return np.dot(vec2_norm, vec1_norm)

    def _generate_id(self, chunk: Dict) -> str:
        """生成唯一ID"""
        content = f"{chunk.get('file_path')}:{chunk.get('start_line')}:{chunk.get('name')}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def get_stats(self) -> Dict:
        """获取索引统计"""
        languages = {}
        for doc in self.documents:
            lang = doc.get("language", "unknown")
            languages[lang] = languages.get(lang, 0) + 1

        return {
            "total_chunks": len(self.documents),
            "languages": languages,
            "model": self.config.get("embedding_model", "unknown"),
        }

    def clear(self):
        """清空索引"""
        self.documents = []
        self.embeddings = None

        if self.index_path.exists():
            self.index_path.unlink()

        if self.vectors_path.exists():
            self.vectors_path.unlink()

        print("✓ 索引已清空")
