"""scanner — rglob source-root → jsonl 文件清单.

source-root 默认 ~/.claude/projects/, 内部按 <project-dir>/*.jsonl 组织.
--since 过滤 mtime.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path


def scan(source_root: Path, since: str = "") -> list[Path]:
    """递归扫 *.jsonl, 按 mtime 升序; since 为 YYYY-MM-DD 过滤."""
    if not source_root.is_dir():
        return []
    files = sorted(source_root.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    if since:
        try:
            cutoff = _dt.datetime.strptime(since, "%Y-%m-%d").timestamp()
        except ValueError:
            return files
        files = [p for p in files if p.stat().st_mtime >= cutoff]
    return files
