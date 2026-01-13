#!/usr/bin/env python3
"""
代码索引器 - 整合代码解析、嵌入生成和存储

扫描项目代码，生成向量嵌入，存储到数据库。
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Set
from datetime import datetime
import pathspec

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.text import Text

from lib.embedding.storage import create_storage
from lib.embedding import EmbeddingGenerator, generate_code_id, truncate_code
from lib.parsers import parse_file
from lib.constants import SUPPORTED_LANGUAGES

console = Console()


class CodeIndexer:
    """代码索引器"""

    def __init__(self, config: Dict, data_path: Path):
        self.config = config
        self.data_path = data_path
        self.storage = create_storage(config)
        self.embedding = EmbeddingGenerator(
            model_id=config.get("embedding_model", "bge-code-v1"),
            use_gpu=config.get("use_gpu", True),
        )
        self.languages = config.get("languages", {})
        self.exclude_patterns = config.get("exclude_patterns", [])
        self.use_gitignore = config.get("gitignore", True)

    def initialize(self) -> bool:
        """初始化索引器"""
        # 初始化存储
        if not self.storage.initialize(self.data_path):
            return False

        # 加载嵌入模型
        if not self.embedding.load():
            return False

        return True

    def scan_files(
        self, root_path: Path, incremental: bool = False
    ) -> List[Path]:
        """扫描需要索引的文件"""
        files = []

        # 构建排除规则（配置中的 exclude_patterns）
        exclude_patterns = self.exclude_patterns.copy()

        # 如果启用遵守 .gitignore，读取所有 .gitignore 文件
        if self.use_gitignore:
            gitignore_patterns = self._load_gitignore_patterns(root_path)
            if gitignore_patterns:
                exclude_patterns.extend(gitignore_patterns)

        spec = pathspec.PathSpec.from_lines("gitwildmatch", exclude_patterns)

        # 获取启用的语言扩展名
        enabled_extensions = set()
        for lang, enabled in self.languages.items():
            if enabled:
                if lang in SUPPORTED_LANGUAGES:
                    enabled_extensions.update(SUPPORTED_LANGUAGES[lang])

        # 扫描目录（添加超时和异常处理）
        def safe_rglob(path: Path):
            """安全的递归目录扫描，跳过不可访问的目录"""
            try:
                for item in path.iterdir():
                    try:
                        # 检查是否是文件或目录
                        is_file = item.is_file()
                        is_dir = item.is_dir()

                        if is_file:
                            yield item
                        elif is_dir:
                            # 跳过某些特殊目录
                            if item.name.startswith('.') or item.name in ('node_modules', '__pycache__', 'venv', '.venv'):
                                continue
                            # 递归扫描
                            yield from safe_rglob(item)
                    except (OSError, TimeoutError, PermissionError):
                        # 跳过不可访问的路径
                        continue
            except (OSError, TimeoutError, PermissionError):
                # 跳过不可访问的目录
                pass

        for file_path in safe_rglob(root_path):
            try:
                # 检查排除规则
                relative_path = file_path.relative_to(root_path)
                if spec.match_file(str(relative_path)):
                    continue

                # 检查扩展名
                if file_path.suffix in enabled_extensions:
                    files.append(file_path)
            except (OSError, TimeoutError, PermissionError):
                # 跳过处理失败的文件
                continue

        return files

    def _load_gitignore_patterns(self, root_path: Path) -> List[str]:
        """加载项目中所有 .gitignore 文件的规则"""
        patterns = []

        try:
            # 查找所有 .gitignore 文件
            for gitignore_path in root_path.rglob(".gitignore"):
                try:
                    # 跳过虚拟环境目录中的 .gitignore（它们通常包含 * 规则）
                    if ".venv" in gitignore_path.parts or "venv" in gitignore_path.parts:
                        continue

                    with open(gitignore_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            # 跳过空行和注释
                            if not line or line.startswith("#"):
                                continue
                            # 跳过以 ! 开头的否定规则（pathspec 不支持）
                            if line.startswith("!"):
                                continue
                            # 跳过单独的 * 规则（会匹配所有文件）
                            if line == "*":
                                continue
                            patterns.append(line)
                except Exception:
                    # 忽略读取失败的 .gitignore 文件
                    pass
        except Exception:
            pass

        return patterns

    def index_file(self, file_path: Path) -> int:
        """索引单个文件"""
        # 确定语言
        language = self._detect_language(file_path)
        if not language:
            return 0

        # 解析代码
        chunks = parse_file(file_path, language)
        if not chunks:
            return 0

        # 生成嵌入
        indexed_chunks = []
        skipped_chunks = 0
        for chunk in chunks:
            # 截断代码
            code = truncate_code(chunk["code"])

            # 生成嵌入
            embedding = self.embedding.encode(code)
            if not embedding or not embedding[0]:
                skipped_chunks += 1
                continue

            # 验证嵌入维度（应与配置的模型维度匹配）
            model_name = self.config.get("embedding_model", "bge-code-v1")
            # 模型维度映射
            model_dims = {
                "bge-small-en": 384,
                "bge-small-zh": 512,
                "bge-base-en": 768,
                "bge-large-en": 1024,
                "bge-code-v1": 768,
                "jina-small-en": 512,
                "jina-base-en": 768,
                "jina-code": 768,
                "jina-v2-code": 768,
                "jina-v2-small": 512,
                "arctic-embed-xs": 384,
                "arctic-embed-s": 384,
                "arctic-embed-m": 768,
                "arctic-embed-l": 1024,
                "gte-large": 1024,
                "mxbai-embed-large": 1024,
                "multilingual-e5-small": 384,
                "multilingual-e5-large": 1024,
                "nomic-embed-text-1.5": 768,
                "all-minilm-l6-v2": 384,
                "default": 384,
            }
            expected_dim = model_dims.get(model_name, 768)
            if len(embedding[0]) != expected_dim:
                # 维度不匹配，跳过该向量
                skipped_chunks += 1
                continue

            # 生成 ID
            chunk_id = generate_code_id(
                chunk["file_path"], chunk["start_line"], chunk["type"]
            )

            indexed_chunk = {
                "id": chunk_id,
                "file_path": chunk["file_path"],
                "language": chunk["language"],
                "code_type": chunk["type"],
                "name": chunk["name"],
                "code": code,
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"],
                "vector": embedding[0],
                "metadata": chunk.get("metadata", {}),
                "indexed_at": datetime.now().isoformat(),
            }
            indexed_chunks.append(indexed_chunk)

        # 存储到数据库
        if indexed_chunks:
            self.storage.insert(indexed_chunks)

        return len(indexed_chunks)

    def index_project(
        self,
        root_path: Path,
        incremental: bool = False,
        batch_size: int = 100,
    ) -> Dict:
        """索引整个项目"""
        stats = {
            "total_files": 0,
            "indexed_files": 0,
            "total_chunks": 0,
            "failed_files": 0,
        }

        # 扫描文件
        files = self.scan_files(root_path, incremental)
        stats["total_files"] = len(files)

        if not files:
            return stats

        # 使用 rich 进度条
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                "[cyan]正在索引文件...", total=len(files)
            )

            # 批量索引
            for file_path in files:
                try:
                    chunk_count = self.index_file(file_path)
                    stats["indexed_files"] += 1
                    stats["total_chunks"] += chunk_count

                except Exception as e:
                    stats["failed_files"] += 1
                finally:
                    progress.update(task, advance=1)

        # 索引完成后，自动创建余弦距离向量索引
        if stats["total_chunks"] >= 100:
            console.print("[dim]\\n正在创建余弦距离向量索引...[/dim]")
            self.create_index()

        return stats

    def create_index(self, index_type: str = "IVF_PQ") -> bool:
        """创建向量索引

        Args:
            index_type: 索引类型 ("IVF_PQ" 或 "HNSW")
        """
        return self.storage.create_vector_index(index_type=index_type)

    def get_index_status(self) -> Dict:
        """获取索引状态"""
        return self.storage.check_index_status()

    def _detect_language(self, file_path: Path) -> Optional[str]:
        """检测文件的语言"""
        suffix = file_path.suffix

        # 根据扩展名映射语言
        for lang, extensions in SUPPORTED_LANGUAGES.items():
            if suffix in extensions:
                return lang

        return None

    def search(
        self,
        query: str,
        limit: int = 10,
        language: Optional[str] = None,
        threshold: float = 0.5,
    ) -> List[Dict]:
        """语义搜索"""
        # 生成查询嵌入
        query_vector = self.embedding.encode_query(query)
        if not query_vector:
            return []

        # 构建过滤条件
        filters = {}
        if language:
            filters["language"] = language

        # 搜索
        results = self.storage.search(
            query_vector=query_vector, limit=limit, filters=filters
        )

        # 过滤低相似度结果
        filtered_results = [
            r for r in results if r.get("similarity", 0) >= threshold
        ]

        return filtered_results

    def get_stats(self) -> Dict:
        """获取索引统计信息"""
        total_count = self.storage.count()

        return {
            "total_chunks": total_count,
            "backend": self.config.get("backend", "lancedb"),
            "model": self.config.get("embedding_model", "bge-code-v1"),
        }

    def clear(self) -> bool:
        """清空索引"""
        try:
            # 删除所有数据
            self.storage.delete({})
            return True
        except Exception as e:
            print(f"错误: 清空索引失败: {e}")
            return False

    def close(self):
        """关闭索引器"""
        self.storage.close()
