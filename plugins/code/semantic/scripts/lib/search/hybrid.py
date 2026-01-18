#!/usr/bin/env python3
"""
混合搜索器 - 融合向量搜索和关键词搜索

支持：
- 向量搜索（语义相似性）
- 关键词搜索（BM25）
- 混合搜索（向量 + 关键词的加权融合）
- 结果重排序（RRF、线性组合等策略）
"""

import math
from typing import List, Dict, Optional, Tuple
from enum import Enum


class RankingStrategy(Enum):
    """排序策略"""
    RRF = "rrf"  # Reciprocal Rank Fusion
    LINEAR = "linear"  # 线性组合
    MULTIPLICATIVE = "multiplicative"  # 乘法组合
    MAX = "max"  # 取最大值
    MIN = "min"  # 取最小值


class HybridSearcher:
    """混合搜索器

    融合向量搜索和关键词搜索的结果，提高搜索准确率。
    """

    def __init__(
        self,
        vector_searcher=None,
        keyword_searcher=None,
        vector_weight: float = 0.6,
        keyword_weight: float = 0.4,
    ):
        """
        初始化混合搜索器

        Args:
            vector_searcher: 向量搜索器（如 CodeIndexer）
            keyword_searcher: 关键词搜索器（如 BM25Searcher）
            vector_weight: 向量搜索的权重（默认 0.6）
            keyword_weight: 关键词搜索的权重（默认 0.4）
        """
        self.vector_searcher = vector_searcher
        self.keyword_searcher = keyword_searcher
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight

        # 验证权重和为 1
        assert abs(
            self.vector_weight + self.keyword_weight - 1.0
        ) < 1e-6, "权重和必须为 1.0"

    def search(
        self,
        query: str,
        limit: int = 10,
        language: Optional[str] = None,
        threshold: float = 0.0,
        strategy: RankingStrategy = RankingStrategy.RRF,
    ) -> List[Dict]:
        """执行混合搜索

        Args:
            query: 查询文本
            limit: 返回结果数量
            language: 限定编程语言
            threshold: 结果相似度阈值
            strategy: 排序策略

        Returns:
            排序后的搜索结果列表
        """
        results_by_source = {}

        # 1. 向量搜索
        if self.vector_searcher:
            vector_results = self._vector_search(query, limit * 2, language)
            results_by_source["vector"] = vector_results
        else:
            vector_results = []

        # 2. 关键词搜索
        if self.keyword_searcher:
            keyword_results = self._keyword_search(query, limit * 2)
            results_by_source["keyword"] = keyword_results
        else:
            keyword_results = []

        # 3. 融合结果
        if not vector_results and not keyword_results:
            return []

        if strategy == RankingStrategy.RRF:
            merged = self._merge_rrf(
                vector_results,
                keyword_results,
                limit,
                threshold,
            )
        elif strategy == RankingStrategy.LINEAR:
            merged = self._merge_linear(
                vector_results,
                keyword_results,
                limit,
                threshold,
            )
        elif strategy == RankingStrategy.MULTIPLICATIVE:
            merged = self._merge_multiplicative(
                vector_results,
                keyword_results,
                limit,
                threshold,
            )
        elif strategy == RankingStrategy.MAX:
            merged = self._merge_max(
                vector_results,
                keyword_results,
                limit,
                threshold,
            )
        elif strategy == RankingStrategy.MIN:
            merged = self._merge_min(
                vector_results,
                keyword_results,
                limit,
                threshold,
            )
        else:
            merged = self._merge_linear(
                vector_results,
                keyword_results,
                limit,
                threshold,
            )

        return merged[:limit]

    def _vector_search(
        self,
        query: str,
        limit: int,
        language: Optional[str],
    ) -> List[Dict]:
        """执行向量搜索

        Args:
            query: 查询文本
            limit: 返回结果数量
            language: 编程语言过滤

        Returns:
            搜索结果列表
        """
        if not self.vector_searcher:
            return []

        try:
            results = self.vector_searcher.search(
                query=query,
                limit=limit,
                language=language,
            )

            # 规范化向量搜索结果
            normalized = []
            for r in results:
                normalized.append({
                    "id": r.get("id", ""),
                    "text": r.get("code", ""),
                    "metadata": {
                        k: v for k, v in r.items()
                        if k not in ["id", "code", "similarity"]
                    },
                    "source": "vector",
                    "original_score": r.get("similarity", 0),
                    "normalized_score": r.get("similarity", 0),  # 向量搜索的相似度已是 0-1
                })

            return normalized
        except Exception as e:
            print(f"向量搜索失败: {e}")
            return []

    def _keyword_search(
        self,
        query: str,
        limit: int,
    ) -> List[Dict]:
        """执行关键词搜索

        Args:
            query: 查询文本
            limit: 返回结果数量

        Returns:
            搜索结果列表
        """
        if not self.keyword_searcher:
            return []

        try:
            results = self.keyword_searcher.search(query, limit)

            # 规范化关键词搜索结果
            normalized = []
            for doc_id, score in results:
                doc = self.keyword_searcher.documents.get(doc_id, {})
                # 将 BM25 分数规范化到 0-1 范围
                normalized_score = self._normalize_score(
                    score,
                    results,
                )
                normalized.append({
                    "id": doc_id,
                    "text": doc.get("text", ""),
                    "metadata": doc.get("metadata", {}),
                    "source": "keyword",
                    "original_score": score,
                    "normalized_score": normalized_score,
                })

            return normalized
        except Exception as e:
            print(f"关键词搜索失败: {e}")
            return []

    def _normalize_score(
        self,
        score: float,
        all_scores: List[Tuple],
    ) -> float:
        """将 BM25 分数规范化到 0-1 范围

        Args:
            score: 原始分数
            all_scores: 所有分数列表

        Returns:
            规范化后的分数（0-1）
        """
        if not all_scores:
            return 0.0

        scores = [s[1] for s in all_scores]
        max_score = max(scores) if scores else 1.0

        if max_score == 0:
            return 0.0

        return min(1.0, score / max_score)

    def _merge_rrf(
        self,
        vector_results: List[Dict],
        keyword_results: List[Dict],
        limit: int,
        threshold: float,
    ) -> List[Dict]:
        """使用 RRF 策略融合结果

        RRF（Reciprocal Rank Fusion）是一个基于排序融合的方法。
        每个源中的每个结果被赋予倒数排名分数。

        Args:
            vector_results: 向量搜索结果
            keyword_results: 关键词搜索结果
            limit: 结果数量限制
            threshold: 分数阈值

        Returns:
            融合后的结果
        """
        # 为每个结果计算 RRF 分数
        merged = {}  # id -> {merged_result}

        # 处理向量搜索结果
        for rank, result in enumerate(vector_results, 1):
            doc_id = result["id"]
            rrf_score = 1.0 / (60 + rank)  # 标准 RRF 常数为 60

            if doc_id not in merged:
                merged[doc_id] = self._create_merged_result(result)

            merged[doc_id]["vector_rrf_score"] = rrf_score

        # 处理关键词搜索结果
        for rank, result in enumerate(keyword_results, 1):
            doc_id = result["id"]
            rrf_score = 1.0 / (60 + rank)

            if doc_id not in merged:
                merged[doc_id] = self._create_merged_result(result)

            merged[doc_id]["keyword_rrf_score"] = rrf_score

        # 计算最终分数
        final_results = []
        for doc_id, result in merged.items():
            vector_rrf = result.get("vector_rrf_score", 0)
            keyword_rrf = result.get("keyword_rrf_score", 0)

            # 加权融合
            final_score = (
                self.vector_weight * vector_rrf +
                self.keyword_weight * keyword_rrf
            )

            if final_score >= threshold:
                result["score"] = final_score
                result["vector_score"] = result.get("vector_rrf_score", 0)
                result["keyword_score"] = result.get("keyword_rrf_score", 0)
                final_results.append(result)

        # 按最终分数排序
        final_results.sort(key=lambda x: x["score"], reverse=True)
        return final_results[:limit]

    def _merge_linear(
        self,
        vector_results: List[Dict],
        keyword_results: List[Dict],
        limit: int,
        threshold: float,
    ) -> List[Dict]:
        """使用线性组合策略融合结果

        Args:
            vector_results: 向量搜索结果
            keyword_results: 关键词搜索结果
            limit: 结果数量限制
            threshold: 分数阈值

        Returns:
            融合后的结果
        """
        merged = {}  # id -> {merged_result}

        # 处理向量搜索结果
        for result in vector_results:
            doc_id = result["id"]
            if doc_id not in merged:
                merged[doc_id] = self._create_merged_result(result)
            merged[doc_id]["vector_score"] = result.get("normalized_score", 0)

        # 处理关键词搜索结果
        for result in keyword_results:
            doc_id = result["id"]
            if doc_id not in merged:
                merged[doc_id] = self._create_merged_result(result)
            merged[doc_id]["keyword_score"] = result.get("normalized_score", 0)

        # 计算最终分数
        final_results = []
        for doc_id, result in merged.items():
            vector_score = result.get("vector_score", 0)
            keyword_score = result.get("keyword_score", 0)

            # 线性组合
            final_score = (
                self.vector_weight * vector_score +
                self.keyword_weight * keyword_score
            )

            if final_score >= threshold:
                result["score"] = final_score
                final_results.append(result)

        # 按最终分数排序
        final_results.sort(key=lambda x: x["score"], reverse=True)
        return final_results[:limit]

    def _merge_multiplicative(
        self,
        vector_results: List[Dict],
        keyword_results: List[Dict],
        limit: int,
        threshold: float,
    ) -> List[Dict]:
        """使用乘法组合策略融合结果

        Args:
            vector_results: 向量搜索结果
            keyword_results: 关键词搜索结果
            limit: 结果数量限制
            threshold: 分数阈值

        Returns:
            融合后的结果
        """
        merged = {}  # id -> {merged_result}

        # 处理向量搜索结果
        for result in vector_results:
            doc_id = result["id"]
            if doc_id not in merged:
                merged[doc_id] = self._create_merged_result(result)
            merged[doc_id]["vector_score"] = result.get("normalized_score", 0)

        # 处理关键词搜索结果
        for result in keyword_results:
            doc_id = result["id"]
            if doc_id not in merged:
                merged[doc_id] = self._create_merged_result(result)
            merged[doc_id]["keyword_score"] = result.get("normalized_score", 0)

        # 计算最终分数
        final_results = []
        for doc_id, result in merged.items():
            vector_score = result.get("vector_score", 0)
            keyword_score = result.get("keyword_score", 0)

            # 乘法组合
            if vector_score > 0 and keyword_score > 0:
                final_score = math.sqrt(vector_score * keyword_score)
            else:
                # 如果其中一个为 0，只使用不为 0 的那个
                final_score = max(vector_score, keyword_score)

            if final_score >= threshold:
                result["score"] = final_score
                result["vector_score"] = vector_score
                result["keyword_score"] = keyword_score
                final_results.append(result)

        # 按最终分数排序
        final_results.sort(key=lambda x: x["score"], reverse=True)
        return final_results[:limit]

    def _merge_max(
        self,
        vector_results: List[Dict],
        keyword_results: List[Dict],
        limit: int,
        threshold: float,
    ) -> List[Dict]:
        """使用最大值策略融合结果

        Args:
            vector_results: 向量搜索结果
            keyword_results: 关键词搜索结果
            limit: 结果数量限制
            threshold: 分数阈值

        Returns:
            融合后的结果
        """
        merged = {}  # id -> {merged_result}

        # 处理向量搜索结果
        for result in vector_results:
            doc_id = result["id"]
            if doc_id not in merged:
                merged[doc_id] = self._create_merged_result(result)
            merged[doc_id]["vector_score"] = result.get("normalized_score", 0)

        # 处理关键词搜索结果
        for result in keyword_results:
            doc_id = result["id"]
            if doc_id not in merged:
                merged[doc_id] = self._create_merged_result(result)
            merged[doc_id]["keyword_score"] = result.get("normalized_score", 0)

        # 计算最终分数
        final_results = []
        for doc_id, result in merged.items():
            vector_score = result.get("vector_score", 0)
            keyword_score = result.get("keyword_score", 0)

            # 取最大值
            final_score = max(vector_score, keyword_score)

            if final_score >= threshold:
                result["score"] = final_score
                result["vector_score"] = vector_score
                result["keyword_score"] = keyword_score
                final_results.append(result)

        # 按最终分数排序
        final_results.sort(key=lambda x: x["score"], reverse=True)
        return final_results[:limit]

    def _merge_min(
        self,
        vector_results: List[Dict],
        keyword_results: List[Dict],
        limit: int,
        threshold: float,
    ) -> List[Dict]:
        """使用最小值策略融合结果

        Args:
            vector_results: 向量搜索结果
            keyword_results: 关键词搜索结果
            limit: 结果数量限制
            threshold: 分数阈值

        Returns:
            融合后的结果
        """
        merged = {}  # id -> {merged_result}

        # 处理向量搜索结果
        for result in vector_results:
            doc_id = result["id"]
            if doc_id not in merged:
                merged[doc_id] = self._create_merged_result(result)
            merged[doc_id]["vector_score"] = result.get("normalized_score", 0)

        # 处理关键词搜索结果
        for result in keyword_results:
            doc_id = result["id"]
            if doc_id not in merged:
                merged[doc_id] = self._create_merged_result(result)
            merged[doc_id]["keyword_score"] = result.get("normalized_score", 0)

        # 计算最终分数
        final_results = []
        for doc_id, result in merged.items():
            vector_score = result.get("vector_score", 0)
            keyword_score = result.get("keyword_score", 0)

            # 只保留同时出现在两个搜索中的结果
            if vector_score > 0 and keyword_score > 0:
                final_score = min(vector_score, keyword_score)
                result["score"] = final_score
                result["vector_score"] = vector_score
                result["keyword_score"] = keyword_score
                final_results.append(result)

        # 按最终分数排序
        final_results.sort(key=lambda x: x["score"], reverse=True)
        return final_results[:limit]

    def _create_merged_result(self, source_result: Dict) -> Dict:
        """创建融合结果对象

        Args:
            source_result: 源搜索结果

        Returns:
            融合结果对象
        """
        return {
            "id": source_result.get("id", ""),
            "text": source_result.get("text", ""),
            "metadata": source_result.get("metadata", {}),
            "sources": [source_result.get("source", "")],
        }

    def set_weights(self, vector_weight: float, keyword_weight: float):
        """设置搜索权重

        Args:
            vector_weight: 向量搜索权重
            keyword_weight: 关键词搜索权重
        """
        assert abs(vector_weight + keyword_weight - 1.0) < 1e-6
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight


__all__ = [
    "HybridSearcher",
    "RankingStrategy",
]
