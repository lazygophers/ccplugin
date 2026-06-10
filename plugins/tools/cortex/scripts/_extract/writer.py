"""writer — dry-run / apply 落盘 + 增量游标.

游标: <target>/state/extract-cursor.json
  { "last_processed_mtime": <epoch>, "processed": ["<sha256>", ...] }

apply 行为:
  - 目标目录不存在则创建
  - 写入新文件 (若同名存在追加 .N 后缀, 不覆盖)
  - 原 inbox 文件移到 <wiki>/memory/L4-inbox/_archived/ 保留, 不 delete
  - 游标记录 sha256 + 更新 last_processed_mtime
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .classifier import Entry
from .router import Decision, decide
from .classifier import scan_inbox


CURSOR_REL = "state/extract-cursor.json"
INBOX_REL = ".wiki/memory/L4-inbox"
ARCHIVE_REL = ".wiki/memory/L4-inbox/_archived"


def _load_cursor(target: Path) -> dict[str, Any]:
    p = target / CURSOR_REL
    if not p.exists():
        return {"last_processed_mtime": 0.0, "processed": []}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"last_processed_mtime": 0.0, "processed": []}


def _save_cursor(target: Path, cursor: dict[str, Any]) -> None:
    p = target / CURSOR_REL
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(cursor, ensure_ascii=False, indent=2), encoding="utf-8")


def _unique_path(dir_: Path, filename: str) -> Path:
    out = dir_ / filename
    if not out.exists():
        return out
    stem, _, ext = filename.rpartition(".")
    if not stem:
        stem, ext = filename, ""
    n = 1
    while True:
        cand = dir_ / (f"{stem}.{n}.{ext}" if ext else f"{stem}.{n}")
        if not cand.exists():
            return cand
        n += 1


def _l0_decision(entry: Entry) -> str:
    """L0 ask: env CORTEX_EXTRACT_L0_AUTO ∈ {accept, reject, ask}.
    默认 ask 阻断 (非交互场景必须 explicit env)."""
    mode = os.environ.get("CORTEX_EXTRACT_L0_AUTO", "ask").lower()
    return mode if mode in ("accept", "reject", "ask") else "ask"


def build_plan(target: Path, ignore_cursor: bool = False) -> dict[str, Any]:
    inbox = target / INBOX_REL
    if not inbox.is_dir():
        return {"plan": [], "skipped": [], "error": f"inbox missing: {inbox}"}

    cursor = _load_cursor(target)
    processed: set[str] = set(cursor.get("processed", []) or [])
    last_mtime: float = float(cursor.get("last_processed_mtime", 0.0) or 0.0)

    entries = scan_inbox(inbox)
    plan: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for e in entries:
        if not ignore_cursor and (e.sha256 in processed or e.mtime <= last_mtime):
            skipped.append({"rel": e.rel, "sha256": e.sha256, "reason": "cursor skip"})
            continue
        dec = decide(e)
        plan.append(
            {
                "source": str(e.path),
                "sha256": e.sha256,
                "mtime": e.mtime,
                "weight": e.weight,
                "reuse_count": e.reuse_count,
                "kw_hits": e.kw_hits,
                "target": {
                    "module": dec.module,
                    "level": dec.level,
                    "path": dec.target_path,
                    "filename": dec.target_filename,
                },
                "reason": dec.reason,
                "ask": dec.ask,
                "promote_hint": dec.promote_hint,
            }
        )
    return {"plan": plan, "skipped": skipped}


def apply_plan(target: Path, plan: list[dict[str, Any]]) -> dict[str, Any]:
    wiki = target / ".wiki"
    archive = target / ARCHIVE_REL
    archive.mkdir(parents=True, exist_ok=True)
    cursor = _load_cursor(target)
    processed: list[str] = list(cursor.get("processed", []) or [])
    last_mtime: float = float(cursor.get("last_processed_mtime", 0.0) or 0.0)

    applied: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for item in plan:
        src = Path(item["source"])
        if not src.exists():
            rejected.append({"item": item, "reason": "source missing"})
            continue

        if item.get("ask"):
            mode = _l0_decision_for(item)
            if mode != "accept":
                rejected.append({"item": item, "reason": f"L0 ask → {mode}"})
                continue

        dst_dir = wiki / item["target"]["path"]
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = _unique_path(dst_dir, item["target"]["filename"])
        shutil.copy2(src, dst)

        # archive 原 inbox
        arch = _unique_path(archive, src.name)
        shutil.move(str(src), str(arch))

        applied.append({"source": item["source"], "dest": str(dst), "archived": str(arch)})
        processed.append(item["sha256"])
        last_mtime = max(last_mtime, float(item["mtime"]))

    cursor = {"last_processed_mtime": last_mtime, "processed": processed}
    _save_cursor(target, cursor)
    return {"applied": applied, "rejected": rejected, "cursor": cursor}


def _l0_decision_for(item: dict[str, Any]) -> str:
    return _l0_decision(_FakeEntry(item))


class _FakeEntry:  # 仅为 _l0_decision 接口兼容
    def __init__(self, item: dict[str, Any]) -> None:
        self.item = item
