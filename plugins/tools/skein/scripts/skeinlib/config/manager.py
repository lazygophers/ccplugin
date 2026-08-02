"""Config — config.yaml 读写/合并/校验/类型coerce 的统一入口。

消费方不再直接 import _cfg_effective / _cfg_backfill 等散函数, 统一经 Config class 或包级函数。
"""
from __future__ import annotations

from typing import Any

from skeinlib.config.defaults import (
    CFG_LEGACY, CFG_NO_PATH, CONFIG_DEFAULTS,
)
from skeinlib.config.yaml import yaml_load, yaml_dump


def cfg_paths() -> list[str]:
    """CONFIG_DEFAULTS 全部合法路径 (分组键点号展开), config set/展示/校验共用。

    刻意排除 CFG_NO_PATH (hooks): 阶段名自带点号与路径语法冲突; hooks 叶是列表, config set 只处理标量。
    """
    paths: list[str] = []
    for k, v in CONFIG_DEFAULTS.items():
        if k in CFG_NO_PATH:
            continue
        paths.extend(f"{k}.{gk}" for gk in v) if isinstance(v, dict) else paths.append(k)
    return paths


def cfg_effective(raw: dict[str, Any]) -> dict[str, Any]:
    """把磁盘 raw 合并成 CONFIG_DEFAULTS 结构的生效值 (每叶必存在)。
    优先级: 嵌套新键 > 旧扁平键(deprecated fallback) > 默认值。"""
    cfg: dict[str, Any] = {}
    for k, dv in CONFIG_DEFAULTS.items():
        if not isinstance(dv, dict):
            cfg[k] = raw.get(k, dv)
            continue
        group = dict(dv)
        for flat_key, (gk, leaf) in CFG_LEGACY.items():
            if gk == k and flat_key in raw and not isinstance(raw[flat_key], dict):
                group[leaf] = raw[flat_key]
        raw_group = raw.get(k)
        if isinstance(raw_group, dict):
            group.update(raw_group)
        cfg[k] = group
    return cfg


def cfg_backfill(raw: dict[str, Any]) -> dict[str, Any]:
    """回填 raw 中真正缺失的叶用于写盘; 已有旧扁平键的叶不重复加嵌套键。"""
    out = dict(raw)
    for k, dv in CONFIG_DEFAULTS.items():
        if k in CFG_NO_PATH:
            continue
        if not isinstance(dv, dict):
            out.setdefault(k, dv)
            continue
        raw_group = dict(raw[k]) if isinstance(raw.get(k), dict) else {}
        for leaf, lv in dv.items():
            flat_key = next((fk for fk, (gk2, lk2) in CFG_LEGACY.items() if gk2 == k and lk2 == leaf), None)
            if flat_key and flat_key in raw:
                continue
            raw_group.setdefault(leaf, lv)
        if raw_group:
            out[k] = raw_group
    return out


def cfg_get_path(cfg: dict[str, Any], path: str) -> Any:
    node: Any = cfg
    for p in path.split("."):
        node = node[p]
    return node


def cfg_set_path(raw: dict[str, Any], path: str, val: Any) -> dict[str, Any]:
    """按点号 path 把 val 写入 raw 的嵌套结构 (返回新 dict)。"""
    parts = path.split(".")
    out = dict(raw)
    node = out
    for p in parts[:-1]:
        nxt = dict(node[p]) if isinstance(node.get(p), dict) else {}
        node[p] = nxt
        node = nxt
    node[parts[-1]] = val
    return out


def coerce_config(path: str, v: Any) -> Any:
    """按 CONFIG_DEFAULTS 对应叶的类型 coerce v。"""
    d = cfg_get_path(CONFIG_DEFAULTS, path)
    if isinstance(d, bool):
        return str(v).strip().lower() in ("true", "1", "yes", "on")
    if isinstance(d, int):
        return int(v)
    return str(v)
