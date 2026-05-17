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
        # AI 工具配置 / 会话状态 (vault 可能同时是 AI 协作 workspace)
        ".claude",
        ".claude-plugin",
        ".codex",
        ".opencode",
        ".cursor",
        ".continue",
        ".windsurf",
        ".trae",
        ".copilot",
        ".sourcegraph",
        ".tabnine",
        ".sweep",
        ".trellis",
        ".smart-env",
    },
    "root_files": {
        "hot.md",
        "index.md",
        "README.md",
        "主页.md",
        "焦点.md",
        # AI 工具项目级文档 (面向人类 + 多 AI 工具, 不应被 lint 误删)
        "CLAUDE.md",
        "AGENTS.md",
        "AGENT.md",
        "CHANGELOG.md",
        "LICENSE",
        "LICENSE.md",
        ".cursorrules",
        ".cursorignore",
        ".windsurfrules",
        ".aider.conf.yml",
        ".gitignore",
        ".gitattributes",
    },
}


def get_schema(preset: str | None = None) -> VaultSchema:
    """Return single vault schema. `preset` arg kept for back-compat, ignored."""
    return SCHEMA
