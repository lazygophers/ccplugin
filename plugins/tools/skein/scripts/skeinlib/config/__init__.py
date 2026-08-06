"""config 包 — Config 读写 class + pydantic 模型定义。

字段类型+范围+默认值定义在 ConfigData (pydantic BaseModel), 含 hooks 结构 (HooksConfig)。
YAML 解析用 PyYAML; 配置结构由 pydantic 校验。
"""
from __future__ import annotations

from skeinlib.config.manager import (
    Config, ConfigData, PoolsConfig, WorktreeConfig, WebConfig, SpecConfig,
    HooksConfig, StageHooks, AgentHooks, HookEntry,
    LEGAL_HOOK_STAGES, HOOK_STAGE_DISPLAY,
)

# CONFIG_DEFAULTS: 从 pydantic model 默认值生成 (单一真值源 = ConfigData Field defaults)
CONFIG_DEFAULTS = ConfigData().model_dump(by_alias=True)

__all__ = [
    "Config",
    "ConfigData", "PoolsConfig", "WorktreeConfig", "WebConfig", "SpecConfig",
    "HooksConfig", "StageHooks", "AgentHooks", "HookEntry",
    "LEGAL_HOOK_STAGES", "HOOK_STAGE_DISPLAY",
    "CONFIG_DEFAULTS",
]
