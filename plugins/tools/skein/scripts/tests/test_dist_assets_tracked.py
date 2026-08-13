"""dist/ 前端资产完整性检查 — 引用的 _next 资产必须盘上存在。

dist/ 不再入库 (serve 启动时自动编译), 本测试改为验证盘上产物完整性:
HTML/JS/TXT 引用的 _next/static/ 路径都能找到对应文件。
"""
from __future__ import annotations

import re
from pathlib import Path

DIST = Path(__file__).resolve().parents[2] / "assets" / "dist"
REF = re.compile(r"_next/static/[A-Za-z0-9_/.-]+")


def test_referenced_next_assets_exist() -> None:
    refs = set()
    for f in DIST.rglob("*"):
        if f.is_file() and f.suffix in (".html", ".txt", ".js"):
            refs |= {r.rstrip("\\") for r in REF.findall(f.read_text(encoding="utf-8", errors="replace"))}
    assert refs, "dist/ 里没找到任何 _next 引用, 构建产物可能丢了 (跑 `skein serve` 自动编译)"

    missing = [r for r in sorted(refs) if not (DIST / r).is_file()]
    assert not missing, f"dist/ 引用的资产在盘上不存在: {missing}"
