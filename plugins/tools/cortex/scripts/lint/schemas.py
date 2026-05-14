"""Vault structure schema — 单一 4 子目录布局。

定义:
- root_dirs: 允许的顶层目录
- root_files: 允许的顶层文件
- 其余 vault root 路径 → vault-structure-violation
"""
from __future__ import annotations

from typing import TypedDict


class VaultSchema(TypedDict):
    root_dirs: set[str]
    root_files: set[str]


SCHEMA: VaultSchema = {
    "root_dirs": {
        "_meta",
        "_templates",
        "_assets",
        "知识库",
        "记忆",
        "仪表盘",
        "归档",
        "locales",
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
}


def get_schema(preset: str | None = None) -> VaultSchema:
    """Return single vault schema. `preset` arg kept for back-compat, ignored."""
    return SCHEMA
