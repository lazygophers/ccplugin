"""PostToolUse: prd.md 写后规范化 (幂等)。

共同纪律 (三个 postwrite hook 共守): **永不返回非零**。写已经发生了, 这层再阻断也收不回来,
只会打断用户的 Edit/Write。
"""
from __future__ import annotations

import os
import re
import sys
from typing import Any

# ── fmt (PostToolUse: prd.md 写后规范化) ────────────────────────────────────
PRD_RE = re.compile(r"(?:^|/)\.skein/task/([^/]+)/prd\.md$")


def cmd_fmt(d: dict[str, Any]) -> int:
    """写 .skein/task/<id>/prd.md 后自动跑一次 skein fmt <id> (幂等; python 写回不经工具层 → 不递归)。"""
    fp = d.get("tool_input", {}).get("file_path", "")
    if not fp:
        return 0
    norm = fp.replace("\\", "/")
    m = PRD_RE.search(norm)
    if not m:
        return 0  # 非 prd.md 放行
    tid = m.group(1)
    root = norm[:m.start()] or (d.get("cwd") or os.getcwd())  # .skein 所在仓库根作 cwd
    # 局部 import: 仅本子命令用。paths 拉 pathlib、subprocess 也不轻, 而 dispatch 是懒加载的
    # (cli.py), 所以 permission/user-prompt 那些热子命令根本不会付这份钱。
    import subprocess

    from skeinlib.paths import SKEIN_ENTRY
    try:
        subprocess.run([sys.executable, str(SKEIN_ENTRY), "fmt", tid], cwd=root,
                       capture_output=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        pass  # 非阻塞 hook: fmt 失败不影响写入
    return 0
