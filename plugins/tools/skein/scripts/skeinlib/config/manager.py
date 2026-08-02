"""Config — config.yaml 单例 class。

一个 workspace 一个 Config 实例 (单例), 管全部配置读写/合并/校验/coerce。
消费方: `config = Config.get(path)` 或 `config = Config(path)` (同 path 返回同一实例)。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from skeinlib.config.defaults import (
    CFG_LEGACY, CFG_NO_PATH, CONFIG_DEFAULTS,
)
from skeinlib.config.yaml import yaml_load, yaml_dump


class Config:
    """config.yaml 单例 — 一个文件路径对应同一实例。

    职责: 读盘 → 合并默认值 → 缓存生效值; set 写盘+刷缓存。
    不管 hooks 校验 (那是 hooks.py 的事), 不管 YAML 解析 (那是 yaml.py 的事)。
    """
    _instances: dict[str, "Config"] = {}

    def __new__(cls, path: Path) -> "Config":
        key = str(path.resolve())
        if key not in cls._instances:
            cls._instances[key] = super().__new__(cls)
        return cls._instances[key]

    def __init__(self, path: Path) -> None:
        if hasattr(self, "_initialized"):
            return
        self._path = path
        self._raw: dict[str, Any] = {}
        self._cfg: dict[str, Any] = {}
        self._initialized = True
        self.reload()

    @classmethod
    def get(cls, path: Path) -> "Config":
        """显式单例取 (同 __init__, 语义更清晰)。"""
        return cls(path)

    @classmethod
    def _reset(cls) -> None:
        """清全部单例 (测试用)。"""
        cls._instances.clear()

    def reload(self) -> dict[str, Any]:
        """重读盘 → 合并默认值 → 缓存。返回生效配置 dict。"""
        if self._path.exists():
            self._raw = yaml_load(self._path.read_text(encoding="utf-8"))
        else:
            self._raw = {}
        self._cfg = _effective(self._raw)
        return self._cfg

    def raw(self) -> dict[str, Any]:
        """磁盘原始 dict (无默认值合并)。"""
        return dict(self._raw)

    def effective(self) -> dict[str, Any]:
        """生效配置 (默认值 + 盘上 override + 旧扁平 fallback)。"""
        return dict(self._cfg)

    def get_path(self, path: str) -> Any:
        """点号路径取值 (如 worktree.enabled)。"""
        node: Any = self._cfg
        for p in path.split("."):
            node = node[p]
        return node

    def set_path(self, path: str, val: Any) -> None:
        """点号路径设值 → 写盘 → 刷缓存。"""
        self._raw = _set_path(self._raw, path, val)
        self._path.write_text(yaml_dump(self._raw), encoding="utf-8")
        self._cfg = _effective(self._raw)

    def backfill(self) -> dict[str, Any]:
        """回填缺失叶, 返回补全后的 raw (不写盘; 写盘由调用方决定)。"""
        return _backfill(self._raw)

    def hooks(self) -> dict[str, Any]:
        """hooks 配置 (从生效值取)。"""
        return self._cfg.get("hooks", {})


# ---- 包级函数 (Config class 内部用, 也兼容旧消费方 import) ----

def cfg_paths() -> list[str]:
    """CONFIG_DEFAULTS 全部合法路径 (分组键点号展开)。"""
    paths: list[str] = []
    for k, v in CONFIG_DEFAULTS.items():
        if k in CFG_NO_PATH:
            continue
        paths.extend(f"{k}.{gk}" for gk in v) if isinstance(v, dict) else paths.append(k)
    return paths


def _effective(raw: dict[str, Any]) -> dict[str, Any]:
    """合并 raw + CONFIG_DEFAULTS → 生效值 (Config 内部用)。"""
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


def _backfill(raw: dict[str, Any]) -> dict[str, Any]:
    """回填缺失叶 (Config 内部用)。"""
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


def coerce_config(path: str, v: Any) -> Any:
    """按 CONFIG_DEFAULTS 对应叶的类型 coerce v。"""
    d = _get_path(CONFIG_DEFAULTS, path)
    if isinstance(d, bool):
        return str(v).strip().lower() in ("true", "1", "yes", "on")
    if isinstance(d, int):
        return int(v)
    return str(v)


def _get_path(cfg: dict[str, Any], path: str) -> Any:
    node: Any = cfg
    for p in path.split("."):
        node = node[p]
    return node


def _set_path(raw: dict[str, Any], path: str, val: Any) -> dict[str, Any]:
    parts = path.split(".")
    out = dict(raw)
    node = out
    for p in parts[:-1]:
        nxt = dict(node[p]) if isinstance(node.get(p), dict) else {}
        node[p] = nxt
        node = nxt
    node[parts[-1]] = val
    return out
