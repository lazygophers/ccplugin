"""dist/ 前端资产必须全部进 git — 否则 marketplace 装出来的包缺 _next chunks, 页面 404。

根 .gitignore 有全局 `dist/` 规则, 曾把 assets/dist/_next/ 整个吞掉 (只剩 2 个 force-add 的文件)。
本地跑 serve 看不出来 (文件在盘上), 只有安装到 marketplace 才炸 → 用测试兜住。
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

DIST = Path(__file__).resolve().parents[2] / "assets" / "dist"
REF = re.compile(r"_next/static/[A-Za-z0-9_/.-]+")


def _tracked() -> set[str]:
    out = subprocess.run(["git", "ls-files", "--full-name", "--", str(DIST)],
                         cwd=str(DIST), capture_output=True, text=True, check=True).stdout
    return {line for line in out.splitlines() if line}


def test_referenced_next_assets_exist_and_tracked() -> None:
    refs = set()
    for f in DIST.rglob("*"):
        if f.is_file() and f.suffix in (".html", ".txt", ".js"):
            refs |= {r.rstrip("\\") for r in REF.findall(f.read_text(encoding="utf-8", errors="replace"))}
    assert refs, "dist/ 里没找到任何 _next 引用, 构建产物可能丢了"

    repo_root = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=str(DIST),
                                    capture_output=True, text=True, check=True).stdout.strip())
    tracked = _tracked()
    missing = [r for r in sorted(refs) if not (DIST / r).is_file()]
    untracked = [r for r in sorted(refs)
                 if (DIST / r).is_file() and str((DIST / r).relative_to(repo_root)) not in tracked]
    assert not missing, f"dist/ 引用的资产在盘上不存在: {missing}"
    assert not untracked, f"dist/ 资产没进 git (会导致安装后 404): {untracked}"
