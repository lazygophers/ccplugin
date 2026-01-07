#!/usr/bin/env python3
"""
混合索引器 - 整合 FastEmbed、CodeModel 和符号索引

支持多引擎索引和混合检索。
"""

from pathlib import Path
from typing import List, Dict, Optional, Any, TYPE_CHECKING
from datetime import datetime

from .storage import create_storage
from .embedding import EmbeddingGenerator, generate_code_id, truncate_code
from .codemodel import HybridEmbeddingGenerator
from .symbol_index import SymbolIndex, SymbolExtractor
from .parsers import parse_file
from .language_config import (
    get_chunk_size,
    get_chunk_overlap,
    get_indexing_priority,
)


class HybridIndexer:
    """混合索引器 - 支持多引擎"""

    def __init__(self, config: Dict, data_path: Path):
        self.config = config
        self.data_path = data_path
        self.languages = config.get("languages", {})
        self.exclude_patterns = config.get("exclude_patterns", [])
        self.use_gitignore = config.get("gitignore", True)

        # 引擎配置
        engine_config = config.get("engines", {})
        fastembed_config = engine_config.get("fastembed", {})
        codemodel_config = engine_config.get("codemodel", {})
        symbols_config = engine_config.get("symbols", {})

        # FastEmbed 引擎（默认启用）
        if fastembed_config.get("enabled", True):
            self.fastembed = EmbeddingGenerator(
                model_id=fastembed_config.get("model", config.get("embedding_model", "default")),
                use_gpu=config.get("use_gpu", True),
            )
        else:
            self.fastembed = None

        # CodeModel 引擎（可选）
        if codemodel_config.get("enabled", False):
            self.codemodel = HybridEmbeddingGenerator(
                fastembed_model=fastembed_config.get("model", config.get("embedding_model", "default")),
                codemodel_model=codemodel_config.get("model"),
                use_gpu=config.get("use_gpu", True),
            )
        else:
            self.codemodel = None

        # 符号索引（可选）
        if symbols_config.get("enabled", False):
            self.symbol_index = SymbolIndex(data_path)
        else:
            self.symbol_index = None

        # 向量存储
        self.storage = create_storage(config)

    def initialize(self) -> bool:
        """初始化索引器"""
        success = True

        # 初始化向量存储
        if not self.storage.initialize(self.data_path):
            return False

        # 初始化 FastEmbed
        if self.fastembed and not self.fastembed.load():
            return False

        # 初始化 CodeModel
        if self.codemodel and not self.codemodel.load():
            return False

        # 初始化符号索引
        if self.symbol_index and not self.symbol_index.initialize():
            return False

        return success

    def scan_files(
        self, root_path: Path, incremental: bool = False
    ) -> List[Path]:
        """扫描需要索引的文件"""
        import pathspec

        files = []
        exclude_patterns = self.exclude_patterns.copy()

        # 加载 .gitignore 规则
        if self.use_gitignore:
            gitignore_patterns = self._load_gitignore_patterns(root_path)
            if gitignore_patterns:
                exclude_patterns.extend(gitignore_patterns)

        spec = pathspec.PathSpec.from_lines("gitwildmatch", exclude_patterns)

        # 获取启用的语言扩展名
        enabled_extensions = set()
        for lang, enabled in self.languages.items():
            if enabled:
                from semantic import SUPPORTED_LANGUAGES
                if lang in SUPPORTED_LANGUAGES:
                    enabled_extensions.update(SUPPORTED_LANGUAGES[lang])

        # 扫描目录
        for file_path in root_path.rglob("*"):
            if not file_path.is_file():
                continue

            relative_path = file_path.relative_to(root_path)
            if spec.match_file(str(relative_path)):
                continue

            if file_path.suffix in enabled_extensions:
                files.append(file_path)

        # 增量索引：过滤未修改的文件
        if incremental and self.symbol_index:
            modified = self.symbol_index.get_modified_files([str(f) for f in files])
            files = [Path(f) for f in modified]

        return files

    def index_file(self, file_path: Path) -> Dict:
        """索引单个文件 - 使用语言特定策略"""
        stats = {
            "symbols": 0,
            "chunks": 0,
            "errors": 0,
        }

        # 1. 提取符号
        if self.symbol_index:
            try:
                symbols = SymbolExtractor.extract_from_file(file_path)
                if symbols:
                    self.symbol_index.update_file_symbols(str(file_path), symbols)
                    stats["symbols"] = len(symbols)
            except Exception as e:
                print(f"警告: 符号提取失败 {file_path}: {e}")
                stats["errors"] += 1

        # 2. 生成向量嵌入
        language = self._detect_language(file_path)
        if not language:
            return stats

        # 获取语言特定配置
        chunk_size = get_chunk_size(language, default=500)
        chunk_overlap = get_chunk_overlap(language, default=50)

        chunks = parse_file(file_path, language)
        if not chunks:
            return stats

        for chunk in chunks:
            try:
                # 使用语言特定的分块大小
                code = truncate_code(chunk["code"], max_length=chunk_size)

                # FastEmbed 向量
                fast_vector = None
                if self.fastembed:
                    fast_embedding = self.fastembed.encode(code)
                    if fast_embedding and fast_embedding[0]:
                        fast_vector = fast_embedding[0]

                # CodeModel 向量
                code_vector = None
                if self.codemodel:
                    code_embedding = self.codemodel.encode_code(code)
                    if code_embedding and code_embedding[0]:
                        code_vector = code_embedding[0]

                # 生成 ID
                chunk_id = generate_code_id(
                    chunk["file_path"], chunk["start_line"], chunk["type"]
                )

                # 构建元数据（包含语言特定信息）
                metadata = chunk.get("metadata", {})
                metadata["language_priority"] = get_indexing_priority(language)
                metadata["chunk_size"] = chunk_size
                metadata["chunk_overlap"] = chunk_overlap

                # 存储到向量数据库
                indexed_chunk = {
                    "id": chunk_id,
                    "file_path": chunk["file_path"],
                    "language": chunk["language"],
                    "code_type": chunk["type"],
                    "name": chunk["name"],
                    "code": code,
                    "start_line": chunk["start_line"],
                    "end_line": chunk["end_line"],
                    "vector": fast_vector or code_vector,  # 优先使用 FastEmbed
                    "metadata": metadata,
                    "indexed_at": datetime.now().isoformat(),
                }

                # 存储双向量（如果都可用）
                if fast_vector and code_vector:
                    indexed_chunk["code_vector"] = code_vector

                self.storage.insert([indexed_chunk])
                stats["chunks"] += 1

            except Exception as e:
                print(f"警告: 嵌入生成失败 {file_path}: {e}")
                stats["errors"] += 1

        return stats

    def index_project(
        self,
        root_path: Path,
        incremental: bool = False,
        progress: Optional[Any] = None,
        silent: bool = False,
    ) -> Dict:
        """索引整个项目

        Args:
            root_path: 项目根路径
            incremental: 是否增量索引
            progress: rich.progress.Progress 对象（可选）
            silent: 静默模式（不显示进度）
        """
        stats = {
            "total_files": 0,
            "indexed_files": 0,
            "total_symbols": 0,
            "total_chunks": 0,
            "failed_files": 0,
        }

        files = self.scan_files(root_path, incremental)
        stats["total_files"] = len(files)

        if not files:
            return stats

        # 使用进度条或简单循环
        if progress and not silent:
            task_id = progress.add_task(
                "[cyan]索引文件...",
                total=len(files),
            )

        for i, file_path in enumerate(files):
            try:
                file_stats = self.index_file(file_path)
                stats["indexed_files"] += 1
                stats["total_symbols"] += file_stats.get("symbols", 0)
                stats["total_chunks"] += file_stats.get("chunks", 0)

                # 更新进度条（显示累计统计）
                if progress and not silent:
                    progress.update(
                        task_id,
                        advance=1,
                        description=(
                            f"[cyan]索引 {file_path.name} | "
                            f"[green]{stats['total_symbols']}符号[/green] | "
                            f"[blue]{stats['total_chunks']}代码块[/blue]"
                        ),
                    )

                # 回退到简单进度显示（无 rich.progress 时）
                elif not silent and (i + 1) % 10 == 0:
                    print(f"进度: {i + 1}/{len(files)} 文件 | {stats['total_symbols']}符号 | {stats['total_chunks']}代码块")

            except Exception as e:
                stats["failed_files"] += 1
                if not silent:
                    print(f"警告: 索引失败 {file_path}: {e}")

        return stats

    def hybrid_search(
        self,
        query: str,
        limit: int = 10,
        language: Optional[str] = None,
        threshold: float = 0.7,
    ) -> Dict:
        """混合检索 - 整合多引擎结果"""
        results = {
            "symbols": [],
            "fastembed": [],
            "codemodel": [],
            "fused": [],
        }

        # 1. 符号搜索（最快，精确匹配）
        if self.symbol_index:
            try:
                symbol_results = self.symbol_index.search_by_name(query, limit=limit)
                results["symbols"] = symbol_results
            except Exception as e:
                print(f"警告: 符号搜索失败: {e}")

        # 2. FastEmbed 语义搜索（快速）
        if self.fastembed:
            try:
                query_vector = self.fastembed.encode_query(query)
                if query_vector:
                    fast_results = self.storage.search(
                        query_vector=query_vector,
                        limit=limit,
                        filters={"language": language} if language else {},
                    )
                    results["fastembed"] = [
                        r for r in fast_results if r.get("similarity", 0) >= threshold
                    ]
            except Exception as e:
                print(f"警告: FastEmbed 搜索失败: {e}")

        # 3. CodeModel 搜索（精准）
        # 暂时禁用：LanceDB 版本不支持指定向量列搜索
        # TODO: 升级到支持多向量列搜索的版本，或使用其他方案
        # if self.codemodel:
        #     try:
        #         query_vector = self.codemodel.encode_query(query, use_codemodel=True)
        #         if query_vector:
        #             code_results = self.storage.search(
        #                 query_vector=query_vector,
        #                 limit=limit,
        #                 filters={"language": language} if language else {},
        #             )
        #             results["codemodel"] = [
        #                 r for r in code_results if r.get("similarity", 0) >= threshold
        #             ]
        #     except Exception as e:
        #         print(f"警告: CodeModel 搜索失败: {e}")

        # 4. 融合结果
        results["fused"] = self._fuse_results(
            results["symbols"],
            results["fastembed"],
            results["codemodel"],
            limit=limit,
        )

        return results

    def _fuse_results(
        self,
        symbols: List[Dict],
        fast_results: List[Dict],
        code_results: List[Dict],
        limit: int,
    ) -> List[Dict]:
        """融合多引擎结果"""
        # 获取融合权重
        fusion_weights = self.config.get("fusion_weights", {
            "symbols": 0.3,
            "fastembed": 0.4,
            "codemodel": 0.3,
        })

        # 收集所有结果
        all_results = {}

        # 符号结果（权重最高）
        for result in symbols:
            file_path = result.get("file_path", "")
            line = result.get("line_number", 0)
            key = f"{file_path}:{line}"
            all_results[key] = {
                "data": result,
                "score": fusion_weights.get("symbols", 0.3) * 1.0,  # 精确匹配满分
                "source": "symbol",
            }

        # FastEmbed 结果
        for result in fast_results:
            file_path = result.get("file_path", "")
            line = result.get("start_line", 0)
            key = f"{file_path}:{line}"
            similarity = result.get("similarity", 0)
            if key not in all_results:
                all_results[key] = {
                    "data": result,
                    "score": similarity * fusion_weights.get("fastembed", 0.4),
                    "source": "fastembed",
                }
            else:
                # 累加分数
                all_results[key]["score"] += similarity * fusion_weights.get("fastembed", 0.4)

        # CodeModel 结果
        for result in code_results:
            file_path = result.get("file_path", "")
            line = result.get("start_line", 0)
            key = f"{file_path}:{line}"
            similarity = result.get("similarity", 0)
            if key not in all_results:
                all_results[key] = {
                    "data": result,
                    "score": similarity * fusion_weights.get("codemodel", 0.3),
                    "source": "codemodel",
                }
            else:
                # 累加分数
                all_results[key]["score"] += similarity * fusion_weights.get("codemodel", 0.3)

        # 排序并返回
        sorted_results = sorted(
            all_results.values(),
            key=lambda x: x["score"],
            reverse=True,
        )[:limit]

        return [r["data"] for r in sorted_results]

    def _detect_language(self, file_path: Path) -> Optional[str]:
        """检测文件的语言"""
        suffix = file_path.suffix
        from semantic import SUPPORTED_LANGUAGES

        for lang, extensions in SUPPORTED_LANGUAGES.items():
            if suffix in extensions:
                return lang
        return None

    def _load_gitignore_patterns(self, root_path: Path) -> List[str]:
        """加载 .gitignore 规则

        只加载 root_path 及其子目录中的 .gitignore 文件，
        不加载父目录的 .gitignore，避免被项目根目录规则影响
        """
        patterns = []
        try:
            # 只扫描 root_path 下的 .gitignore 文件，不递归到父目录
            for gitignore_path in root_path.glob(".gitignore"):
                try:
                    with open(gitignore_path, "r", encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            # 跳过空行、注释和否定模式（简化处理）
                            if not line or line.startswith("#") or line.startswith("!"):
                                continue
                            patterns.append(line)
                except Exception:
                    pass
        except Exception:
            pass
        return patterns

    def get_stats(self) -> Dict:
        """获取索引统计"""
        stats = {
            "total_chunks": self.storage.count(),
            "backend": self.config.get("backend", "lancedb"),
        }

        if self.symbol_index:
            symbol_stats = self.symbol_index.get_stats()
            stats.update(symbol_stats)

        return stats

    def clear(self) -> bool:
        """清空索引"""
        try:
            self.storage.delete({})
            if self.symbol_index:
                self.symbol_index.clear()
            return True
        except Exception as e:
            print(f"错误: 清空索引失败: {e}")
            return False

    def close(self):
        """关闭索引器"""
        self.storage.close()
        if self.symbol_index:
            self.symbol_index.close()
