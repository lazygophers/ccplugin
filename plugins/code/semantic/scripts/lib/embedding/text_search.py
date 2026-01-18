#!/usr/bin/env python3
"""
纯文本搜索存储 - 作为 LanceDB 的替代方案

使用 BM25 关键词搜索和简单的相似度计算。
"""

from pathlib import Path
from typing import List, Dict, Optional
import json
import pickle
from collections import defaultdict
import math


class TextSearchStorage:
    """基于文本搜索的存储实现"""

    def __init__(self, config: Dict):
        self.config = config
        self.data_path = None
        self.storage_file = None
        self.index = {}  # 存储所有代码块
        self.word_index = defaultdict(list)  # 倒排索引

    def initialize(self, data_path: Path) -> bool:
        """初始化文本搜索存储"""
        try:
            self.data_path = data_path / "text_search"
            self.data_path.mkdir(parents=True, exist_ok=True)
            self.storage_file = self.data_path / "index.pkl"

            # 加载现有索引（如果存在）
            if self.storage_file.exists():
                with open(self.storage_file, "rb") as f:
                    self.index = pickle.load(f)
                print(f"✓ 加载现有索引: {len(self.index)} 个代码块")

            return True
        except Exception as e:
            print(f"错误: 文本搜索初始化失败: {e}")
            return False

    def insert(self, items: List[Dict]) -> bool:
        """插入数据到文本搜索"""
        if not items:
            return False

        try:
            for item in items:
                item_id = item.get("id", "")
                if not item_id:
                    continue

                # 存储整个项目
                self.index[item_id] = item

                # 建立倒排索引
                code = item.get("code", "")
                name = item.get("name", "")
                language = item.get("language", "")

                # 分词
                words = set()
                for text in [code, name, language]:
                    if text:
                        # 简单分词：去除非字母数字字符
                        words.update(self._tokenize(text))

                for word in words:
                    if item_id not in self.word_index[word]:
                        self.word_index[word].append(item_id)

            # 保存到文件
            self._save()
            return True
        except Exception as e:
            print(f"错误: 文本搜索插入失败: {e}")
            return False

    def search(
        self,
        query_vector: Optional[List[float]] = None,
        query_text: Optional[str] = None,
        limit: int = 10,
        filters: Optional[Dict] = None,
    ) -> List[Dict]:
        """执行文本搜索"""
        if not query_text or not self.index:
            return []

        try:
            # 分词查询
            query_words = self._tokenize(query_text)
            if not query_words:
                return []

            # BM25 评分
            scores = defaultdict(float)
            for word in query_words:
                if word in self.word_index:
                    for item_id in self.word_index[word]:
                        # 简单的 BM25-like 评分
                        doc = self.index[item_id]
                        text = (
                            doc.get("code", "") + " " + doc.get("name", "")
                        ).lower()
                        word_count = text.count(word.lower())
                        # IDF-like: 词越罕见，权重越高
                        idf = math.log(len(self.index) / len(self.word_index[word]))
                        scores[item_id] += word_count * idf

            # 排序结果
            sorted_items = sorted(
                scores.items(), key=lambda x: x[1], reverse=True
            )[:limit]

            # 格式化结果
            results = []
            for item_id, score in sorted_items:
                doc = self.index[item_id]
                result = {
                    "id": doc.get("id", ""),
                    "file_path": doc.get("file_path", ""),
                    "language": doc.get("language", ""),
                    "code_type": doc.get("code_type", ""),
                    "name": doc.get("name", ""),
                    "code": doc.get("code", ""),
                    "start_line": doc.get("start_line", 0),
                    "end_line": doc.get("end_line", 0),
                    "similarity": min(1.0, score / 10.0),  # 归一化相似度
                    "metadata": doc.get("metadata", {}),
                }
                results.append(result)

            return results
        except Exception as e:
            print(f"错误: 文本搜索失败: {e}")
            return []

    def create_vector_index(self, index_type: str = "IVF_PQ", wait: bool = True) -> bool:
        """创建索引（文本搜索不需要，直接返回成功）"""
        print("✓ 文本搜索已优化")
        return True

    def check_index_status(self) -> Dict:
        """检查索引状态"""
        return {
            "exists": len(self.index) > 0,
            "indices": [],
            "count": len(self.index),
        }

    def delete(self, filters: Dict) -> int:
        """删除数据"""
        if not filters:
            return 0

        try:
            deleted = 0
            file_path = filters.get("file_path", "")
            items_to_delete = [
                item_id
                for item_id, doc in self.index.items()
                if doc.get("file_path", "") == file_path
            ]

            for item_id in items_to_delete:
                del self.index[item_id]
                deleted += 1

            self._save()
            return deleted
        except Exception as e:
            print(f"错误: 文本搜索删除失败: {e}")
            return 0

    def count(self, filters: Optional[Dict] = None) -> int:
        """统计数据量"""
        return len(self.index)

    def close(self):
        """关闭存储"""
        self._save()

    def _tokenize(self, text: str) -> set:
        """简单分词"""
        if not text:
            return set()

        # 转换为小写
        text = text.lower()

        # 去除非字母数字字符
        words = []
        current_word = ""
        for char in text:
            if char.isalnum() or char in "-_":
                current_word += char
            else:
                if current_word and len(current_word) > 2:  # 忽略太短的词
                    words.append(current_word)
                current_word = ""

        if current_word and len(current_word) > 2:
            words.append(current_word)

        return set(words)

    def _save(self):
        """保存索引到文件"""
        try:
            if self.storage_file:
                with open(self.storage_file, "wb") as f:
                    pickle.dump(self.index, f)
        except Exception as e:
            print(f"警告: 无法保存文本搜索索引: {e}")


def create_storage(config: Dict) -> TextSearchStorage:
    """创建文本搜索存储后端"""
    return TextSearchStorage(config)
