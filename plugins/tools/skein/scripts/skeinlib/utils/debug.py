"""debug 基础设施 — Debug 单例 + token 预算守卫。

从 hooks/__init__.py 抽出 (ADR 0003 S2): DBG 被 8 处跨层 import, 物理位置不该在 hooks 层。
本模块只依赖 stdlib (rich 是 lazy import), 放在最底层不影响热路径。
"""
from __future__ import annotations

import os
import sys
from typing import Any, Optional


def debug_enabled(args: Any = None) -> bool:
    if args is not None and getattr(args, "debug", False):
        return True
    return os.environ.get("SKEIN_DEBUG", "").strip().lower() not in ("", "0", "false", "no")


class Debug:
    def __init__(self, enabled: bool) -> None:
        self.enabled = False
        self.c: Optional[Any] = None
        self.enable(enabled)

    def enable(self, on: bool) -> None:
        self.enabled = on
        if on and self.c is None:
            try:
                from rich.console import Console
                self.c = Console(stderr=True)
            except Exception:
                self.c = None

    def log(self, message: str, style: Optional[str] = None) -> None:
        if self.enabled:
            self._emit(message, style)

    def warn(self, message: str) -> None:
        self._emit(message, "yellow")

    def error(self, message: str) -> None:
        self._emit(message, "red")

    def _emit(self, message: str, style: Optional[str] = None) -> None:
        if self.c is None:
            try:
                from rich.console import Console
                self.c = Console(stderr=True)
            except Exception:
                pass
        if self.c:
            self.c.print(message, style=style, markup=False, highlight=False)
        else:
            sys.stderr.write(f"{message}\n")

    def rule(self, title: str) -> None:
        if not self.enabled:
            return
        if self.c:
            self.c.rule(f"[bold cyan]{title}")
        else:
            sys.stderr.write(f"\n──── {title} ────\n")

    def kv(self, mapping: dict[str, Any], title: Optional[str] = None) -> None:
        if not self.enabled or not mapping:
            return
        if self.c:
            from rich.table import Table
            table = Table(show_header=False, box=None, title=title, title_justify="left", title_style="dim")
            table.add_column(style="cyan", no_wrap=True)
            table.add_column(overflow="fold")
            for key, value in mapping.items():
                table.add_row(str(key), str(value))
            self.c.print(table)
        else:
            if title:
                sys.stderr.write(f"{title}\n")
            for key, value in mapping.items():
                sys.stderr.write(f"  {key}: {value}\n")


DBG = Debug(False)


def est_tokens(text: str) -> int:
    return len(text) // 4


def budget_guard(text: str, budget_tokens: int, label: str) -> str:
    tokens = est_tokens(text)
    if tokens <= budget_tokens:
        return text
    sys.stderr.write(
        f"[skein hook:{label}] 注入内容 ~{tokens} token > 预算 {budget_tokens} — "
        f"请简化 (core 规则降级 recall / 精简正文), 已硬截断到 {budget_tokens} token\n")
    return text[:budget_tokens * 4] + "\n\n… (超预算已截断, 见 stderr)"
