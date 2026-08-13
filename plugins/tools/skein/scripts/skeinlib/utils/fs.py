"""文件系统与 IO 工具函数 — 从 hooks/__init__.py 抽出。"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Optional, cast


def git_root(start: str) -> str:
    directory = os.path.abspath(start or ".")
    while True:
        if os.path.isdir(os.path.join(directory, ".git")):
            return directory
        parent = os.path.dirname(directory)
        if parent == directory:
            return os.path.abspath(start or ".")
        directory = parent


def load_stdin() -> Optional[dict[str, Any]]:
    try:
        return cast(dict[str, Any], json.load(sys.stdin))
    except (json.JSONDecodeError, ValueError):
        return None


def prefix_lines(tag: str, text: str) -> str:
    return "".join(f"{tag} {line}\n" for line in text.splitlines())
