"""
Semantic Plugin Configuration Module
语义搜索插件的配置管理
"""

import yaml
from pathlib import Path
from typing import Dict, Optional

# 常量定义
DATA_DIR = ".lazygophers/ccplugin/semantic"
CONFIG_FILE = "config.yaml"

# 默认配置
DEFAULT_CONFIG = {
    "backend": "lancedb",
    "embedding_model": "default",
    "similarity_threshold": 0.5,
    "max_chunk_size": 1024,
    "chunk_overlap": 100,
    "supported_languages": [
        "python", "javascript", "typescript", "go", "rust", "java", "cpp", "c",
        "csharp", "php", "ruby", "swift", "kotlin", "scala", "dart", "vue"
    ]
}


def get_data_path(project_root: Optional[str] = None) -> Path:
    """获取数据目录路径

    Args:
        project_root: 项目根目录，如果为None则自动查找包含.lazygophers的目录

    Returns:
        数据目录的Path对象
    """
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
    """加载配置文件

    Args:
        project_root: 项目根目录，如果为None则自动查找

    Returns:
        配置字典，如果配置文件不存在则返回默认配置
    """
    config_path = get_config_path(project_root)

    if not config_path.exists():
        # 使用默认配置
        return DEFAULT_CONFIG.copy()

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
        # 合并默认配置（处理新增字段）
        merged_config = DEFAULT_CONFIG.copy()
        merged_config.update(config)
        return merged_config
    except Exception as e:
        # 配置文件读取失败时使用默认配置
        return DEFAULT_CONFIG.copy()


__all__ = ["get_data_path", "get_config_path", "load_config", "DEFAULT_CONFIG"]
