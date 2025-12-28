"""市场插件配置管理."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class MarketConfig:
    """市场插件配置."""

    # 日志配置
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    # 超时配置
    max_timeout: float = float(os.getenv("MAX_TIMEOUT", "30.0"))

    # 存储配置
    storage_path: str = os.getenv("MARKET_STORAGE_PATH", "./.market_data")
    vector_db_path: str = os.getenv("VECTOR_DB_PATH", "./.market_data/vectordb")
    graph_db_path: str = os.getenv("GRAPH_DB_PATH", "./.market_data/graphdb")

    # 功能开关
    enable_memory: bool = os.getenv("ENABLE_MEMORY", "true").lower() == "true"
    enable_context: bool = os.getenv("ENABLE_CONTEXT", "true").lower() == "true"
    enable_task: bool = os.getenv("ENABLE_TASK", "true").lower() == "true"
    enable_knowledge: bool = os.getenv("ENABLE_KNOWLEDGE", "true").lower() == "true"

    # 外部服务配置
    api_key: Optional[str] = os.getenv("MARKET_API_KEY")

    def validate(self) -> None:
        """验证配置."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level not in valid_levels:
            raise ValueError(f"无效的 log_level: {self.log_level}")

        if self.max_timeout <= 0:
            raise ValueError("max_timeout 必须大于 0")

        # 确保存储路径存在
        os.makedirs(self.storage_path, exist_ok=True)
        os.makedirs(self.vector_db_path, exist_ok=True)
        os.makedirs(self.graph_db_path, exist_ok=True)


# 全局配置实例
config = MarketConfig()
