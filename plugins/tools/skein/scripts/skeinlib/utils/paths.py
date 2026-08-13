"""路径基准 — 单一真值源。

拆包时踩过两次: 代码从 `scripts/skein.py` 搬进 `scripts/skeinlib/*.py`, 所有
`Path(__file__).parent` 静默深了一层 —— 表现是 `setup` 找不到 spec.py、serve 找不到前端资产,
而单测全绿 (那些路径只在真跑命令时才解析)。所以基准只在这里算一次, 别处一律引用这些常量,
**禁再写 `__file__` 推路径**。

单独一个文件而不是放 `skeinlib/__init__.py`: 那里必须零 import (热路径, 见其 docstring)。
"""
from __future__ import annotations

from pathlib import Path

# ── 路径基准 (单一真值源) ──────────────────────────────────────────────────────
# 本文件位于 skeinlib/utils/paths.py:
#   Path(__file__).resolve().parent          = skeinlib/utils/
#   .parent                                  = skeinlib/
#   .parent.parent                           = scripts/
SCRIPTS_DIR: Path = Path(__file__).resolve().parent.parent.parent  # scripts/
PLUGIN_ROOT: Path = SCRIPTS_DIR.parent                            # 插件根 (assets/ requirements.txt 在此)
SKEIN_ENTRY: Path = SCRIPTS_DIR / "skein.py"                     # CLI 入口 (自我 re-exec 用)
SPEC_ENTRY: Path = SCRIPTS_DIR / "spec.py"
