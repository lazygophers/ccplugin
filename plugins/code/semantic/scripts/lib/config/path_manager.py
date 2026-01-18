"""
Path Manager - 项目路径和配置管理

提供以下功能：
1. get_data_path() - 获取项目数据目录（.lazygophers/ccplugin/[plugin_name]）
2. get_config_path() - 获取配置文件路径
3. load_config() - 加载YAML配置文件，支持默认值回退

用途：
- 所有插件都需要存储数据和配置
- 自动向上查找项目根目录中的 .lazygophers 标记
- 支持多插件独立的数据目录

使用示例：
    from lib.config import get_data_path, load_config

    # 获取当前插件的数据目录
    data_path = get_data_path()

    # 加载配置（无文件时返回默认配置）
    config = load_config()
"""

import yaml
from pathlib import Path
from typing import Dict, Optional

# 常量定义
DATA_DIR = ".lazygophers/ccplugin/semantic"
CONFIG_FILE = "config.yaml"

# 默认配置（可被具体插件覆盖）
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

    从项目根目录（包含 .lazygophers 的目录）下获取数据存储路径。
    如果未指定项目根目录，将自动向上查找。

    Args:
        project_root: 项目根目录。如果为 None，将自动向上查找包含 .lazygophers 的目录

    Returns:
        Path: 数据目录的 Path 对象

    示例：
        >>> data_path = get_data_path()
        >>> # 返回: /path/to/project/.lazygophers/ccplugin/semantic

        >>> data_path = get_data_path("/custom/project")
        >>> # 返回: /custom/project/.lazygophers/ccplugin/semantic
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
    """获取配置文件路径

    Args:
        project_root: 项目根目录

    Returns:
        Path: 配置文件的完整路径

    示例：
        >>> config_path = get_config_path()
        >>> # 返回: /path/to/project/.lazygophers/ccplugin/semantic/config.yaml
    """
    return get_data_path(project_root) / CONFIG_FILE


def load_config(project_root: Optional[str] = None) -> Dict:
    """加载配置文件

    从 YAML 配置文件加载配置。如果文件不存在或读取失败，
    返回默认配置。支持配置文件增量覆盖默认配置。

    Args:
        project_root: 项目根目录，如果为 None 则自动查找

    Returns:
        Dict: 合并后的配置字典
              - 基础配置来自 DEFAULT_CONFIG
              - 被配置文件中的值覆盖
              - 如果文件不存在，返回 DEFAULT_CONFIG

    示例：
        >>> config = load_config()
        >>> embedding_model = config.get('embedding_model')
        >>> threshold = config.get('similarity_threshold', 0.5)
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


__all__ = [
    "get_data_path",
    "get_config_path",
    "load_config",
    "DEFAULT_CONFIG",
]
