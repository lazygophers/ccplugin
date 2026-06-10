"""router — Increment → memory L0-L4 路径.

按 cortex-schema/references/memory-levels.md 5 级映射 (全部全局, target=$HOME/.cortex):
  L0-core   永久/硬性规则 (KIND_L0, ask)
  L1-long   永久个人偏好 / 校正 (KIND_CORRECTION 高强度)
  L2-mid    中期决策 / 踩坑 (KIND_DECISION / KIND_TIP)
  L3-short  暂时性 (默认 fallback)
  L4-inbox  本路由不直落 (留给 cortex-ingest)

filename slug: kind-yyyymmdd-<8hash>.md (避碰).
"""
from __future__ import annotations

import hashlib
import re

from . import (
    KIND_CORRECTION,
    KIND_DECISION,
    KIND_L0,
    KIND_TIP,
    Increment,
)


# kind → (target_path 后缀, level, reason)
_ROUTE_TABLE = {
    KIND_L0: ("memory/L0-core", 0, "L0 关键词命中, ask 确认"),
    KIND_CORRECTION: ("memory/L1-long", 1, "用户校正 — 偏好类持久记忆"),
    KIND_DECISION: ("memory/L2-mid", 2, "决策语 — 中期沉淀"),
    KIND_TIP: ("memory/L2-mid", 2, "踩坑/教训 — 中期沉淀"),
}


def _slug(inc: Increment) -> str:
    """生成稳定 slug: kind-<8hash>.md."""
    h = hashlib.sha1(f"{inc.session_file}:{inc.line_no}:{inc.text}".encode("utf-8")).hexdigest()[:8]
    safe_kind = re.sub(r"[^a-z0-9-]", "-", inc.kind.lower())
    return f"{safe_kind}-{h}.md"


def route(inc: Increment) -> dict:
    """Increment → plan 条目 dict."""
    route_path, level, reason = _ROUTE_TABLE.get(
        inc.kind, ("memory/L3-short", 3, "默认 fallback")
    )
    return {
        "session_file": inc.session_file,
        "line_no": inc.line_no,
        "kind": inc.kind,
        "summary": inc.summary,
        "target_path": route_path,
        "target_filename": _slug(inc),
        "level": level,
        "reason": reason,
    }


def route_all(incs: list[Increment]) -> list[dict]:
    return [route(i) for i in incs]
