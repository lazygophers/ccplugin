#!/usr/bin/env python3
"""
查询处理器 - 智能查询分析和优化

支持查询规范化、查询扩展、意图识别等功能，提高搜索准确率。
"""

import re
from typing import List, Dict, Optional, Tuple
from enum import Enum


class QueryIntent(Enum):
    """查询意图类型"""
    FIND_DEFINITION = "find_definition"  # 查找定义
    FIND_USAGE = "find_usage"  # 查找使用
    FIND_IMPLEMENTATION = "find_implementation"  # 查找实现
    FIND_SIMILAR = "find_similar"  # 查找类似代码
    GENERAL_SEARCH = "general_search"  # 一般搜索


class QueryProcessor:
    """查询处理器"""

    # 同义词映射
    SYNONYMS = {
        "func": ["function", "method", "def"],
        "function": ["func", "method", "def"],
        "class": ["struct", "type", "class"],
        "method": ["function", "func", "procedure"],
        "var": ["variable", "var", "name"],
        "const": ["constant", "const", "literal"],
        "import": ["include", "import", "require"],
        "export": ["export", "public", "expose"],
        "async": ["asynchronous", "promise", "callback"],
        "error": ["exception", "error", "fail"],
        "result": ["return", "output", "result"],
    }

    # 缩写映射
    ABBREVIATIONS = {
        "fn": "function",
        "func": "function",
        "def": "definition",
        "impl": "implementation",
        "decl": "declaration",
        "ref": "reference",
        "param": "parameter",
        "arg": "argument",
        "ret": "return",
        "err": "error",
        "exc": "exception",
        "init": "initialize",
        "del": "delete",
        "prop": "property",
        "attr": "attribute",
    }

    # 代码相关的关键词
    CODE_KEYWORDS = {
        "algorithm": "algo",
        "authentication": "auth",
        "authorization": "authz",
        "configuration": "config",
        "database": "db",
        "dependency": "dep",
        "documentation": "doc",
        "exception": "error",
        "generate": "gen",
        "implementation": "impl",
        "initialize": "init",
        "interface": "iface",
        "parameter": "param",
        "performance": "perf",
        "reference": "ref",
        "security": "sec",
        "serialize": "serialize",
        "structure": "struct",
        "template": "tmpl",
        "transaction": "tx",
        "utility": "util",
        "validation": "validate",
    }

    def __init__(self):
        """初始化查询处理器"""
        self.language_specific_keywords = {
            "python": ["def", "class", "async", "await", "lambda"],
            "javascript": ["function", "class", "async", "await", "const"],
            "typescript": ["function", "class", "async", "await", "interface"],
            "go": ["func", "type", "interface", "struct", "defer"],
            "rust": ["fn", "struct", "enum", "trait", "impl"],
            "java": ["class", "interface", "method", "final", "static"],
        }

    def normalize_query(self, query: str) -> str:
        """规范化查询"""
        # 转换为小写
        normalized = query.lower().strip()

        # 移除多余空格
        normalized = re.sub(r'\s+', ' ', normalized)

        # 移除特殊字符（保留字母、数字、空格、下划线）
        normalized = re.sub(r'[^\w\s]', '', normalized)

        return normalized

    def detect_intent(self, query: str) -> QueryIntent:
        """检测查询意图"""
        query_lower = query.lower()

        # 查找定义的关键词
        if any(keyword in query_lower for keyword in ["define", "definition", "def", "declare"]):
            return QueryIntent.FIND_DEFINITION

        # 查找使用的关键词
        if any(keyword in query_lower for keyword in ["usage", "use", "usage", "call", "reference"]):
            return QueryIntent.FIND_USAGE

        # 查找实现的关键词
        if any(keyword in query_lower for keyword in ["implement", "implementation", "impl", "code"]):
            return QueryIntent.FIND_IMPLEMENTATION

        # 查找类似代码的关键词
        if any(keyword in query_lower for keyword in ["similar", "like", "example", "sample"]):
            return QueryIntent.FIND_SIMILAR

        # 默认为一般搜索
        return QueryIntent.GENERAL_SEARCH

    def detect_symbol_type(self, query: str) -> Optional[str]:
        """检测目标符号类型"""
        query_lower = query.lower()

        if any(keyword in query_lower for keyword in ["function", "func", "fn", "method"]):
            return "function"
        elif any(keyword in query_lower for keyword in ["class", "struct", "type"]):
            return "class"
        elif any(keyword in query_lower for keyword in ["interface", "protocol", "trait"]):
            return "interface"
        elif any(keyword in query_lower for keyword in ["variable", "var", "const", "constant"]):
            return "variable"
        elif any(keyword in query_lower for keyword in ["enum", "enumeration"]):
            return "enum"

        return None

    def expand_query(self, query: str) -> List[str]:
        """查询扩展

        返回原始查询加上各种扩展变体
        """
        expanded = [query]

        # 扩展缩写
        for abbrev, full in self.ABBREVIATIONS.items():
            if abbrev in query.lower():
                expanded.append(query.lower().replace(abbrev, full))

        # 扩展同义词
        words = query.lower().split()
        for word in words:
            if word in self.SYNONYMS:
                for synonym in self.SYNONYMS[word]:
                    expanded.append(query.lower().replace(word, synonym))

        # 移除重复
        expanded = list(set(expanded))

        return expanded

    def extract_keywords(self, query: str) -> List[str]:
        """提取关键词"""
        words = query.lower().split()

        # 移除停用词
        stopwords = {"the", "a", "an", "and", "or", "in", "on", "at", "to", "for"}
        keywords = [w for w in words if w not in stopwords and len(w) > 2]

        return keywords

    def rewrite_query(self, query: str, language: Optional[str] = None) -> str:
        """查询重写

        针对特定语言和上下文优化查询
        """
        # 先规范化
        rewritten = self.normalize_query(query)

        # 如果指定了语言，添加语言相关的上下文
        if language and language.lower() in self.language_specific_keywords:
            keywords = self.language_specific_keywords[language.lower()]
            # 添加语言特定关键词到查询
            rewritten = f"{rewritten} {language.lower()}"

        # 替换代码相关术语
        for long_form, short_form in self.CODE_KEYWORDS.items():
            if short_form in rewritten:
                rewritten = rewritten.replace(short_form, long_form)

        return rewritten

    def analyze_query(self, query: str, language: Optional[str] = None) -> Dict:
        """完整的查询分析"""
        analysis = {
            "original": query,
            "normalized": self.normalize_query(query),
            "intent": self.detect_intent(query),
            "symbol_type": self.detect_symbol_type(query),
            "keywords": self.extract_keywords(query),
            "expanded": self.expand_query(query),
            "rewritten": self.rewrite_query(query, language),
        }

        return analysis

    def generate_search_queries(self, query: str, language: Optional[str] = None) -> List[str]:
        """生成多个搜索查询

        用于混合搜索
        """
        queries = []

        # 原始查询
        queries.append(query)

        # 规范化查询
        normalized = self.normalize_query(query)
        if normalized != query:
            queries.append(normalized)

        # 扩展查询
        for expanded in self.expand_query(query):
            if expanded not in queries:
                queries.append(expanded)

        # 重写查询
        rewritten = self.rewrite_query(query, language)
        if rewritten != query and rewritten not in queries:
            queries.append(rewritten)

        # 关键词组合
        keywords = self.extract_keywords(query)
        if len(keywords) > 1:
            keyword_query = " ".join(keywords)
            if keyword_query not in queries:
                queries.append(keyword_query)

        return queries[:5]  # 返回最多 5 个查询


class SemanticQueryEnhancer:
    """语义查询增强器"""

    def __init__(self):
        """初始化增强器"""
        self.processor = QueryProcessor()

    def enhance_with_metadata(self, query: str, metadata: Dict) -> Dict:
        """使用元数据增强查询"""
        enhanced = {
            "query": query,
            "analysis": self.processor.analyze_query(query),
            "boost_factors": {},
        }

        # 根据元数据调整提升因子
        intent = enhanced["analysis"]["intent"]

        if intent == QueryIntent.FIND_DEFINITION:
            # 提升函数和类定义
            enhanced["boost_factors"]["code_type"] = {
                "function": 1.5,
                "class": 1.5,
                "definition": 2.0,
            }
        elif intent == QueryIntent.FIND_USAGE:
            # 提升被引用的代码
            enhanced["boost_factors"]["is_referenced"] = 1.3

        # 提升文档更全的代码
        enhanced["boost_factors"]["has_docstring"] = 1.2

        return enhanced

    def create_multi_field_query(self, query: str) -> Dict:
        """创建多字段查询"""
        keywords = self.processor.extract_keywords(query)

        return {
            "name": {
                "query": query,
                "boost": 2.0,
            },
            "code": {
                "query": query,
                "boost": 1.0,
            },
            "keywords": {
                "query": " ".join(keywords),
                "boost": 1.5,
            },
            "docstring": {
                "query": query,
                "boost": 1.3,
            },
        }


# 导出
__all__ = [
    "QueryProcessor",
    "QueryIntent",
    "SemanticQueryEnhancer",
]
