#!/usr/bin/env python3
"""
BM25 关键词搜索器 - 实现经典的 BM25 信息检索算法

支持：
- BM25 排序函数（文本相关性评分）
- 关键词提取和规范化
- 索引构建和更新
"""

import math
import re
from typing import List, Dict, Optional, Set, Tuple
from collections import defaultdict
import json


class BM25Searcher:
    """BM25 关键词搜索器

    使用 BM25 算法对代码块进行关键词搜索和排序。
    BM25 是一个经验性的相关性框架，常用于信息检索。
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        初始化 BM25 搜索器

        Args:
            k1: 控制非线性项频率饱和点的参数（默认 1.5）
            b: 控制文档长度归一化的参数（默认 0.75）
        """
        self.k1 = k1
        self.b = b

        # 索引数据
        self.documents: Dict[str, Dict] = {}  # id -> 文档内容
        self.inverted_index: Dict[str, Set[str]] = defaultdict(set)  # term -> {doc_ids}
        self.tf: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))  # doc_id -> {term -> count}
        self.doc_length: Dict[str, int] = {}  # doc_id -> length
        self.avg_doc_length = 0
        self.total_docs = 0

    def add_document(self, doc_id: str, text: str, metadata: Optional[Dict] = None):
        """添加文档到索引

        Args:
            doc_id: 文档 ID
            text: 文档文本内容
            metadata: 文档元数据
        """
        # 存储文档
        self.documents[doc_id] = {
            "text": text,
            "metadata": metadata or {},
        }

        # 分词
        tokens = self._tokenize(text)

        # 更新 TF（词频）
        for token in tokens:
            self.tf[doc_id][token] += 1

        # 更新倒排索引
        for token in set(tokens):
            self.inverted_index[token].add(doc_id)

        # 记录文档长度
        self.doc_length[doc_id] = len(tokens)

        # 更新总文档数和平均长度
        self._update_stats()

    def add_documents_batch(self, documents: List[Dict]):
        """批量添加文档

        Args:
            documents: 文档列表，每个文档包含 "id", "text", "metadata"
        """
        for doc in documents:
            self.add_document(doc["id"], doc["text"], doc.get("metadata"))

    def remove_document(self, doc_id: str):
        """移除文档

        Args:
            doc_id: 文档 ID
        """
        if doc_id not in self.documents:
            return

        # 获取文档的词汇
        tokens = set(self.tf[doc_id].keys())

        # 从倒排索引中移除
        for token in tokens:
            self.inverted_index[token].discard(doc_id)

        # 清理空的倒排索引项
        self.inverted_index = {
            k: v for k, v in self.inverted_index.items() if v
        }

        # 删除文档数据
        del self.documents[doc_id]
        del self.tf[doc_id]
        del self.doc_length[doc_id]

        # 更新统计
        self._update_stats()

    def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict] = None,
    ) -> List[Tuple[str, float]]:
        """搜索文档

        Args:
            query: 查询文本
            limit: 返回结果数量
            filters: 过滤条件

        Returns:
            [(doc_id, score), ...] 列表，按相关性排序
        """
        if not self.documents:
            return []

        # 分词查询
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        # 计算 BM25 分数
        scores: Dict[str, float] = defaultdict(float)

        for token in query_tokens:
            # 获取包含该词的文档
            docs_with_token = self.inverted_index.get(token, set())

            if not docs_with_token:
                continue

            # 计算 IDF（逆文档频率）
            idf = self._calculate_idf(len(docs_with_token))

            # 为每个文档计算 BM25 分数
            for doc_id in docs_with_token:
                # 检查过滤条件
                if filters and not self._match_filters(doc_id, filters):
                    continue

                # 获取词频
                tf = self.tf[doc_id].get(token, 0)

                # 计算 BM25 分数
                score = self._calculate_bm25_score(tf, idf, doc_id)
                scores[doc_id] += score

        # 排序并返回结果
        results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return results[:limit]

    def search_with_context(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict] = None,
    ) -> List[Dict]:
        """搜索文档并返回完整结果

        Args:
            query: 查询文本
            limit: 返回结果数量
            filters: 过滤条件

        Returns:
            包含文档内容和分数的结果列表
        """
        results = self.search(query, limit, filters)

        # 添加完整文档信息
        full_results = []
        for doc_id, score in results:
            doc = self.documents.get(doc_id)
            if doc:
                full_results.append({
                    "id": doc_id,
                    "text": doc["text"],
                    "metadata": doc.get("metadata", {}),
                    "score": score,
                })

        return full_results

    def _tokenize(self, text: str) -> List[str]:
        """分词

        Args:
            text: 文本内容

        Returns:
            词汇列表
        """
        # 转换为小写
        text = text.lower()

        # 移除特殊字符，保留字母、数字和下划线
        text = re.sub(r'[^a-z0-9_\s]', ' ', text)

        # 分词
        tokens = text.split()

        # 移除停用词和短词
        stopwords = {
            "the", "a", "an", "and", "or", "in", "on", "at", "to", "for",
            "of", "with", "by", "is", "are", "am", "be", "been", "being",
            "have", "has", "do", "does", "did", "will", "would", "could",
            "should", "can", "may", "might", "must", "shall", "was", "were",
        }

        tokens = [
            t for t in tokens
            if len(t) > 2 and t not in stopwords
        ]

        return tokens

    def _calculate_idf(self, doc_count: int) -> float:
        """计算 IDF（逆文档频率）

        Args:
            doc_count: 包含该词的文档数

        Returns:
            IDF 值
        """
        if self.total_docs == 0:
            return 0

        return math.log((self.total_docs - doc_count + 0.5) / (doc_count + 0.5) + 1.0)

    def _calculate_bm25_score(
        self,
        tf: int,
        idf: float,
        doc_id: str,
    ) -> float:
        """计算 BM25 分数

        Args:
            tf: 词在文档中的出现次数
            idf: 词的 IDF 值
            doc_id: 文档 ID

        Returns:
            BM25 分数
        """
        doc_len = self.doc_length.get(doc_id, 0)

        if self.avg_doc_length == 0:
            return 0

        # BM25 公式
        numerator = tf * (self.k1 + 1)
        denominator = (
            tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_length)
        )

        return idf * (numerator / denominator)

    def _update_stats(self):
        """更新统计信息"""
        self.total_docs = len(self.documents)

        if self.total_docs > 0:
            total_length = sum(self.doc_length.values())
            self.avg_doc_length = total_length / self.total_docs
        else:
            self.avg_doc_length = 0

    def _match_filters(self, doc_id: str, filters: Dict) -> bool:
        """检查文档是否匹配过滤条件

        Args:
            doc_id: 文档 ID
            filters: 过滤条件

        Returns:
            是否匹配
        """
        doc = self.documents.get(doc_id)
        if not doc:
            return False

        metadata = doc.get("metadata", {})

        for key, value in filters.items():
            if isinstance(value, (list, set)):
                if metadata.get(key) not in value:
                    return False
            else:
                if metadata.get(key) != value:
                    return False

        return True

    def get_stats(self) -> Dict:
        """获取索引统计信息

        Returns:
            包含统计信息的字典
        """
        return {
            "total_documents": self.total_docs,
            "total_terms": len(self.inverted_index),
            "average_doc_length": self.avg_doc_length,
            "k1": self.k1,
            "b": self.b,
        }

    def save(self, path: str):
        """保存索引到文件

        Args:
            path: 保存路径
        """
        import pickle

        data = {
            "documents": self.documents,
            "inverted_index": dict(self.inverted_index),
            "tf": dict(self.tf),
            "doc_length": self.doc_length,
            "avg_doc_length": self.avg_doc_length,
            "total_docs": self.total_docs,
            "k1": self.k1,
            "b": self.b,
        }

        with open(path, "wb") as f:
            pickle.dump(data, f)

    def load(self, path: str):
        """从文件加载索引

        Args:
            path: 加载路径
        """
        import pickle

        with open(path, "rb") as f:
            data = pickle.load(f)

        self.documents = data["documents"]
        self.inverted_index = defaultdict(set, data["inverted_index"])
        self.tf = defaultdict(lambda: defaultdict(int), data["tf"])
        self.doc_length = data["doc_length"]
        self.avg_doc_length = data["avg_doc_length"]
        self.total_docs = data["total_docs"]
        self.k1 = data["k1"]
        self.b = data["b"]

    def clear(self):
        """清空索引"""
        self.documents.clear()
        self.inverted_index.clear()
        self.tf.clear()
        self.doc_length.clear()
        self.avg_doc_length = 0
        self.total_docs = 0


__all__ = ["BM25Searcher"]
