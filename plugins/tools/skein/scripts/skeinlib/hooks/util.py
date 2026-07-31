"""hook 子命令的共享零件 —— 只放**多个子命令都要**的东西, 单一子命令用的常量归它自己那个模块。

刻意用 `os.path` 而非 `pathlib`: 这层在每个 prompt 的热路径上, `pathlib` 要 2.5ms, 而 `os`
本就已导入。见 `skeinlib/hooks/__init__.py` 的热路径纪律。
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Optional, cast


def git_root(start: str) -> str:
    """从 start 往上找 .git; 找不到就退回 start 自己 (非 git 目录也得能用)。"""
    d = os.path.abspath(start or ".")
    while True:
        if os.path.isdir(os.path.join(d, ".git")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return os.path.abspath(start or ".")
        d = parent


def load_stdin() -> Optional[dict[str, Any]]:
    """读 harness 喂的 stdin JSON; 非法 JSON → None (调用方据此静默放行)。"""
    try:
        return cast(dict[str, Any], json.load(sys.stdin))
    except (json.JSONDecodeError, ValueError):
        return None
