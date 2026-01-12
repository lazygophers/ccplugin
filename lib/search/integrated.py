#!/usr/bin/env python3
"""
集成搜索器 - 整合向量搜索、关键词搜索和查询处理

提供统一的搜索接口，支持：
- 智能查询处理（规范化、扩展、意图识别）
- 向量搜索（语义相似性）
- 关键词搜索（BM25）
- 混合搜索（融合多种搜索结果）
"""

from typing import List, Dict, Optional
from pathlib import Path

from .query_processor import QueryProcessor, QueryIntent
from .hybrid import HybridSearcher, RankingStrategy
from .bm25 import BM25Searcher


class IntegratedSearcher:
    """集成搜索器

    提供完整的代码搜索功能，包括查询处理、向量搜索、关键词搜索和结果融合。
    """

    def __init__(
        self,
        vector_searcher=None,
        use_bm25: bool = True,
        hybrid_strategy: str = "rrf",
        vector_weight: float = 0.6,
        keyword_weight: float = 0.4,
    ):
        """
        初始化集成搜索器

        Args:
            vector_searcher: 向量搜索器（CodeIndexer）
            use_bm25: 是否启用 BM25 关键词搜索
            hybrid_strategy: 混合搜索策略（rrf、linear、multiplicative、max、min）
            vector_weight: 向量搜索权重
            keyword_weight: 关键词搜索权重
        """
        self.vector_searcher = vector_searcher
        self.use_bm25 = use_bm25
        self.hybrid_strategy = self._parse_strategy(hybrid_strategy)

        # 初始化查询处理器
        self.query_processor = QueryProcessor()

        # 初始化 BM25 搜索器
        self.bm25_searcher = BM25Searcher() if use_bm25 else None

        # 初始化混合搜索器
        self.hybrid_searcher = HybridSearcher(
            vector_searcher=vector_searcher,
            keyword_searcher=self.bm25_searcher,
            vector_weight=vector_weight,
            keyword_weight=keyword_weight,
        )

    def build_bm25_index(self, documents: List[Dict]):
        """构建 BM25 索引

        Args:
            documents: 文档列表，每个文档包含 "id", "text", "metadata"
        """
        if not self.bm25_searcher:
            return

        # 清空现有索引
        self.bm25_searcher.clear()

        # 添加文档到 BM25 索引
        for doc in documents:
            self.bm25_searcher.add_document(
                doc_id=doc.get("id", ""),
                text=doc.get("text", ""),
                metadata=doc.get("metadata", {}),
            )

    def search(
        self,
        query: str,
        limit: int = 10,
        language: Optional[str] = None,
        threshold: float = 0.0,
        use_hybrid: bool = True,
    ) -> List[Dict]:
        """执行搜索

        Args:
            query: 查询文本
            limit: 返回结果数量
            language: 限定编程语言
            threshold: 结果阈值
            use_hybrid: 是否使用混合搜索

        Returns:
            搜索结果列表
        """
        # 分析查询
        analysis = self.query_processor.analyze_query(query, language)

        # 获取查询意图
        intent = analysis.get("intent", QueryIntent.GENERAL_SEARCH)

        # 根据意图调整搜索策略
        if not use_hybrid or not self.bm25_searcher:
            # 仅使用向量搜索
            return self._vector_only_search(query, limit, language, threshold)

        # 使用混合搜索
        return self._hybrid_search(query, limit, language, threshold, intent)

    def search_with_expansion(
        self,
        query: str,
        limit: int = 10,
        language: Optional[str] = None,
        threshold: float = 0.0,
    ) -> List[Dict]:
        """使用查询扩展进行搜索

        Args:
            query: 查询文本
            limit: 返回结果数量
            language: 限定编程语言
            threshold: 结果阈值

        Returns:
            搜索结果列表
        """
        # 分析查询
        analysis = self.query_processor.analyze_query(query, language)

        # 生成扩展查询
        expanded_queries = analysis.get("expanded", [query])

        # 对每个扩展查询进行搜索
        all_results = {}  # id -> result

        for expanded_query in expanded_queries[:3]:  # 限制扩展查询数量
            results = self.search(
                expanded_query,
                limit=limit * 2,
                language=language,
                threshold=threshold,
                use_hybrid=True,
            )

            # 累积结果
            for result in results:
                doc_id = result.get("id", "")
                if doc_id not in all_results:
                    all_results[doc_id] = result
                else:
                    # 累积分数
                    all_results[doc_id]["score"] = (
                        all_results[doc_id].get("score", 0) +
                        result.get("score", 0)
                    ) / 2

        # 排序并返回
        final_results = sorted(
            all_results.values(),
            key=lambda x: x.get("score", 0),
            reverse=True,
        )

        return final_results[:limit]

    def _vector_only_search(
        self,
        query: str,
        limit: int,
        language: Optional[str],
        threshold: float,
    ) -> List[Dict]:
        """仅使用向量搜索

        Args:
            query: 查询文本
            limit: 返回结果数量
            language: 编程语言过滤
            threshold: 分数阈值

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
                threshold=threshold,
            )

            # 转换为标准格式
            standard_results = []
            for r in results:
                standard_results.append({
                    "id": r.get("id", ""),
                    "text": r.get("code", ""),
                    "file_path": r.get("file_path", ""),
                    "start_line": r.get("start_line", 0),
                    "end_line": r.get("end_line", 0),
                    "code_type": r.get("code_type", ""),
                    "name": r.get("name", ""),
                    "language": r.get("language", ""),
                    "metadata": {
                        k: v for k, v in r.items()
                        if k not in [
                            "id", "code", "file_path", "start_line",
                            "end_line", "code_type", "name", "language",
                        ]
                    },
                    "score": r.get("similarity", 0),
                    "score_type": "vector_similarity",
                })

            return standard_results
        except Exception as e:
            print(f"向量搜索失败: {e}")
            return []

    def _hybrid_search(
        self,
        query: str,
        limit: int,
        language: Optional[str],
        threshold: float,
        intent: QueryIntent,
    ) -> List[Dict]:
        """使用混合搜索

        Args:
            query: 查询文本
            limit: 返回结果数量
            language: 编程语言过滤
            threshold: 分数阈值
            intent: 查询意图

        Returns:
            搜索结果列表
        """
        try:
            # 执行混合搜索
            merged_results = self.hybrid_searcher.search(
                query=query,
                limit=limit,
                language=language,
                threshold=threshold,
                strategy=self.hybrid_strategy,
            )

            # 转换为标准格式
            standard_results = []
            for r in merged_results:
                metadata = r.get("metadata", {})
                standard_results.append({
                    "id": r.get("id", ""),
                    "text": r.get("text", ""),
                    "file_path": metadata.get("file_path", ""),
                    "start_line": metadata.get("start_line", 0),
                    "end_line": metadata.get("end_line", 0),
                    "code_type": metadata.get("code_type", ""),
                    "name": metadata.get("name", ""),
                    "language": metadata.get("language", ""),
                    "metadata": metadata,
                    "score": r.get("score", 0),
                    "score_type": "hybrid",
                    "vector_score": r.get("vector_score", 0),
                    "keyword_score": r.get("keyword_score", 0),
                })

            return standard_results
        except Exception as e:
            print(f"混合搜索失败: {e}")
            return []

    def get_query_analysis(self, query: str, language: Optional[str] = None) -> Dict:
        """获取查询分析结果

        Args:
            query: 查询文本
            language: 编程语言

        Returns:
            查询分析结果
        """
        return self.query_processor.analyze_query(query, language)

    def get_search_stats(self) -> Dict:
        """获取搜索统计信息

        Returns:
            统计信息
        """
        stats = {
            "vector_searcher": "available" if self.vector_searcher else "unavailable",
            "bm25_enabled": self.use_bm25,
            "hybrid_strategy": self.hybrid_strategy.value,
        }

        if self.bm25_searcher:
            stats["bm25_stats"] = self.bm25_searcher.get_stats()

        return stats

    def update_weights(self, vector_weight: float, keyword_weight: float):
        """更新搜索权重

        Args:
            vector_weight: 向量搜索权重
            keyword_weight: 关键词搜索权重
        """
        self.hybrid_searcher.set_weights(vector_weight, keyword_weight)

    def set_strategy(self, strategy: str):
        """设置混合搜索策略

        Args:
            strategy: 策略名称（rrf、linear、multiplicative、max、min）
        """
        self.hybrid_strategy = self._parse_strategy(strategy)

    def _parse_strategy(self, strategy: str) -> RankingStrategy:
        """解析策略字符串

        Args:
            strategy: 策略字符串

        Returns:
            策略枚举
        """
        strategy_lower = strategy.lower()

        if strategy_lower == "rrf":
            return RankingStrategy.RRF
        elif strategy_lower == "linear":
            return RankingStrategy.LINEAR
        elif strategy_lower == "multiplicative":
            return RankingStrategy.MULTIPLICATIVE
        elif strategy_lower == "max":
            return RankingStrategy.MAX
        elif strategy_lower == "min":
            return RankingStrategy.MIN
        else:
            return RankingStrategy.RRF  # 默认 RRF

    def close(self):
        """关闭搜索器"""
        if self.vector_searcher:
            self.vector_searcher.close()


__all__ = ["IntegratedSearcher"]
