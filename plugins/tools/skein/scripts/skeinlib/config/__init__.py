"""config 包 — YAML 解析 + 默认值 + hooks 校验 + Config 单例 class。

四个子模块:
- yaml.py: mini-YAML 解析器
- defaults.py: CONFIG_DEFAULTS + 常量 + HOOKS_SKELETON
- hooks.py: hooks 结构校验
- manager.py: Config 单例 class + 包级兼容函数

消费方推荐: `from skeinlib.config import Config` → `Config(path).effective()`。
旧 `from skeinlib.config import _yaml_load, _cfg_effective` 等仍兼容 (alias)。
"""
from __future__ import annotations

# YAML 解析器
from skeinlib.config.yaml import (
    yaml_load, yaml_dump, yaml_bad,
    yaml_load as _yaml_load,
    yaml_dump as _yaml_dump,
)

# 默认值 + 常量
from skeinlib.config.defaults import (
    CONFIG_DEFAULTS, STAGE_NAMES, CFG_REMOTE_DENY, CFG_NO_PATH,
    HOOK_SCOPES, HOOK_WHENS_STAGE, HOOK_WHENS_AGENT,
    HOOK_ENTRY_TYPES, HOOK_ENTRY_FIELDS, HOOK_ENTRY_REQUIRED,
    HOOKS_SKELETON,
    CFG_LEGACY,
    CFG_LEGACY as _CFG_LEGACY,
)

# hooks 校验
from skeinlib.config.hooks import hooks_schema_errors

# Config 单例 class + 兼容函数
from skeinlib.config.manager import (
    Config,
    cfg_paths, coerce_config,
    cfg_paths as _cfg_paths,
    coerce_config as _coerce_config,
)

# 旧散函数兼容 — 消费方渐进迁移到 Config class
from skeinlib.config.manager import _effective as _cfg_effective, _backfill as _cfg_backfill, _get_path as _cfg_get_path, _set_path as _cfg_set_path

__all__ = [
    # Config class (推荐用法)
    "Config",
    # YAML
    "yaml_load", "yaml_dump", "yaml_bad",
    # 默认值
    "CONFIG_DEFAULTS", "STAGE_NAMES", "CFG_REMOTE_DENY", "CFG_NO_PATH",
    "HOOK_SCOPES", "HOOK_WHENS_STAGE", "HOOK_WHENS_AGENT",
    "HOOK_ENTRY_TYPES", "HOOK_ENTRY_FIELDS", "HOOK_ENTRY_REQUIRED",
    "HOOKS_SKELETON", "CFG_LEGACY",
    # hooks 校验
    "hooks_schema_errors",
    # 包级函数
    "cfg_paths", "coerce_config",
]
