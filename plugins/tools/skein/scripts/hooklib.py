#!/usr/bin/env python3
"""SKEIN hook 公共工具 — 注入内容的 token 预算守卫 (纯 stdlib)。

所有 SessionStart / PostTool* hook 注入上下文前, 过 budget_guard():
内容超预算 → stderr 警告 "简化内容", 且截断到硬上限, 免不可控 token 膨胀。
token 估算 = 字符数 // 4 (英混中的粗略常数, 宁可高估)。
"""
from __future__ import annotations

import os
import sys
from typing import Any, Optional

CHARS_PER_TOKEN = 4  # 粗略: 1 token ≈ 4 字符 (中英混排偏保守)


def debug_enabled(args: Any = None) -> bool:
    """--debug 开关: 命令行 --debug 或环境变量 SKEIN_DEBUG (非空/非 0/false/no) 任一即开。"""
    if args is not None and getattr(args, "debug", False):
        return True
    return os.environ.get("SKEIN_DEBUG", "").strip().lower() not in ("", "0", "false", "no")


class Debug:
    """--debug 叙事器: 把命令干了什么 (git / 写盘 / 锁 / 状态迁移) 用 rich 美化写 **stderr**。

    stdout 全程保持机器纯净 (list --json / claim --dry-run / board / hookSpecificOutput 等被 AI/hook 消费,
    rich 污染即破契约), 所以一切叙事只走 stderr。rich 不可用则纯文本降级; 未启用则全 no-op。
    """
    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled
        self.c: Optional[Any] = None
        if enabled:
            try:
                from rich.console import Console
                self.c = Console(stderr=True)
            except Exception:
                self.c = None  # rich 缺失 → 纯文本降级

    def log(self, msg: str, style: Optional[str] = None) -> None:
        if not self.enabled:
            return
        if self.c:
            self.c.print(msg, style=style, markup=False, highlight=False)
        else:
            sys.stderr.write(f"{msg}\n")

    def rule(self, title: str) -> None:
        if not self.enabled:
            return
        if self.c:
            self.c.rule(f"[bold cyan]{title}")
        else:
            sys.stderr.write(f"\n──── {title} ────\n")

    def kv(self, mapping: dict[str, Any], title: Optional[str] = None) -> None:
        """键值表 (rich Table, 降级为对齐文本)。"""
        if not self.enabled or not mapping:
            return
        if self.c:
            from rich.table import Table
            t = Table(show_header=False, box=None, title=title, title_justify="left",
                      title_style="dim")
            t.add_column(style="cyan", no_wrap=True)
            t.add_column(overflow="fold")
            for k, v in mapping.items():
                t.add_row(str(k), str(v))
            self.c.print(t)
        else:
            if title:
                sys.stderr.write(f"{title}\n")
            for k, v in mapping.items():
                sys.stderr.write(f"  {k}: {v}\n")


def est_tokens(text: str) -> int:
    return len(text) // CHARS_PER_TOKEN


def budget_guard(text: str, budget_tokens: int, label: str) -> str:
    """内容超 token 预算则 stderr 警告 + 硬截断到预算。返回可注入文本。

    label 用于警告定位 (哪个 hook)。硬截断防 model 忽视软警告后仍膨胀上下文。
    """
    tok = est_tokens(text)
    if tok <= budget_tokens:
        return text
    limit = budget_tokens * CHARS_PER_TOKEN
    sys.stderr.write(
        f"[skein hook:{label}] 注入内容 ~{tok} token > 预算 {budget_tokens} — "
        f"请简化 (core 规则降级 recall / 精简正文), 已硬截断到 {budget_tokens} token\n")
    return text[:limit] + "\n\n… (超预算已截断, 见 stderr)"


if __name__ == "__main__":
    # 自检
    assert est_tokens("a" * 40) == 10
    assert budget_guard("short", 100, "t") == "short"
    long = "x" * 1000
    out = budget_guard(long, 10, "t")  # 预算 10 token = 40 字符
    assert len(out) < len(long) and "截断" in out
    # Debug 未启用 = 全 no-op (不写 stderr, 不抛)
    d0 = Debug(False)
    d0.log("x"); d0.rule("y"); d0.kv({"a": 1})
    assert d0.enabled is False and d0.c is None
    # 启用 = 不抛 (rich 有则用, 无则纯文本降级); 显式关掉环境开关避免干扰断言
    assert debug_enabled(None) in (True, False)
    d1 = Debug(True)
    d1.rule("自检"); d1.log("走一遍"); d1.kv({"k": "v"}, title="参数")
    print("hooklib 自检过")
