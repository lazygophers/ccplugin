#!/usr/bin/env python3
"""
Semantic Code Search - 代码语义搜索插件核心脚本

使用 LanceDB/SeekDB 存储向量索引，支持多编程语言、多模型、GPU加速。
数据存储位置: <项目根目录>/.lazygophers/ccplugin/semantic/

⚠️ 必须使用 uv 执行此脚本：
  uv run semantic.py <command> [args...]

依赖：
  - typer: 现代化 CLI 框架
  - rich: 终端美化输出
  - lancedb: 向量数据库（嵌入式）
  - sentence-transformers/flagembedding: 代码嵌入模型
"""
import warnings; warnings.filterwarnings('ignore')

import sys
from pathlib import Path

# 添加项目根目录到 sys.path 以导入 lib 模块
# 从脚本目录向上查找项目根目录（包含lib目录的位置）
script_path = Path(__file__).resolve().parent  # scripts/
plugin_path = script_path.parent  # plugins/semantic/ 或 plugins/
project_root = plugin_path.parent.parent if plugin_path.name != 'semantic' else plugin_path.parent.parent.parent

# 如果自动查找失败，使用备选策略：向上查找包含.lazygophers的目录
if not (project_root / 'lib').exists():
    current = Path(__file__).resolve().parent
    for _ in range(5):
        if (current / 'lib').exists():
            project_root = current
            break
        current = current.parent

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import yaml
from typing import List, Dict, Optional, Literal
from datetime import datetime
import hashlib

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# ========== 常量定义 ==========

PLUGIN_NAME = "semantic"
DATA_DIR = ".lazygophers/ccplugin/semantic"
CONFIG_FILE = "config.yaml"
LANCEDB_DIR = "lancedb"
SEEKDB_DIR = "seekdb"

# 支持的后端类型
BackendType = Literal["lancedb"]

# 导入语言常量
from lib.constants import SUPPORTED_LANGUAGES

# 支持的嵌入模型
SUPPORTED_MODELS = {
    # BGE 系列（推荐）
    "default": {
        "name": "BAAI/bge-small-en-v1.5",
        "dim": 384,
        "description": "默认模型，轻量快速",
    },
    "bge-small-en": {
        "name": "BAAI/bge-small-en-v1.5",
        "dim": 384,
        "description": "英文优化，轻量",
    },
    "bge-small-zh": {
        "name": "BAAI/bge-small-zh-v1.5",
        "dim": 512,
        "description": "中文优化",
    },
    "bge-base-en": {
        "name": "BAAI/bge-base-en-v1.5",
        "dim": 768,
        "description": "英文通用",
    },
    "bge-large-en": {
        "name": "BAAI/bge-large-en-v1.5",
        "dim": 1024,
        "description": "英文高精度",
    },
    # Jina 系列
    "jina-small-en": {
        "name": "jinaai/jina-embeddings-v2-small-en",
        "dim": 512,
        "description": "Jina 英文轻量",
    },
    "jina-base-en": {
        "name": "jinaai/jina-embeddings-v2-base-en",
        "dim": 768,
        "description": "Jina 英文通用",
    },
    "jina-base-de": {
        "name": "jinaai/jina-embeddings-v2-base-de",
        "dim": 768,
        "description": "Jina 德语",
    },
    "jina-code": {
        "name": "jinaai/jina-embeddings-v2-base-code",
        "dim": 768,
        "description": "Jina 代码专用",
    },
    # Snowflake Arctic 系列
    "arctic-embed-xs": {
        "name": "snowflake/snowflake-arctic-embed-xs",
        "dim": 384,
        "description": "Arctic 极轻量",
    },
    "arctic-embed-s": {
        "name": "snowflake/snowflake-arctic-embed-s",
        "dim": 384,
        "description": "Arctic 轻量",
    },
    "arctic-embed-m": {
        "name": "snowflake/snowflake-arctic-embed-m",
        "dim": 768,
        "description": "Arctic 通用",
    },
    "arctic-embed-m-long": {
        "name": "snowflake/snowflake-arctic-embed-m-long",
        "dim": 768,
        "description": "Arctic 长文本",
    },
    "arctic-embed-l": {
        "name": "snowflake/snowflake-arctic-embed-l",
        "dim": 1024,
        "description": "Arctic 高精度",
    },
    # Nomic 系列（多模态）
    "nomic-embed-text": {
        "name": "nomic-ai/nomic-embed-text-v1",
        "dim": 768,
        "description": "Nomic 嵌入",
    },
    "nomic-embed-text-1.5": {
        "name": "nomic-ai/nomic-embed-text-v1.5",
        "dim": 768,
        "description": "Nomic 嵌入 v1.5",
    },
    "nomic-embed-text-Q": {
        "name": "nomic-ai/nomic-embed-text-v1.5-Q",
        "dim": 768,
        "description": "Nomic 嵌入 v1.5 量化版",
    },
    # Sentence Transformers 系列
    "all-minilm-l6-v2": {
        "name": "sentence-transformers/all-MiniLM-L6-v2",
        "dim": 384,
        "description": "MiniLM 极轻量",
    },
    "paraphrase-multilingual-mpnet": {
        "name": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        "dim": 768,
        "description": "多语言 MPNet",
    },
    "paraphrase-multilingual-MiniLM": {
        "name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "dim": 384,
        "description": "多语言 MiniLM",
    },
    # E5 系列
    "multilingual-e5-small": {
        "name": "intfloat/multilingual-e5-small",
        "dim": 384,
        "description": "E5 多语言轻量",
    },
    "multilingual-e5-large": {
        "name": "intfloat/multilingual-e5-large",
        "dim": 1024,
        "description": "E5 多语言高精度",
    },
    # GTE 系列
    "gte-large": {
        "name": "thenlper/gte-large",
        "dim": 1024,
        "description": "GTE 大型",
    },
    # MXBAI 系列
    "mxbai-embed-large": {
        "name": "mixedbread-ai/mxbai-embed-large-v1",
        "dim": 1024,
        "description": "MXBAI 大型",
    },
    # CLIP 系列
    "clip-vit-b-32": {
        "name": "Qdrant/clip-ViT-B-32-text",
        "dim": 512,
        "description": "CLIP 多模态",
    },
}

# 默认配置 - 全部使用最高精度配置
DEFAULT_CONFIG = {
    "backend": "lancedb",
    "embedding_model": "multilingual-e5-large",  # 多语言最高精度，1024维
    "chunk_size": 500,
    "chunk_overlap": 50,
    "gitignore": True,  # 默认遵守 .gitignore
    # 引擎配置 - 全部启用，使用最高精度模型
    "engines": {
        "fastembed": {
            "enabled": True,
            "model": "multilingual-e5-large",  # 多语言最高精度模型 (1024维)
        },
        "codemodel": {
            "enabled": True,  # 启用以获得更好的代码语义理解
            "model": "codet5+",  # 代码理解最高精度模型
        },
        "symbols": {
            "enabled": True,  # 启用以获得精确匹配能力
        },
    },
    # 检索策略 - 使用混合策略获得最佳效果
    "search_strategy": "hybrid",  # fast, hybrid, code, symbols
    # 融合权重 - 语义搜索优先策略
    "fusion_weights": {
        "symbols": 0.1,     # 精确匹配权重降低
        "fastembed": 0.5,   # 向量语义权重提高
        "codemodel": 0.4,   # 代码语义权重提高
    },
    "languages": {
        # 所有语言的默认值（会被 scan_project_languages 覆盖）
        "python": False,
        "golang": False,
        "javascript": False,
        "typescript": False,
        "rust": False,
        "flutter": False,
        "android": False,
        "bash": False,
        "markdown": False,
        "java": False,
        "kotlin": False,
        "csharp": False,
        "swift": False,
        "php": False,
        "ruby": False,
        "c": False,
        "cpp": False,
        "sql": False,
        "dockerfile": False,
        "powershell": False,
    },
    "exclude_patterns": [
        "node_modules",
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        ".lazygophers",
        "dist",
        "build",
        "*.min.js",
        "*.min.css",
    ],
}

# 初始化控制台
console = Console()
app = typer.Typer(
    name="semantic",
    help="代码语义搜索命令 - 基于向量嵌入的智能搜索",
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


# ========== 配置管理 ==========


def get_data_path(project_root: Optional[str] = None) -> Path:
    """获取数据目录路径"""
    if project_root is None:
        # 从当前目录向上查找项目根目录（包含 .lazygophers 的目录）
        current = Path.cwd()
        for level in range(5):
            if (current / ".lazygophers").exists():
                project_root = str(current)
                break
            current = current.parent
        else:
            project_root = str(Path.cwd())

    data_path = Path(project_root) / DATA_DIR
    return data_path


def get_config_path(project_root: Optional[str] = None) -> Path:
    """获取配置文件路径"""
    return get_data_path(project_root) / CONFIG_FILE


def load_config(project_root: Optional[str] = None) -> Dict:
    """加载配置文件"""
    config_path = get_config_path(project_root)

    if not config_path.exists():
        # 使用默认配置
        return DEFAULT_CONFIG.copy()

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        # 合并默认配置（处理新增字段）
        merged_config = DEFAULT_CONFIG.copy()
        merged_config.update(config)
        return merged_config
    except Exception as e:
        console.print(f"[yellow]警告: 配置文件读取失败，使用默认配置: {e}[/yellow]")
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict, project_root: Optional[str] = None) -> bool:
    """保存配置文件（带注释）"""
    config_path = get_config_path(project_root)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            # 写入文件头注释
            f.write("# Semantic 代码语义搜索配置文件\n")
            f.write("# 此文件在首次初始化时自动生成，之后不会自动修改\n")
            f.write("# 如需修改配置，请使用命令: /semantic config 或 /semantic languages\n\n")

            # 逐字段写入配置（带注释）
            f.write("# 向量数据库后端类型（当前仅支持 lancedb）\n")
            f.write(f"backend: {config.get('backend', 'lancedb')}\n\n")

            # 嵌入模型详细说明
            f.write("# ============================================\n")
            f.write("# 嵌入模型选择 (embedding_model)\n")
            f.write("# ============================================\n")
            f.write("# 选择合适的模型可以平衡搜索准确度和性能\n")
            f.write("# \n")
            f.write("# 【BGE 系列 - 推荐】\n")
            f.write("#   bge-small-en     - 英文优化，384维，轻量快速，适合大多数场景\n")
            f.write("#   bge-small-zh     - 中文优化，512维，适合中文项目\n")
            f.write("#   bge-base-en      - 英文通用，768维，平衡性能和准确度\n")
            f.write("#   bge-large-en     - 英文高精度，1024维，搜索效果最佳，推荐用于生产环境\n")
            f.write("# \n")
            f.write("# 【Jina 系列】\n")
            f.write("#   jina-small-en    - 轻量快速，512维\n")
            f.write("#   jina-base-en     - 通用英文，768维\n")
            f.write("#   jina-code        - 代码专用，768维，适合代码搜索\n")
            f.write("# \n")
            f.write("# 【Arctic 系列 - Snowflake】\n")
            f.write("#   arctic-embed-xs  - 极轻量，384维，资源受限环境\n")
            f.write("#   arctic-embed-s   - 轻量，384维\n")
            f.write("#   arctic-embed-m   - 通用，768维\n")
            f.write("#   arctic-embed-l   - 高精度，1024维\n")
            f.write("# \n")
            f.write("# 【其他高质量模型】\n")
            f.write("#   gte-large        - 高精度，1024维，综合性能优秀\n")
            f.write("#   mxbai-embed-large - 高精度，1024维\n")
            f.write("#   multilingual-e5-small  - 多语言，384维\n")
            f.write("#   multilingual-e5-large  - 多语言高精度，1024维\n")
            f.write("#   nomic-embed-text-1.5   - 最新 Nomic，768维\n")
            f.write("#   all-minilm-l6-v2  - 极轻量，384维，最快速度\n")
            f.write("# \n")
            f.write("# 【推荐配置】\n")
            f.write("#   生产环境（高准确度）: bge-large-en 或 gte-large\n")
            f.write("#   中文项目: bge-small-zh 或 multilingual-e5-large\n")
            f.write("#   代码搜索: jina-code 或启用 codemodel 引擎\n")
            f.write("#   资源受限: all-minilm-l6-v2 或 arctic-embed-xs\n")
            f.write("# ============================================\n")
            model_value = config.get('embedding_model', 'bge-large-en')
            # 对包含特殊字符的模型名称使用引号
            if any(c in model_value for c in ['+', '-', ' ', ':', '#', '&', '*', '?', '[', ']']):
                f.write(f"embedding_model: \"{model_value}\"\n\n")
            else:
                f.write(f"embedding_model: {model_value}\n\n")

            f.write("# ============================================\n")
            f.write("# 硬件加速说明\n")
            f.write("# ============================================\n")
            f.write("# GPU/硬件加速已自动检测并启用，无需手动配置\n")
            f.write("# \n")
            f.write("# 支持的加速类型:\n")
            f.write("#   - Apple Silicon (M1/M2/M3): 自动启用 MPS (Metal Performance Shaders)\n")
            f.write("#   - NVIDIA GPU: 自动启用 CUDA 加速\n")
            f.write("#   - 其他平台: 使用 CPU 模式\n")
            f.write("# ============================================\n\n")

            f.write("# 代码分块大小（字符数）\n")
            f.write(f"chunk_size: {config.get('chunk_size', 500)}\n\n")

            f.write("# 分块重叠大小（字符数）\n")
            f.write(f"chunk_overlap: {config.get('chunk_overlap', 50)}\n\n")

            f.write("# 是否遵守 .gitignore 文件（索引时跳过 git 忽略的文件）\n")
            f.write(f"gitignore: {config.get('gitignore', True)}\n\n")

            # 引擎配置详细说明
            f.write("# ============================================\n")
            f.write("# 搜索引擎配置 (engines)\n")
            f.write("# ============================================\n")
            f.write("# 三个独立引擎，可单独启用或组合使用\n")
            f.write("# \n")
            f.write("# 【fastembed】快速向量搜索引擎\n")
            f.write("#   基于 FastEmbed，使用 ONNX 运行，轻量高效\n")
            f.write("#   模型选项:\n")
            f.write("#     bge-large-en     - 英文高精度（推荐）\n")
            f.write("#     bge-small-zh     - 中文优化\n")
            f.write("#     gte-large        - 综合性能优秀\n")
            f.write("#     jina-code        - 代码专用\n")
            f.write("#   优点: 速度快，资源占用低，无需 PyTorch\n")
            f.write("#   缺点: 对代码语义理解有限\n")
            f.write("# \n")
            f.write("# 【codemodel】代码专用模型引擎\n")
            f.write("#   基于 sentence-transformers，使用 CodeT5/UniXcoder 等代码模型\n")
            f.write("#   需要: uv sync --all-extras（安装 torch 和 transformers）\n")
            f.write("#   模型选项:\n")
            f.write("#     codet5+         - CodeT5+，代码理解最佳（推荐）\n")
            f.write("#     unixcoder       - UniXcoder，多语言支持\n")
            f.write("#     graphcodebert   - GraphCodeBERT，图结构分析\n")
            f.write("#     codebert        - CodeBERT，经典代码模型\n")
            f.write("#   优点: 对代码语义、API 调用、控制流理解深入\n")
            f.write("#   缺点: 资源占用高，索引慢，需要 PyTorch\n")
            f.write("# \n")
            f.write("# 【symbols】符号索引引擎\n")
            f.write("#   基于 SQLite FTS5 全文搜索，提取函数/类/变量名\n")
            f.write("#   模型选项: 无（无需配置模型）\n")
            f.write("#   优点: 极快速度，精确名称匹配，资源占用极低\n")
            f.write("#   缺点: 不支持语义搜索，只能匹配名称\n")
            f.write("# \n")
            f.write("# 【推荐配置】\n")
            f.write("#   小项目/资源受限: 仅 fastembed\n")
            f.write("#   大项目/高准确度: fastembed + codemodel + symbols（全部启用）\n")
            f.write("#   代码理解/重构: fastembed + codemodel\n")
            f.write("#   快速定位: 仅 symbols\n")
            f.write("# ============================================\n")
            engines = config.get("engines", {})
            f.write(f"engines:\n")
            for engine_name, engine_config in engines.items():
                f.write(f"  {engine_name}:\n")
                f.write(f"    enabled: {engine_config.get('enabled', False)}\n")
                if "model" in engine_config:
                    model_name = engine_config['model']
                    # 对包含特殊字符的模型名称使用引号
                    if any(c in model_name for c in ['+', '-', ' ', ':', '#', '&', '*', '?', '[', ']']):
                        f.write(f"    model: \"{model_name}\"\n")
                    else:
                        f.write(f"    model: {model_name}\n")
            f.write("\n")

            # 检索策略详细说明
            f.write("# ============================================\n")
            f.write("# 检索策略选择 (search_strategy)\n")
            f.write("# ============================================\n")
            f.write("# 控制使用哪些搜索引擎以及如何组合结果\n")
            f.write("# \n")
            f.write("# 【fast】快速搜索（默认小项目）\n")
            f.write("#   - 仅使用 FastEmbed 引擎\n")
            f.write("#   - 优点: 速度快，资源占用低\n")
            f.write("#   - 缺点: 对代码语义理解有限\n")
            f.write("#   - 适用: 小型项目、快速原型开发\n")
            f.write("# \n")
            f.write("# 【hybrid】混合搜索（推荐大项目）\n")
            f.write("#   - 融合 FastEmbed + CodeModel + Symbol 三个引擎\n")
            f.write("#   - 优点: 搜索准确度最高，结合向量、代码语义和符号匹配\n")
            f.write("#   - 缺点: 需要更多资源和索引时间\n")
            f.write("#   - 适用: 大型项目、生产环境、需要最佳搜索质量\n")
            f.write("# \n")
            f.write("# 【code】代码语义搜索\n")
            f.write("#   - 仅使用 CodeModel 引擎（CodeT5/UniXcoder）\n")
            f.write("#   - 优点: 对代码语义理解最深入\n")
            f.write("#   - 缺点: 索引和搜索速度较慢\n")
            f.write("#   - 适用: 代码理解、重构分析\n")
            f.write("# \n")
            f.write("# 【symbols】符号索引\n")
            f.write("#   - 仅使用符号索引（函数名、类名精确匹配）\n")
            f.write("#   - 优点: 极快速度，精确匹配\n")
            f.write("#   - 缺点: 不支持语义搜索\n")
            f.write("#   - 适用: 快速定位已知函数/类\n")
            f.write("# \n")
            f.write("# 【推荐配置】\n")
            f.write("#   小项目（<1000文件）: fast\n")
            f.write("#   大项目（>=1000文件）: hybrid\n")
            f.write("#   代码理解/重构: code\n")
            f.write("#   快速定位: symbols\n")
            f.write("# ============================================\n")
            strategy_value = config.get('search_strategy', 'hybrid')
            # 对包含特殊字符的策略名称使用引号
            if any(c in strategy_value for c in ['+', '-', ' ', ':', '#', '&', '*', '?', '[', ']']):
                f.write(f"search_strategy: \"{strategy_value}\"\n\n")
            else:
                f.write(f"search_strategy: {strategy_value}\n\n")

            f.write("# ============================================\n")
            f.write("# 融合权重配置 (fusion_weights)\n")
            f.write("# ============================================\n")
            f.write("# 仅在使用 hybrid 检索策略时生效\n")
            f.write("# 控制三个引擎的搜索结果在最终排序中的权重\n")
            f.write("# \n")
            f.write("# symbols:    符号索引权重（精确匹配函数名、类名）\n")
            f.write("#              范围: 0.0-1.0\n")
            f.write("#              增加: 提高精确名称匹配的优先级\n")
            f.write("# \n")
            f.write("# fastembed:  向量搜索权重（FastEmbed 语义相似度）\n")
            f.write("#              范围: 0.0-1.0\n")
            f.write("#              增加: 提高语义相关性的优先级\n")
            f.write("# \n")
            f.write("# codemodel:   代码模型权重（CodeModel 代码语义）\n")
            f.write("#              范围: 0.0-1.0\n")
            f.write("#              增加: 提高代码语义理解的优先级\n")
            f.write("# \n")
            f.write("# 【推荐配置】\n")
            f.write("#   语义搜索优先（默认）: symbols=0.1, fastembed=0.5, codemodel=0.4\n")
            f.write("#   精确匹配优先:     symbols=0.6, fastembed=0.2, codemodel=0.2\n")
            f.write("#   完全均衡:         symbols=0.33, fastembed=0.34, codemodel=0.33\n")
            f.write("# ============================================\n")
            f.write(f"fusion_weights:\n")
            fusion_weights = config.get("fusion_weights", {})
            f.write(f"  symbols: {fusion_weights.get('symbols', 0.1)}\n")
            f.write(f"  fastembed: {fusion_weights.get('fastembed', 0.5)}\n")
            f.write(f"  codemodel: {fusion_weights.get('codemodel', 0.4)}\n\n")

            f.write("# ============================================\n")
            f.write("# 语言特定优化策略\n")
            f.write("# ============================================\n")
            f.write("# Semantic 为不同编程语言提供针对性的优化策略\n")
            f.write("# \n")
            f.write("# 【高优先级语言（完整解析）】\n")
            f.write("#   Python  - AST 解析，提取函数/类/装饰器/类型提示\n")
            f.write("#   Golang  - 函数/接口/结构体解析\n")
            f.write("#   Rust    - 解析函数/结构体/特质/impl（可选 syn 库）\n")
            f.write("#   Flutter - Widget/类/方法解析\n")
            f.write("#   Java    - 类/接口/注解解析（可选 javalang 库）\n")
            f.write("#   Kotlin  - 类/函数/对象/扩展解析\n")
            f.write("#   TypeScript - 类/接口/类型解析\n")
            f.write("# \n")
            f.write("# 【中优先级语言（基础解析）】\n")
            f.write("#   JavaScript - 函数/类/箭头函数解析\n")
            f.write("#   C++        - 类/模板解析\n")
            f.write("#   C#         - 类/接口解析\n")
            f.write("#   Swift      - 类/结构体/协议解析\n")
            f.write("# \n")
            f.write("# 【低优先级语言（简单分块）】\n")
            f.write("#   C, PHP, Ruby, Bash - 按行数分块\n")
            f.write("# \n")
            f.write("# 【语言特定配置】\n")
            f.write("#   chunk_size:     分块大小（Python=500, Rust=300, Go=400）\n")
            f.write("#   chunk_overlap:  分块重叠（自适应调整）\n")
            f.write("#   推荐模型:      Python→codet5+, Rust→unixcoder, Go→jina-code\n")
            f.write("# \n")
            f.write("# 【可选依赖】\n")
            f.write("#   安装完整依赖: uv sync --all-extras\n")
            f.write("#   Java:  javalang (AST 解析) - 已包含在 parsers 组\n")
            f.write("#   Rust:  使用正则解析（syn 是 Rust 库，Python 端回退）\n")
            f.write("# ============================================\n")
            f.write("# 启用的编程语言（true=启用, false=禁用）\n")
            f.write("# 支持的语言: python, golang, javascript, typescript, rust, flutter,\n")
            f.write("#            android, bash, c, cpp, csharp, java, kotlin, swift, php, ruby, markdown\n")
            languages = config.get('languages', {})
            f.write("languages:\n")
            for lang, enabled in languages.items():
                status = "true" if enabled else "false"
                f.write(f"  {lang}: {status}\n")
            f.write("\n")

            f.write("# 索引时排除的文件/目录模式\n")
            exclude_patterns = config.get('exclude_patterns', [])
            f.write("exclude_patterns:\n")
            for pattern in exclude_patterns:
                # 对包含特殊字符的模式使用引号
                if any(c in pattern for c in ['*', '?', '[', ']', '!', ' ', ':', '#', '&']):
                    f.write(f"  - \"{pattern}\"\n")
                else:
                    f.write(f"  - {pattern}\n")
        return True
    except Exception as e:
        console.print(f"[red]错误: 配置文件保存失败: {e}[/red]")
        return False


def scan_project_languages(project_root: Path) -> Dict[str, bool]:
    """扫描项目，检测使用的编程语言

    Args:
        project_root: 项目根目录

    Returns:
        检测到的语言配置字典
    """
    detected_languages = {}

    # 统计各语言的文件数量
    language_counts = {lang: 0 for lang in SUPPORTED_LANGUAGES.keys()}

    try:
        # 扫描项目目录
        for file_path in project_root.rglob("*"):
            if not file_path.is_file():
                continue

            # 跳过常见的忽略目录
            parts = file_path.parts
            if any(part in [".git", ".venv", "venv", "__pycache__", "node_modules",
                       "dist", "build", ".lazygophers"] for part in parts):
                continue

            # 根据扩展名统计语言
            suffix = file_path.suffix
            for lang, extensions in SUPPORTED_LANGUAGES.items():
                if suffix in extensions:
                    language_counts[lang] += 1
                    break
    except Exception as e:
        console.print(f"[dim]警告: 扫描语言时出错: {e}[/dim]")

    # 显示检测结果
    detected_langs = []
    for lang, count in sorted(language_counts.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            detected_langs.append(f"{lang}({count})")
            # 自动启用检测到的语言（只要存在文件就启用）
            detected_languages[lang] = True

    # 禁用未检测到的语言
    for lang in SUPPORTED_LANGUAGES.keys():
        if lang not in detected_languages:
            detected_languages[lang] = False

    # 输出检测结果
    if detected_langs:
        console.print(f"[dim]✓ 检测到语言: {', '.join(detected_langs)}[/dim]")

    return detected_languages


def init_environment(force: bool = False, silent: bool = False) -> bool:
    """初始化语义搜索环境

    Args:
        force: 是否强制重新初始化
        silent: 是否静默模式

    Returns:
        是否初始化成功
    """
    try:
        # 查找项目根目录
        project_root = None
        current = Path.cwd()
        for _ in range(6):
            if (current / ".lazygophers").exists():
                project_root = current
                break
            if (current / ".git").exists():
                pass
            current = current.parent
        else:
            project_root = Path.cwd()

        # 创建数据目录
        data_path = Path(project_root) / DATA_DIR
        data_path.mkdir(parents=True, exist_ok=True)

        # 创建 .lazygophers/.gitignore
        lazygophers_gitignore = Path(project_root) / ".lazygophers" / ".gitignore"
        required_content = [
            "# 忽略插件数据",
            "/ccplugin/semantic/",
        ]

        if not lazygophers_gitignore.exists():
            try:
                lazygophers_gitignore.parent.mkdir(parents=True, exist_ok=True)
                with open(lazygophers_gitignore, "w", encoding="utf-8") as f:
                    for line in required_content:
                        f.write(line + "\n")
                if not silent:
                    console.print(f"[green]✓ 已创建 {lazygophers_gitignore}[/green]")
            except Exception as e:
                if not silent:
                    console.print(f"[dim]无法创建 .gitignore: {e}[/dim]")

        # 创建或加载配置
        # 注意：配置文件只在首次创建时初始化，之后永不自动修改或覆盖
        config_path = data_path / CONFIG_FILE
        if config_path.exists():
            # 配置已存在，加载现有配置（永不修改）
            config = load_config(str(project_root))
            if not silent and force:
                console.print("[dim]注意: 配置文件已存在，保留现有配置（不覆盖）[/dim]")
        else:
            # 首次创建配置，扫描项目语言
            if not silent:
                console.print("[dim]扫描项目文件，检测编程语言...[/dim]")

            detected_languages = scan_project_languages(project_root)
            enabled_langs = [lang for lang, enabled in detected_languages.items() if enabled]

            if not silent and enabled_langs:
                console.print(f"[dim]检测到语言: {', '.join(enabled_langs)}[/dim]")

            # 创建配置，使用检测到的语言
            config = DEFAULT_CONFIG.copy()
            config["languages"] = detected_languages

            save_config(config, str(project_root))

        if not silent:
            console.print(f"[green]✓ 语义搜索环境初始化完成[/green]")
            console.print(f"[dim]  数据目录: {data_path}[/dim]")
            console.print(f"[dim]  配置文件: {config_path}[/dim]")

        return True

    except Exception as e:
        if not silent:
            console.print(f"[red]✗ 初始化失败: {e}[/red]")
        return False


def check_gitignore(project_root: Path = None, silent: bool = False) -> bool:
    """检查并更新 .lazygophers/.gitignore

    Args:
        project_root: 项目根目录路径，如果为 None 则自动查找
        silent: 是否静默模式（不输出信息）

    Returns:
        是否已经正确配置
    """
    # 查找项目根目录
    if project_root is None:
        current = Path.cwd()
        for _ in range(6):
            if (current / ".lazygophers").exists():
                project_root = current
                break
            if (current / ".git").exists():
                pass
            current = current.parent
        else:
            project_root = None

    if not project_root:
        return False

    lazygophers_gitignore = project_root / ".lazygophers" / ".gitignore"

    # 需要添加的内容
    required_content = [
        "# 忽略插件数据",
        "/ccplugin/semantic/",
    ]

    # 检查文件是否存在
    if lazygophers_gitignore.exists():
        # 读取现有内容
        try:
            with open(lazygophers_gitignore, "r", encoding="utf-8") as f:
                existing_lines = [line.strip() for line in f if line.strip()]
        except Exception:
            existing_lines = []

        # 检查是否已包含所需内容
        has_required = all(line in existing_lines for line in required_content)

        if has_required:
            if not silent:
                console.print("[green]✓ Git ignore 配置正确[/green]")
            return True
        else:
            # 追加缺失的内容
            try:
                with open(lazygophers_gitignore, "a", encoding="utf-8") as f:
                    # 确保文件以换行结尾
                    if existing_lines and not existing_lines[-1].endswith("\n"):
                        f.write("\n")
                    # 追加缺失的行
                    for line in required_content:
                        if line not in existing_lines:
                            f.write(line + "\n")
                if not silent:
                    console.print(f"[green]✓ 已更新 {lazygophers_gitignore}[/green]")
                return True
            except Exception as e:
                if not silent:
                    console.print(f"[dim]无法更新 .gitignore: {e}[/dim]")
                return False
    else:
        # 文件不存在，创建新文件
        try:
            lazygophers_gitignore.parent.mkdir(parents=True, exist_ok=True)
            with open(lazygophers_gitignore, "w", encoding="utf-8") as f:
                for line in required_content:
                    f.write(line + "\n")
            if not silent:
                console.print(f"[green]✓ 已创建 {lazygophers_gitignore}[/green]")
            return True
        except Exception as e:
            if not silent:
                console.print(f"[dim]无法创建 .gitignore: {e}[/dim]")
            return False


def check_and_auto_init(silent: bool = False) -> bool:
    """检查并自动初始化 Semantic（由 hooks 调用）

    Args:
        silent: 是否静默模式

    Returns:
        是否初始化成功
    """
    data_path = get_data_path()
    config_path = get_config_path()

    # 检查是否已初始化（config.yaml 存在）
    if not config_path.exists():
        if not silent:
            console.print("[dim]🔧 Semantic 未初始化，正在自动初始化...[/dim]")
        return init_environment(force=False, silent=silent)

    # 检查索引是否存在（lancedb 目录存在且非空）
    lancedb_path = data_path / LANCEDB_DIR
    if not lancedb_path.exists():
        return True  # 已初始化，索引不存在是正常的
    # 检查是否为空目录
    if not any(lancedb_path.iterdir()):
        return True  # 已初始化，空索引是正常的

    return True  # 已初始化且有索引


# ========== CLI 命令 ==========


@app.command()
def init(
    force: bool = typer.Option(False, "--force", "-f", help="强制重新初始化"),
    silent: bool = typer.Option(False, "--silent", "-s", help="静默模式"),
    auto_index: bool = typer.Option(True, "--auto-index/--no-auto-index", help="初始化后自动建立索引"),
):
    """初始化语义搜索环境（内部命令，由 hooks 自动调用）"""
    success = init_environment(force=force, silent=silent)
    if not silent:
        if success:
            check_gitignore(silent=silent)
            console.print("[green]✓ 初始化完成[/green]")
        else:
            raise typer.Exit(1)

    # 自动建立索引（如果需要）
    if success and auto_index:
        data_path = get_data_path()
        lancedb_path = data_path / LANCEDB_DIR

        # 检查索引是否存在
        need_index = not lancedb_path.exists() or not any(lancedb_path.iterdir())

        if need_index:
            if not silent:
                console.print("[dim]正在建立索引...[/dim]")

            # 导入并调用索引功能
            import sys
            # 找到项目根目录以导入 lib 模块
            script_dir = Path(__file__).resolve().parent
            project_root = script_dir.parent.parent.parent
            if not (project_root / 'lib').exists():
                current = script_dir
                for _ in range(5):
                    if (current / 'lib').exists():
                        project_root = current
                        break
                    current = current.parent
            sys.path.insert(0, str(project_root))

            from lib.utils.hybrid_indexer import HybridIndexer

            config_data = load_config()
            indexer = HybridIndexer(config_data, data_path)

            if indexer.initialize():
                # 查找项目根目录
                current = Path.cwd()
                project_root = None
                for _ in range(6):
                    if (current / ".lazygophers").exists():
                        project_root = current
                        break
                    if (current / ".git").exists():
                        pass
                    current = current.parent
                if not project_root:
                    project_root = Path.cwd()

                # 执行索引
                stats = indexer.index_project(project_root, incremental=False)

                if not silent:
                    console.print(f"[green]✓ 索引建立完成: {stats['indexed_files']} 文件, {stats['total_chunks']} 代码块[/green]")

                indexer.close()


@app.command()
def config(
    model: Optional[str] = typer.Option(None, "--model", "-m", help="设置嵌入模型"),
):
    """查看和修改配置"""
    config_data = load_config()

    # 显示当前配置
    console.print("\n[bold cyan]当前配置[/bold cyan]\n")

    # 模型配置
    model_value = config_data.get("embedding_model", "bge-large-en")
    console.print(f"[dim]嵌入模型:[/dim] {model_value}")

    # 硬件加速状态（自动检测）
    console.print(f"[dim]硬件加速:[/dim] 自动检测并启用")

    # 引擎配置
    engines = config_data.get("engines", {})
    console.print(f"\n[bold]引擎配置:[/bold]")
    console.print(f"  [dim]fastembed:[/dim] {'✓ 启用' if engines.get('fastembed', {}).get('enabled') else '✗ 禁用'} ({engines.get('fastembed', {}).get('model', 'N/A')})")
    console.print(f"  [dim]codemodel:[/dim] {'✓ 启用' if engines.get('codemodel', {}).get('enabled') else '✗ 禁用'} ({engines.get('codemodel', {}).get('model', 'N/A')})")
    console.print(f"  [dim]symbols:[/dim] {'✓ 启用' if engines.get('symbols', {}).get('enabled') else '✗ 禁用'}")

    # 检索策略
    strategy = config_data.get("search_strategy", "hybrid")
    console.print(f"\n[bold]检索策略:[/bold] {strategy}")

    # 语言配置
    languages = config_data.get("languages", {})
    enabled_langs = [lang for lang, enabled in languages.items() if enabled]
    console.print(f"\n[bold]启用的语言:[/bold] {', '.join(enabled_langs) if enabled_langs else '无'}")

    # 更新配置
    updated = False

    if model is not None:
        if model in SUPPORTED_MODELS:
            config_data["embedding_model"] = model
            console.print(f"\n[green]✓ 模型已设置为: {model}[/green]")
            updated = True
        else:
            console.print(f"\n[red]错误: 不支持的模型 '{model}'[/red]")
            console.print(f"可用模型: {', '.join(list(SUPPORTED_MODELS.keys())[:10])}...")
            raise typer.Exit(1)

    # 保存配置
    if updated:
        if save_config(config_data):
            console.print("\n[green]✓ 配置已保存[/green]")
        else:
            console.print("\n[red]✗ 配置保存失败[/red]")
            raise typer.Exit(1)


@app.command()
def languages(
    action: str = typer.Argument(..., help="操作: list/enable/disable"),
    language: Optional[str] = typer.Option(None, "--lang", "-l", help="编程语言"),
):
    """管理启用的编程语言"""
    config_data = load_config()
    languages_config = config_data.get("languages", {})

    if action == "list":
        # 列出所有支持的语言
        table = Table(title="支持的编程语言", show_header=True, header_style="bold magenta")
        table.add_column("语言", style="bold")
        table.add_column("状态")
        table.add_column("扩展名")

        for lang, exts in SUPPORTED_LANGUAGES.items():
            enabled = languages_config.get(lang, False)
            status = "[green]✓ 启用[/green]" if enabled else "[dim]✗ 禁用[/dim]"
            table.add_row(lang, status, ", ".join(exts))

        console.print(table)

    elif action in ["enable", "disable"]:
        if language is None:
            console.print("[red]错误: 请指定 --lang 参数[/red]")
            console.print(f"可用语言: {', '.join(SUPPORTED_LANGUAGES.keys())}")
            raise typer.Exit(1)

        if language not in SUPPORTED_LANGUAGES:
            console.print(f"[red]错误: 不支持的语言 '{language}'[/red]")
            console.print(f"可用语言: {', '.join(SUPPORTED_LANGUAGES.keys())}")
            raise typer.Exit(1)

        languages_config[language] = (action == "enable")
        config_data["languages"] = languages_config

        if save_config(config_data):
            status = "启用" if languages_config[language] else "禁用"
            console.print(f"[green]✓ 已{status}语言: {language}[/green]")
        else:
            console.print("[red]✗ 配置保存失败[/red]")
            raise typer.Exit(1)

    else:
        console.print(f"[red]错误: 无效的操作 '{action}'[/red]")
        console.print("可用操作: list, enable, disable")
        raise typer.Exit(1)


@app.command()
def engines(
    action: str = typer.Argument(..., help="操作: list/enable/disable/model/strategy"),
    engine: Optional[str] = typer.Option(None, "--engine", "-e", help="引擎名称"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="模型名称"),
    strategy: Optional[str] = typer.Option(None, "--strategy", "-s", help="检索策略"),
):
    """管理多引擎配置"""
    config_data = load_config()
    engines_config = config_data.get("engines", {})

    if action == "list":
        # 列出所有引擎
        table = Table(title="搜索引擎配置", show_header=True, header_style="bold magenta")
        table.add_column("引擎", style="bold")
        table.add_column("状态")
        table.add_column("模型")
        table.add_column("说明")

        engine_info = {
            "fastembed": {"desc": "快速向量搜索（FastEmbed）", "models": list(EmbeddingGenerator.MODELS.keys())},
            "codemodel": {"desc": "代码专用模型（CodeT5/UniXcoder）", "models": ["codet5+", "unixcoder", "graphcodebert", "codebert"]},
            "symbols": {"desc": "符号索引（函数/类名匹配）", "models": []},
        }

        for eng_name, eng_info in engine_info.items():
            enabled = engines_config.get(eng_name, {}).get("enabled", False)
            status = "[green]✓ 启用[/green]" if enabled else "[dim]✗ 禁用[/dim]"
            current_model = engines_config.get(eng_name, {}).get("model", "N/A")
            table.add_row(eng_name, status, str(current_model), eng_info["desc"])

        console.print(table)

        # 显示当前检索策略
        current_strategy = config_data.get("search_strategy", "fast")
        console.print(f"\n[bold]检索策略:[/bold] {current_strategy}")
        console.print("[dim]可用策略: fast (快速), hybrid (混合), code (代码模型), symbols (符号)[/dim]")

        # 显示融合权重
        if current_strategy == "hybrid":
            weights = config_data.get("fusion_weights", {})
            console.print(f"\n[bold]融合权重:[/bold]")
            console.print(f"  symbols: {weights.get('symbols', 0.3)}")
            console.print(f"  fastembed: {weights.get('fastembed', 0.4)}")
            console.print(f"  codemodel: {weights.get('codemodel', 0.3)}")

    elif action in ["enable", "disable"]:
        if engine is None:
            console.print("[red]错误: 请指定 --engine 参数[/red]")
            console.print("可用引擎: fastembed, codemodel, symbols")
            raise typer.Exit(1)

        if engine not in ["fastembed", "codemodel", "symbols"]:
            console.print(f"[red]错误: 不支持的引擎 '{engine}'[/red]")
            console.print("可用引擎: fastembed, codemodel, symbols")
            raise typer.Exit(1)

        if engine not in engines_config:
            engines_config[engine] = {}
        engines_config[engine]["enabled"] = (action == "enable")
        config_data["engines"] = engines_config

        if save_config(config_data):
            status = "启用" if engines_config[engine]["enabled"] else "禁用"
            console.print(f"[green]✓ 已{status}引擎: {engine}[/green]")
        else:
            console.print("[red]✗ 配置保存失败[/red]")
            raise typer.Exit(1)

    elif action == "model":
        if engine is None:
            console.print("[red]错误: 请指定 --engine 参数[/red]")
            console.print("可用引擎: fastembed, codemodel")
            raise typer.Exit(1)

        if model is None:
            console.print("[red]错误: 请指定 --model 参数[/red]")
            raise typer.Exit(1)

        if engine == "fastembed":
            if model not in EmbeddingGenerator.MODELS:
                console.print(f"[red]错误: 不支持的模型 '{model}'[/red]")
                console.print(f"可用模型: {', '.join(list(EmbeddingGenerator.MODELS.keys())[:10])}...")
                raise typer.Exit(1)
        elif engine == "codemodel":
            if model not in ["codet5+", "unixcoder", "graphcodebert", "codebert"]:
                console.print(f"[red]错误: 不支持的模型 '{model}'[/red]")
                console.print("可用模型: codet5+, unixcoder, graphcodebert, codebert")
                raise typer.Exit(1)
        else:
            console.print(f"[red]错误: '{engine}' 引擎不支持模型选择[/red]")
            raise typer.Exit(1)

        if engine not in engines_config:
            engines_config[engine] = {}
        engines_config[engine]["model"] = model
        config_data["engines"] = engines_config

        if save_config(config_data):
            console.print(f"[green]✓ 已设置 {engine} 模型为: {model}[/green]")
        else:
            console.print("[red]✗ 配置保存失败[/red]")
            raise typer.Exit(1)

    elif action == "strategy":
        if strategy is None:
            console.print("[red]错误: 请指定 --strategy 参数[/red]")
            console.print("可用策略: fast, hybrid, code, symbols")
            raise typer.Exit(1)

        if strategy not in ["fast", "hybrid", "code", "symbols"]:
            console.print(f"[red]错误: 不支持的策略 '{strategy}'[/red]")
            console.print("可用策略: fast, hybrid, code, symbols")
            raise typer.Exit(1)

        config_data["search_strategy"] = strategy

        if save_config(config_data):
            console.print(f"[green]✓ 已设置检索策略为: {strategy}[/green]")
        else:
            console.print("[red]✗ 配置保存失败[/red]")
            raise typer.Exit(1)

    else:
        console.print(f"[red]错误: 无效的操作 '{action}'[/red]")
        console.print("可用操作: list, enable, disable, model, strategy")
        raise typer.Exit(1)


@app.command()
def models():
    """列出支持的嵌入模型"""
    table = Table(title="支持的嵌入模型", show_header=True, header_style="bold magenta")
    table.add_column("模型ID", style="bold")
    table.add_column("模型名称")
    table.add_column("维度")
    table.add_column("说明")

    for model_id, model_info in SUPPORTED_MODELS.items():
        table.add_row(
            model_id,
            model_info["name"],
            str(model_info["dim"]),
            model_info.get("description", ""),
        )

    console.print(table)


@app.command()
def help_command():
    """显示帮助信息"""
    help_md = r"""
# 语义搜索命令 - 混合架构版本

## 配置管理

| 命令 | 说明 | 示例 |
|------|------|------|
| `init` | 初始化环境 | `semantic init` |
| `config` | 查看配置 | `semantic config` |
| `config --model <name>` | 设置嵌入模型 | `semantic config --model bge-large-en` |
| `config --gpu <bool>` | 设置GPU | `semantic config --gpu true` |

## 引擎管理

| 命令 | 说明 | 示例 |
|------|------|------|
| `engines list` | 列出所有引擎 | `semantic engines list` |
| `engines enable --engine <name>` | 启用引擎 | `semantic engines enable --engine codemodel` |
| `engines disable --engine <name>` | 禁用引擎 | `semantic engines disable --engine symbols` |
| `engines model --engine <name> --model <model>` | 设置引擎模型 | `semantic engines model -e fastembed -m gte-large` |
| `engines strategy --strategy <name>` | 设置检索策略 | `semantic engines strategy -s hybrid` |

**可用引擎：**
- `fastembed` - 快速向量搜索（FastEmbed，默认）
- `codemodel` - 代码专用模型搜索（CodeT5/UniXcoder）
- `symbols` - 符号索引（函数/类名精确匹配）

**检索策略：**
- `fast` - 仅使用 FastEmbed 快速搜索
- `hybrid` - 混合搜索（融合所有引擎结果，推荐）
- `code` - 仅使用代码模型搜索
- `symbols` - 仅使用符号索引

## 语言管理

| 命令 | 说明 | 示例 |
|------|------|------|
| `languages list` | 列出语言 | `semantic languages list` |
| `languages enable --lang <name>` | 启用语言 | `semantic languages enable --lang python` |
| `languages disable --lang <name>` | 禁用语言 | `semantic languages disable --lang java` |

## 模型管理

| 命令 | 说明 |
|------|------|
| `models` | 列出支持的嵌入模型 |

## 索引与搜索

| 命令 | 说明 | 示例 |
|------|------|------|
| `index` | 索引代码库 | `semantic index -i` |
| `index --incremental` | 增量索引 | `semantic index -i` |
| `index --force` | 强制重建 | `semantic index -f` |
| `search <query>` | 搜索代码 | `semantic search "函数名"` |
| `search --limit <n>` | 限制结果数 | `semantic search "API" -l 20` |

## 其他

| 命令 | 说明 |
|------|------|
| `help-command` | 显示帮助 |
| `stats` | 显示索引统计 |

## 架构说明

### 混合搜索引擎

本插件采用三层混合架构：

1. **FastEmbed 引擎** - 快速向量搜索
   - 支持多种嵌入模型（BGE、Jina、GTE 等）
   - 基于 ONNX，轻量高效
   - 适用于快速初筛

2. **CodeModel 引擎** - 代码专用搜索
   - 支持 CodeT5、UniXcoder、GraphCodeBERT
   - 基于代码语义理解
   - 适用于精确代码搜索

3. **Symbol 索引** - 符号精确匹配
   - 提取函数、类、变量名
   - 支持 SQLite 全文搜索
   - 适用于快速定位

### 结果融合

混合检索会融合三个引擎的结果：
- 符号匹配权重：30%
- FastEmbed 向量相似度：40%
- CodeModel 语义相似度：30%

## 支持的编程语言

- `python` - Python (.py)
- `golang` - Go (.go)
- `javascript` - JavaScript (.js, .jsx)
- `typescript` - TypeScript (.ts, .tsx)
- `rust` - Rust (.rs)
- `flutter` - Flutter/Dart (.dart)
- `android` - Android (.java, .kt)
- `bash` - Bash (.sh, .bash)
- `c` - C (.c, .h)
- `cpp` - C++ (.cpp, .hpp)
- `csharp` - C# (.cs)
- `java` - Java (.java)
- `kotlin` - Kotlin (.kt)
- `swift` - Swift (.swift)
- `php` - PHP (.php)
- `ruby` - Ruby (.rb)
- `markdown` - Markdown (.md)

## 支持的嵌入模型

### BGE 系列（推荐）
- `bge-small-en` - BAAI bge-small-en-v1.5 (384维, 英文)
- `bge-small-zh` - BAAI bge-small-zh-v1.5 (512维, 中文)
- `bge-base-en` - BAAI bge-base-en-v1.5 (768维, 英文)
- `bge-large-en` - BAAI bge-large-en-v1.5 (1024维, 英文高精度)

### Jina 系列
- `jina-small-en` - Jina v2-small-en (512维)
- `jina-base-en` - Jina v2-base-en (768维)
- `jina-base-de` - Jina v2-base-de (768维, 德语)
- `jina-code` - Jina v2-base-code (768维, 代码)

### Snowflake Arctic 系列
- `arctic-embed-xs` - Arctic XS (384维, 极轻量)
- `arctic-embed-s` - Arctic S (384维, 轻量)
- `arctic-embed-m` - Arctic M (768维, 通用)
- `arctic-embed-m-long` - Arctic M Long (768维, 长文本)
- `arctic-embed-l` - Arctic L (1024维, 高精度)

### Nomic 系列
- `nomic-embed-text` - Nomic v1 (768维)
- `nomic-embed-text-1.5` - Nomic v1.5 (768维)

### Sentence Transformers 系列
- `all-minilm-l6-v2` - MiniLM (384维, 极轻量)
- `paraphrase-multilingual-mpnet` - MPNet (768维, 多语言)

### E5 系列
- `multilingual-e5-small` - E5 small (384维, 多语言)
- `multilingual-e5-large` - E5 large (1024维, 多语言高精度)

### GTE 系列
- `gte-large` - GTE large (1024维)

### MXBAI 系列
- `mxbai-embed-large` - MXBAI large (1024维)

### CLIP 系列
- `clip-vit-b-32` - CLIP ViT-B-32 (512维, 多模态)

## 数据存储

数据目录: `.lazygophers/ccplugin/semantic/`
- `config.yaml` - 配置文件（YAML 格式）
- `lancedb/` - LanceDB 向量数据库
"""
    panel = Panel(help_md, title="帮助信息", border_style="blue")
    console.print(panel)


@app.command()
def index(
    path: Optional[str] = typer.Option(None, "--path", "-p", help="索引目录"),
    incremental: bool = typer.Option(False, "--incremental", "-i", help="增量索引"),
    force: bool = typer.Option(False, "--force", "-f", help="强制重建索引"),
    batch_size: int = typer.Option(100, "--batch-size", "-b", help="批处理大小"),
    silent: bool = typer.Option(False, "--silent", "-s", help="静默模式"),
):
    """索引代码库"""
    import sys
    # 找到项目根目录以导入 lib 模块
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent.parent
    if not (project_root / 'lib').exists():
        current = script_dir
        for _ in range(5):
            if (current / 'lib').exists():
                project_root = current
                break
            current = current.parent
    sys.path.insert(0, str(project_root))

    from lib.database.indexer import CodeIndexer

    # 自动检查并初始化（hooks 调用）
    if not check_and_auto_init(silent=silent):
        raise typer.Exit(1)

    # 加载配置
    config_data = load_config()
    data_path = get_data_path()

    # 确定索引路径
    if path:
        root_path = Path(path).resolve()
    else:
        # 查找项目根目录
        current = Path.cwd()
        for _ in range(6):
            if (current / ".lazygophers").exists():
                root_path = current
                break
            current = current.parent
        else:
            root_path = Path.cwd()

    # 显示配置（非静默模式）
    if not silent:
        console.print(f"\n[bold cyan]代码索引[/bold cyan]")
        console.print(f"[dim]项目路径:[/dim] {root_path}")
        console.print(f"[dim]模型:[/dim] {config_data.get('embedding_model', 'bge-small-en')}")
        console.print()

    # 初始化索引器（使用 LanceDB）
    indexer = CodeIndexer(config_data, data_path)

    if not indexer.initialize():
        console.print("[red]错误: 索引器初始化失败[/red]")
        raise typer.Exit(1)

    # 清空索引（如果强制）
    if force:
        if not silent:
            console.print("[yellow]清空现有索引...[/yellow]")
        indexer.clear()

    # 执行索引
    stats = indexer.index_project(root_path, incremental=incremental, batch_size=batch_size)

    # 显示结果
    if not silent:
        console.print("\n[bold green]✓ 索引完成[/bold green]\n")
        console.print(f"[dim]扫描文件:[/dim] {stats['total_files']}")
        console.print(f"[dim]索引文件:[/dim] {stats['indexed_files']}")
        console.print(f"[dim]代码块数:[/dim] {stats['total_chunks']}")
        console.print(f"[dim]失败文件:[/dim] {stats['failed_files']}")

    # 关闭索引器
    indexer.close()


@app.command()
def search(
    query: str = typer.Argument(..., help="搜索查询"),
    limit: int = typer.Option(10, "--limit", "-l", help="返回结果数量"),
    language: Optional[str] = typer.Option(None, "--lang", help="限定编程语言"),
    threshold: Optional[float] = typer.Option(None, "--threshold", "-t", help="相似度阈值（覆盖配置文件）"),
    context: bool = typer.Option(True, "--context/--no-context", help="显示上下文"),
    hybrid: bool = typer.Option(True, "--hybrid/--vector-only", help="使用混合搜索（向量+关键词）"),
    strategy: str = typer.Option("rrf", "--strategy", "-s", help="混合搜索策略（rrf/linear/max/min）"),
):
    """语义搜索（支持向量搜索和混合搜索）"""
    import sys
    # 找到项目根目录以导入 lib 模块
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent.parent
    if not (project_root / 'lib').exists():
        current = script_dir
        for _ in range(5):
            if (current / 'lib').exists():
                project_root = current
                break
            current = current.parent
    sys.path.insert(0, str(project_root))

    from lib.database.indexer import CodeIndexer
    from lib.search.integrated import IntegratedSearcher

    # 自动检查并初始化（hooks 调用）
    if not check_and_auto_init(silent=False):
        console.print("[red]错误: 初始化失败[/red]")
        raise typer.Exit(1)

    # 加载配置
    config_data = load_config()
    data_path = get_data_path()

    # 从配置文件读取默认阈值
    default_threshold = config_data.get("similarity_threshold", 0.5)
    # 如果命令行未指定阈值，使用配置文件中的值
    if threshold is None:
        threshold = default_threshold

    # 初始化索引器（使用 LanceDB）
    indexer = CodeIndexer(config_data, data_path)

    if not indexer.initialize():
        console.print("[red]错误: 索引器初始化失败[/red]")
        raise typer.Exit(1)

    # 检查索引
    stats = indexer.get_stats()
    if stats.get("total_chunks", 0) == 0:
        console.print("[yellow]警告: 索引为空，请先运行: /semantic index[/yellow]")
        raise typer.Exit(0)

    # 执行搜索
    console.print(f"\n[bold cyan]搜索:[/bold cyan] {query}")
    console.print(f"[dim]相似度阈值:[/dim] {threshold:.2f}")

    search_mode = "混合搜索" if hybrid else "向量搜索"
    console.print(f"[dim]搜索模式:[/dim] {search_mode}")
    if hybrid:
        console.print(f"[dim]融合策略:[/dim] {strategy}\n")
    else:
        console.print()

    # 使用集成搜索器
    if hybrid:
        integrated = IntegratedSearcher(
            vector_searcher=indexer,
            use_bm25=True,
            hybrid_strategy=strategy,
            vector_weight=0.6,
            keyword_weight=0.4,
        )

        # 获取所有已索引的块，构建 BM25 索引
        try:
            # 从存储中获取所有文档
            all_docs = indexer.storage.search(
                query_vector=[0] * 384,  # 虚拟查询向量
                limit=10000,
            )

            # 构建 BM25 索引
            documents = [
                {
                    "id": doc.get("id", ""),
                    "text": doc.get("code", ""),
                    "metadata": {
                        k: v for k, v in doc.items()
                        if k not in ["id", "code", "vector"]
                    },
                }
                for doc in all_docs
            ]

            if documents:
                integrated.build_bm25_index(documents)
                console.print(f"[dim]已构建 BM25 索引：{len(documents)} 个文档[/dim]\n")
        except Exception as e:
            console.print(f"[yellow]警告: 构建 BM25 索引失败：{e}[/yellow]\n")

        # 执行混合搜索
        results = integrated.search(
            query=query,
            limit=limit,
            language=language,
            threshold=threshold,
            use_hybrid=True,
        )
    else:
        # 仅向量搜索
        results = indexer.search(
            query=query,
            limit=limit,
            language=language,
            threshold=threshold,
        )

        # 转换为标准格式
        results = [
            {
                "id": r.get("id", ""),
                "text": r.get("code", ""),
                "file_path": r.get("file_path", ""),
                "start_line": r.get("start_line", 0),
                "end_line": r.get("end_line", 0),
                "code_type": r.get("code_type", ""),
                "name": r.get("name", ""),
                "language": r.get("language", ""),
                "score": r.get("similarity", 0),
            }
            for r in results
        ]

    # 显示结果
    if not results:
        console.print("[yellow]未找到相关代码[/yellow]")
    else:
        # 确定要显示的分数列标签
        score_label = "混合分数" if hybrid else "相似度"

        table = Table(
            title=f"搜索结果 ({len(results)} 条)",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column(score_label, style="cyan", width=10)
        table.add_column("文件", style="green")
        table.add_column("位置", style="blue", width=10)
        table.add_column("类型", width=10)
        table.add_column("名称", style="bold")
        table.add_column("代码")

        for r in results[:limit]:
            score = f"{r.get('score', 0):.2f}"
            file_path = r.get('file_path', '')
            line_info = f"{r.get('start_line', 0)}:{r.get('end_line', 0)}"
            code_type = r.get('code_type', 'block')
            name = r.get('name', '')
            code = r.get('text', '')[:100]

            table.add_row(score, file_path, line_info, code_type, name, code)

        console.print(table)

        # 显示完整代码（如果需要上下文）
        if context and results:
            console.print("\n[bold]详细结果:[/bold]\n")
            for i, r in enumerate(results[:limit], 1):
                console.print(f"[cyan]{i}.[/cyan] [bold]{r.get('file_path', '')}:{r.get('start_line', 0)}[/bold]")
                console.print(f"[dim]分数: {r.get('score', 0):.3f}[/dim]")

                # 混合搜索时显示向量和关键词分数
                if hybrid and r.get('vector_score') is not None:
                    console.print(f"[dim]向量分数: {r.get('vector_score', 0):.3f} | 关键词分数: {r.get('keyword_score', 0):.3f}[/dim]")

                console.print(f"[dim]类型: {r.get('code_type')} | 名称: {r.get('name')}[/dim]")
                console.print(f"\n[bold yellow]代码:[/bold yellow]")
                console.print(r.get('text', '')[:500])
                console.print()

    # 关闭索引器
    indexer.close()


@app.command()
def stats(
    silent: bool = typer.Option(False, "--silent", "-s", help="静默模式"),
):
    """显示索引统计信息"""
    import sys
    # 找到项目根目录以导入 lib 模块
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent.parent
    if not (project_root / 'lib').exists():
        current = script_dir
        for _ in range(5):
            if (current / 'lib').exists():
                project_root = current
                break
            current = current.parent
    sys.path.insert(0, str(project_root))

    from lib.database.indexer import CodeIndexer

    # 自动检查并初始化（hooks 调用）
    if not check_and_auto_init(silent=True):
        return

    # 加载配置
    config_data = load_config()
    data_path = get_data_path()

    # 初始化索引器（使用 LanceDB）
    indexer = CodeIndexer(config_data, data_path)

    if not indexer.initialize():
        if not silent:
            console.print("[red]错误: 索引器初始化失败[/red]")
        raise typer.Exit(1)

    # 获取统计信息
    stats_data = indexer.get_stats()

    if not silent:
        console.print("\n[bold cyan]索引统计[/bold cyan]\n")

        console.print(f"[bold]向量索引 (LanceDB):[/bold]")
        console.print(f"  后端: {stats_data.get('backend', 'lancedb')}")
        console.print(f"  模型: {stats_data.get('model', 'unknown')}")
        console.print(f"  代码块: {stats_data.get('total_chunks', 0)}")

        console.print()

    # 关闭索引器
    indexer.close()


# ========== 主入口 ==========

def main():
    """主入口函数，用于 uvx entry point"""
    app()


if __name__ == "__main__":
    main()
