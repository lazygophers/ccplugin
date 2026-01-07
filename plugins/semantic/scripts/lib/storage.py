#!/usr/bin/env python3
"""
存储层 - LanceDB 向量存储接口

提供向量存储和检索功能。
"""

from pathlib import Path
from typing import List, Dict, Optional
import json


class LanceDBStorage:
    """LanceDB 存储实现 - 向量索引"""

    def __init__(self, config: Dict):
        self.config = config
        self.client = None
        self.table = None
        self.db_path = None

    def initialize(self, data_path: Path) -> bool:
        """初始化 LanceDB"""
        try:
            import lancedb
            import pyarrow as pa

            self.db_path = data_path / "lancedb"
            self.db_path.mkdir(parents=True, exist_ok=True)

            self.client = lancedb.connect(str(self.db_path))

            # 获取模型维度
            model_name = self.config.get("embedding_model", "bge-code-v1")
            dim = self._get_model_dim(model_name)

            # 创建或打开表
            table_name = "code_index"
            try:
                self.table = self.client.open_table(table_name)
            except Exception:
                # 表不存在，创建新表 - 使用 pyarrow.Schema
                schema = pa.schema([
                    pa.field("id", pa.string()),
                    pa.field("file_path", pa.string()),
                    pa.field("language", pa.string()),
                    pa.field("code_type", pa.string()),  # function, class, block, etc.
                    pa.field("name", pa.string()),  # 函数名/类名
                    pa.field("code", pa.string()),
                    pa.field("start_line", pa.int32()),
                    pa.field("end_line", pa.int32()),
                    pa.field("vector", pa.list_(pa.float32(), list_size=dim)),
                    pa.field("metadata", pa.string()),  # JSON 字符串
                    pa.field("indexed_at", pa.string()),
                ])
                self.table = self.client.create_table(table_name, schema=schema)

            return True
        except ImportError:
            print("错误: 未安装 lancedb 或 pyarrow，运行: uv pip install lancedb pyarrow")
            return False
        except Exception as e:
            print(f"错误: LanceDB 初始化失败: {e}")
            return False

    def _get_model_dim(self, model_name: str) -> int:
        """获取模型维度"""
        # FastEmbed 模型维度映射
        model_dims = {
            # BGE 系列
            "bge-small-en": 384,
            "bge-small-zh": 512,
            "bge-base-en": 768,
            "bge-large-en": 1024,
            "bge-code-v1": 768,
            # Jina 系列
            "jina-small-en": 512,
            "jina-base-en": 768,
            "jina-code": 768,
            "jina-v2-code": 768,
            "jina-v2-small": 512,
            # Arctic 系列
            "arctic-embed-xs": 384,
            "arctic-embed-s": 384,
            "arctic-embed-m": 768,
            "arctic-embed-l": 1024,
            # 其他高质量模型
            "gte-large": 1024,
            "mxbai-embed-large": 1024,
            "multilingual-e5-small": 384,
            "multilingual-e5-large": 1024,
            "nomic-embed-text-1.5": 768,
            "all-minilm-l6-v2": 384,
            "default": 384,
        }
        return model_dims.get(model_name, 768)

    def insert(self, items: List[Dict]) -> bool:
        """插入数据到 LanceDB"""
        if self.table is None:
            return False

        try:
            # 确保每个项目都有必需字段
            processed_items = []
            for item in items:
                vector = item.get("vector", [])
                if not vector:
                    # 跳过没有向量的项
                    continue

                processed_item = {
                    "id": item.get("id", ""),
                    "file_path": item.get("file_path", ""),
                    "language": item.get("language", ""),
                    "code_type": item.get("code_type", "block"),
                    "name": item.get("name", ""),
                    "code": item.get("code", ""),
                    "start_line": item.get("start_line", 0),
                    "end_line": item.get("end_line", 0),
                    "vector": vector,
                    "metadata": json.dumps(item.get("metadata", {}), ensure_ascii=False),
                    "indexed_at": item.get("indexed_at", ""),
                }
                processed_items.append(processed_item)

            if not processed_items:
                return False

            # 执行插入
            self.table.add(processed_items)
            return True
        except Exception as e:
            print(f"错误: LanceDB 插入失败: {e}")
            return False

    def search(
        self,
        query_vector: Optional[List[float]] = None,
        query_text: Optional[str] = None,
        limit: int = 10,
        filters: Optional[Dict] = None,
    ) -> List[Dict]:
        """在 LanceDB 中搜索"""
        if self.table is None or not query_vector:
            return []

        try:
            # 构建查询
            results = self.table.search(query_vector).limit(limit)

            # 应用过滤
            if filters:
                where_clause = self._build_where_clause(filters)
                if where_clause:
                    results = results.where(where_clause)

            # 执行搜索
            search_results = results.to_list()

            # 格式化结果
            formatted_results = []
            for r in search_results:
                result = {
                    "id": r.get("id", ""),
                    "file_path": r.get("file_path", ""),
                    "language": r.get("language", ""),
                    "code_type": r.get("code_type", ""),
                    "name": r.get("name", ""),
                    "code": r.get("code", ""),
                    "start_line": r.get("start_line", 0),
                    "end_line": r.get("end_line", 0),
                    "similarity": r.get("_score", 0.0),
                    "metadata": json.loads(r.get("metadata", "{}")),
                }
                formatted_results.append(result)

            return formatted_results
        except Exception as e:
            print(f"错误: LanceDB 搜索失败: {e}")
            return []

    def _build_where_clause(self, filters: Dict) -> str:
        """构建 WHERE 子句"""
        conditions = []
        for key, value in filters.items():
            if isinstance(value, str):
                conditions.append(f"{key} = '{value}'")
            elif isinstance(value, list):
                values = ",".join(f"'{v}'" for v in value)
                conditions.append(f"{key} IN ({values})")
            else:
                conditions.append(f"{key} = {value}")
        return " AND ".join(conditions) if conditions else ""

    def delete(self, filters: Dict) -> int:
        """从 LanceDB 删除数据"""
        if self.table is None:
            return 0

        try:
            where_clause = self._build_where_clause(filters)
            if not where_clause:
                return 0

            self.table.delete(where_clause)
            return 1  # LanceDB 不返回删除计数
        except Exception as e:
            print(f"错误: LanceDB 删除失败: {e}")
            return 0

    def count(self, filters: Optional[Dict] = None) -> int:
        """统计 LanceDB 中的数据量"""
        if self.table is None:
            return 0

        try:
            if not filters:
                return self.table.count_rows()
            return 0
        except Exception as e:
            print(f"错误: LanceDB 统计失败: {e}")
            return 0

    def close(self):
        """关闭 LanceDB 连接"""
        # LanceDB 连接不需要显式关闭
        self.client = None
        self.table = None


def create_storage(config: Dict) -> LanceDBStorage:
    """创建存储后端（LanceDB）"""
    return LanceDBStorage(config)
