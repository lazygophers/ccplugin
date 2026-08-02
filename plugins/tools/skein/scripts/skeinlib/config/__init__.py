"""config 包 — YAML 解析 + 默认值 + hooks 校验 + config 操作。

原 config.py 拆为四个子模块:
- yaml.py: mini-YAML 解析器
- defaults.py: CONFIG_DEFAULTS + 常量 + HOOKS_SKELETON
- hooks.py: hooks 结构校验
- manager.py: config 操作函数 (effective/backfill/get/set/coerce)

__init__.py re-export 全部公开 API, 消费方 `from skeinlib.config import X` 零改动兼容。
旧下划线前缀函数名 (如 _yaml_load / _cfg_effective) 保留为 alias, 渐进迁移到无下划线名。
"""
from __future__ import annotations

# YAML 解析器
from skeinlib.config.yaml import (
    yaml_load, yaml_dump, yaml_bad,
    # 兼容旧下划线别名
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
    # 兼容旧下划线别名
    CFG_LEGACY as _CFG_LEGACY,
)

# hooks 校验
from skeinlib.config.hooks import hooks_schema_errors

# config 操作
from skeinlib.config.manager import (
    cfg_paths, cfg_effective, cfg_backfill, cfg_get_path, cfg_set_path, coerce_config,
    # 兼容旧下划线别名
    cfg_paths as _cfg_paths,
    cfg_effective as _cfg_effective,
    cfg_backfill as _cfg_backfill,
    cfg_get_path as _cfg_get_path,
    cfg_set_path as _cfg_set_path,
    coerce_config as _coerce_config,
)

__all__ = [
    # YAML
    "yaml_load", "yaml_dump", "yaml_bad",
    # 默认值
    "CONFIG_DEFAULTS", "STAGE_NAMES", "CFG_REMOTE_DENY", "CFG_NO_PATH",
    "HOOK_SCOPES", "HOOK_WHENS_STAGE", "HOOK_WHENS_AGENT",
    "HOOK_ENTRY_TYPES", "HOOK_ENTRY_FIELDS", "HOOK_ENTRY_REQUIRED",
    "HOOKS_SKELETON", "CFG_LEGACY",
    # hooks 校验
    "hooks_schema_errors",
    # config 操作
    "cfg_paths", "cfg_effective", "cfg_backfill", "cfg_get_path", "cfg_set_path", "coerce_config",
]
