"""exec 命令白名单 — 严格 enum → 固定 argv (绝不 shell 拼串)。

从 boardsource.py BoardSourceMixin._exec_argv 抽出 (ADR 0003 S3/G2):
属性分析证明此函数零 self 依赖, 是纯函数, 不该挂在 mixin 上。
"""
from __future__ import annotations

import sys
from typing import Any, Optional, cast

from skeinlib.utils.paths import SKEIN_ENTRY


def exec_argv(body: dict[str, Any]) -> Optional[list[str]]:
    """返回 argv 或 None(拒绝)。纯函数, 不读 self。"""
    cmd = body.get("cmd")
    base = [sys.executable, str(SKEIN_ENTRY)]

    def s(k: str) -> Optional[str]:
        v = body.get(k)
        return v.strip() if isinstance(v, str) and v.strip() else None

    def g(k: str) -> str:
        return cast(str, s(k))

    if cmd == "list":
        argv = ["list", "--json"]
        return base + (argv + ["--status", g("status")] if s("status") else argv)
    if cmd == "ready":
        return base + ["ready"]
    if cmd == "doctor":
        return base + ["doctor"]
    if cmd == "status":
        if not s("id"):
            return None
        argv = ["status", g("id")] + ([g("sid")] if s("sid") else []) + ["--json"]
        return base + argv
    if cmd == "subtask-list":
        return base + ["subtask", "list", g("id")] if s("id") else None
    if cmd == "create":
        if not (s("id") and s("name") and s("desc")):
            return None
        argv = ["task", "create", g("id"), "--name", g("name"), "--desc", g("desc")]
        return base + (argv + ["--deps", g("deps")] if s("deps") else argv)
    if cmd == "subtask-add":
        if not (s("id") and s("sid") and s("name") and s("desc") and s("estimate")):
            return None
        argv = ["subtask", "add", g("id"), g("sid"), "--name", g("name"), "--desc", g("desc"),
                "--estimate", g("estimate")]
        if s("deps"):
            argv += ["--deps", g("deps")]
        return base + argv
    if cmd == "clean":
        days = body.get("days", 0)
        if isinstance(days, bool) or not isinstance(days, (int, str)):
            return None
        try:
            d = int(days)
        except ValueError:
            return None
        return base + ["clean", "--days", str(d)] if d >= 0 else None
    force = ["--force"] if body.get("force") is True else []
    if cmd == "confirm":
        return base + ["task", "confirm", g("id"), "--approved"] + force if s("id") else None
    if cmd == "revert":
        return base + ["task", "revert", g("id")] if s("id") else None
    if cmd == "finish":
        return base + ["task", "finish", g("id")] + force if s("id") else None
    if cmd == "priority":
        return base + ["task", "priority", g("id"), "--set", g("set")] if (s("id") and s("set")) else None
    if cmd == "del":
        return base + ["del", g("id")] + force if s("id") else None
    if cmd == "prd":
        if not (s("id") and s("type") and s("action")):
            return None
        act = g("action")
        if act not in ("read", "write", "add", "check", "uncheck"):
            return None
        argv = ["prd", act, g("id"), "--type", g("type")]
        if act != "read":
            raw_list = body.get("list")
            if not isinstance(raw_list, str):
                return None
            # write 空串 = 整章清空 (web 端删光条目要能落盘); 其余 action 空 list 无意义照旧拒
            if act != "write" and not raw_list.strip():
                return None
            argv += ["--list", raw_list]
        return base + argv
    return None
