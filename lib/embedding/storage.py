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
                self.table = self.client.create_table(
                    table_name,
                    schema=schema,
                    mode="overwrite",
                )

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
            # 获取预期的向量维度
            model_name = self.config.get("embedding_model", "bge-code-v1")
            expected_dim = self._get_model_dim(model_name)

            # 确保每个项目都有必需字段
            processed_items = []
            skipped_count = 0
            vector_stats = {"total": 0, "dims": set(), "invalid": 0}

            for item in items:
                vector = item.get("vector", [])
                if not vector:
                    # 跳过没有向量的项
                    skipped_count += 1
                    continue

                # 验证向量维度和类型
                if not isinstance(vector, (list, tuple)):
                    skipped_count += 1
                    continue

                actual_dim = len(vector)
                vector_stats["dims"].add(actual_dim)
                vector_stats["total"] += 1

                if actual_dim != expected_dim:
                    # 跳过维度不匹配的向量
                    skipped_count += 1
                    continue

                # 转换向量为列表（确保格式一致）
                vector_list = list(vector) if isinstance(vector, tuple) else vector

                # 验证所有元素都是有效的数字（非 NaN、无穷）
                try:
                    import math
                    valid_vector = []
                    for v in vector_list:
                        fv = float(v)
                        # 检查是否是 NaN 或无穷大
                        if math.isnan(fv) or math.isinf(fv):
                            vector_stats["invalid"] += 1
                            raise ValueError(f"无效的向量值: {fv}")
                        valid_vector.append(fv)
                    vector_list = valid_vector
                except (TypeError, ValueError) as e:
                    skipped_count += 1
                    continue

                processed_item = {
                    "id": item.get("id", ""),
                    "file_path": item.get("file_path", ""),
                    "language": item.get("language", ""),
                    "code_type": item.get("code_type", "block"),
                    "name": item.get("name", ""),
                    "code": item.get("code", ""),
                    "start_line": int(item.get("start_line", 0)),
                    "end_line": int(item.get("end_line", 0)),
                    "vector": vector_list,
                    "metadata": json.dumps(item.get("metadata", {}), ensure_ascii=False),
                    "indexed_at": item.get("indexed_at", ""),
                }
                processed_items.append(processed_item)

            if not processed_items:
                if skipped_count > 0:
                    print(f"警告: 所有项目都被跳过 (跳过 {skipped_count} 项)")
                    print(f"  向量统计: 总计 {vector_stats['total']}，维度 {vector_stats['dims']}，无效值 {vector_stats['invalid']}")
                return False

            # 调试信息
            dims_set = set()
            for item in processed_items:
                dims_set.add(len(item.get("vector", [])))
            if len(dims_set) > 1:
                print(f"警告: 处理后的项目中存在不同维度: {dims_set}")

            # 执行插入
            self.table.add(processed_items)
            return True
        except Exception as e:
            print(f"错误: LanceDB 插入失败: {e}")
            return False

    def create_vector_index(self, index_type: str = "IVF_PQ", wait: bool = True) -> bool:
        """创建 FAISS 向量索引

        Args:
            index_type: 索引类型，支持 "IVF_PQ"（默认）或 "HNSW"
            wait: 是否等待索引创建完成

        Returns:
            是否成功创建索引
        """
        if self.table is None:
            return False

        try:
            # 检查是否已存在索引
            existing_indices = self.table.list_indices()
            for idx in existing_indices:
                if idx.get("name", "") == "vector_idx":
                    print("索引已存在，跳过创建")
                    return True

            # 获取当前行数
            num_rows = self.table.count_rows()

            # 数据太少时不需要索引（FAISS 需要足够的数据训练）
            if num_rows < 1000:
                print(f"数据量较少 ({num_rows} 行)，跳过索引创建（建议 ≥1000 行）")
                return True

            print(f"正在创建 {index_type} 向量索引 ({num_rows} 行)...")

            # 创建索引
            try:
                # 尝试标准 API：create_index(column, index_type, metric)
                if index_type == "HNSW":
                    self.table.create_index(
                        column="vector",
                        index_type="HNSW",
                        metric="cosine"
                    )
                else:
                    self.table.create_index(
                        column="vector",
                        index_type="IVF_PQ",
                        metric="cosine"
                    )
            except (TypeError, ValueError):
                try:
                    # 尝试不指定 metric 的 API
                    if index_type == "HNSW":
                        self.table.create_index(
                            column="vector",
                            index_type="HNSW"
                        )
                    else:
                        self.table.create_index(
                            column="vector",
                            index_type="IVF_PQ"
                        )
                except (TypeError, ValueError):
                    # 尝试位置参数 API：create_index(column, metric, index_type)
                    try:
                        if index_type == "HNSW":
                            self.table.create_index("vector", "cosine", "HNSW")
                        else:
                            self.table.create_index("vector", "cosine", "IVF_PQ")
                    except (TypeError, ValueError):
                        # 最后的尝试：不指定任何可选参数
                        self.table.create_index("vector")

            print("✓ 向量索引创建完成")
            return True
        except Exception as e:
            print(f"错误: 索引创建失败: {e}")
            return False

    def check_index_status(self) -> Dict:
        """检查索引状态"""
        if self.table is None:
            return {"exists": False, "indices": []}

        try:
            indices = self.table.list_indices()
            return {
                "exists": len(indices) > 0,
                "indices": indices,
                "count": len(indices)
            }
        except Exception as e:
            print(f"错误: 检查索引状态失败: {e}")
            return {"exists": False, "indices": []}

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
                # LanceDB 返回的是距离（越小越好），需要转换为相似度（越大越好）
                distance = r.get("_distance", 1.0)

                # 根据距离类型转换相似度
                # 余弦距离: similarity = 1 - distance (范围 [0, 2])
                # L2 距离: similarity = 1 / (1 + distance) (范围 [0, +∞])
                if distance <= 2.0:
                    # 可能是余弦距离
                    similarity = max(0.0, 1.0 - distance)
                else:
                    # 可能是 L2 距离，使用反比例转换
                    similarity = 1.0 / (1.0 + distance)

                result = {
                    "id": r.get("id", ""),
                    "file_path": r.get("file_path", ""),
                    "language": r.get("language", ""),
                    "code_type": r.get("code_type", ""),
                    "name": r.get("name", ""),
                    "code": r.get("code", ""),
                    "start_line": r.get("start_line", 0),
                    "end_line": r.get("end_line", 0),
                    "similarity": similarity,
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
