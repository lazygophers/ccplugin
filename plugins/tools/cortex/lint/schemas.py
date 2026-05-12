"""Vault structure schemas per preset.

Each schema defines:
- root_dirs: allowed top-level directories
- root_files: allowed top-level files
- All other paths at vault root → vault-structure-violation

Preset key lookup is case-insensitive. Unknown presets fall back to LYT.
"""
from __future__ import annotations

from typing import TypedDict


class VaultSchema(TypedDict):
    root_dirs: set[str]
    root_files: set[str]


SCHEMAS: dict[str, VaultSchema] = {
    "LYT": {
        "root_dirs": {
            "_meta",
            "_templates",
            "_assets",
            # 双 namespace 顶层
            "知识库",
            "记忆体系",
            "仪表盘",
            "归档",
            "folds",
            "log",
            "locales",
            "sessions",
            ".obsidian",
            ".trash",
            ".git",
        },
        "root_files": {
            "hot.md",
            "index.md",
            "README.md",
            "主页.md",
            "焦点.md",
        },
    },
    "PARA": {
        "root_dirs": {
            "_meta",
            "_templates",
            "1_projects",
            "2_areas",
            "3_resources",
            "4_archives",
            "log",
            "folds",
            "locales",
            "sessions",
            ".obsidian",
            ".trash",
            ".git",
        },
        "root_files": {"hot.md", "index.md", "README.md"},
    },
    "flat": {
        "root_dirs": {
            "_meta",
            "_templates",
            "concepts",
            "domains",
            "log",
            "folds",
            "locales",
            "sessions",
            ".archive",
            ".obsidian",
            ".trash",
            ".git",
        },
        "root_files": {"hot.md", "index.md", "README.md"},
    },
}


def get_schema(preset: str | None) -> VaultSchema:
    """Return schema for preset (case-insensitive). Fallback: LYT."""
    if not preset:
        return SCHEMAS["LYT"]
    # Case-insensitive lookup
    key_map = {k.lower(): k for k in SCHEMAS}
    real = key_map.get(preset.lower())
    if real is None:
        return SCHEMAS["LYT"]
    return SCHEMAS[real]
