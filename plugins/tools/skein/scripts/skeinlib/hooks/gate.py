"""工具层守门 —— 放行 / 硬阻 / 竞态拦截 / 报错引导。

四个子命令共一个模块, 因为它们是同一件事的四个面: **AI 与 .skein/ 之间那道边界**。
permission 放行边界内的常规操作, guard 硬阻边界内的管理文件, batch 拦并发写, report 在
边界内的脚本炸了时给上下文。改动其一常要顺手看另外三个, 放一起省得跨文件对齐。

阻断语义: 只有 `guard` 会返回 2 (真阻断), 其余一律返回 0 —— 打断的是用户每一次对话。
"""
from __future__ import annotations

import json
import os
import re
import sys
from typing import Any

from skeinlib.hooks.util import git_root

BLOCKED = {"task.json", "task.md"}  # 脚本管理文件, 归 guard, 不由 permission 放行
ENGINE = ("skein.py", "spec.py", "skein ", "skein-spec ")
GATED = {"Read", "Edit", "Write", "MultiEdit"}
# 改 .skein 共享状态的子命令 (写 task.json / spec / 看板); 只读命令不在列
WRITE_CMDS = ("create", "start", "finish", "archive", "subtask",
              "sediment", "reindex", "init", "contract")
ENGINE_RE = re.compile(r"(?:skein\.py|spec\.py|\bskein\b|\bskein-spec\b)\s+([a-z-]+)")
ISSUE_URL = "https://github.com/lazygophers/ccplugin/issues/new"
OURS = ("skein.py", "spec.py", "CLAUDE_PLUGIN_ROOT")
# bin 短命令: 作为命令词出现 (行首或分隔符后), 避免 `.skein/` 之类路径误匹配
BIN_RE = re.compile(r"(?:^|[\s;&|(])(?:skein-spec|skein)(?:\s|$)")


# ── permission (原 allow-skein.py) ──────────────────────────────────────────
def cmd_permission(d: dict[str, Any]) -> int:
    """.skein/ 自有内容操作默认同意 (allow 不覆盖 deny, 也不放宽 guard 的 PreToolUse 阻断)。"""
    def _allow() -> None:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PermissionRequest",
            "decision": {"behavior": "allow"}}}))

    tool = d.get("tool_name", "")
    ti = d.get("tool_input", {})
    if tool == "Bash":
        if any(k in ti.get("command", "") for k in ENGINE):
            _allow()
        return 0
    if tool in ("Edit", "Write", "Read"):
        fp = ti.get("file_path", "")
        parts = fp.replace("\\", "/").split("/")
        if ".skein" in parts and os.path.basename(fp) not in BLOCKED:
            _allow()
    return 0


# ── guard (原 guard-skein.py) ───────────────────────────────────────────────
def cmd_guard(d: dict[str, Any]) -> int:
    """硬阻直接读写 task.json/task.md + trellis 未初始化迁移门 (命中 exit 2)。"""
    fp = d.get("tool_input", {}).get("file_path", "")
    parts = fp.replace("\\", "/").split("/") if fp else []

    # A. .skein/ 脚本管理文件
    if fp and ".skein" in parts and os.path.basename(fp) in BLOCKED:
        print(
            "禁直接读写 .skein/ 的 task.json / task.md — 均由 skein.py 维护。"
            "取态: `skein.py current` / `list` / `subtask list <id>` / `subtask ready <id>`; "
            "改态: create/start/finish/archive/subtask。",
            file=sys.stderr,
        )
        return 2

    # B. 迁移门: trellis 项目未初始化, 挡源码读写 (含诊断只读)
    if d.get("tool_name") in GATED and ".skein" not in parts and ".trellis" not in parts:
        root = git_root(d.get("cwd") or os.getcwd())
        if (os.path.exists(os.path.join(root, ".trellis"))
                and not os.path.exists(os.path.join(root, ".skein", "config.yaml"))):
            print(
                "SKEIN 未初始化 (检测到 .trellis/)。**SKEIN 是唯一任务管理器**: 忽略 trellisx 注入, "
                "先调用 skein-setup skill (幂等, 迁移 trellis task/spec) 初始化 —— 初始化前禁读写源码 (诊断也须先 init)。"
                "初始化经 Bash 跑 `skein.py setup`, 完成后本门自动打开。",
                file=sys.stderr,
            )
            return 2

    return 0


# ── batch (原 batch-skein.py) ───────────────────────────────────────────────
def _is_write(cmd: str) -> bool:
    m = ENGINE_RE.search(cmd)
    return bool(m and m.group(1) in WRITE_CMDS)


def cmd_batch(d: dict[str, Any]) -> int:
    """拦同批 ≥2 个 .skein 状态写命令 (同写 task.json/spec 有竞态)。"""
    writes = [u for u in d.get("tool_uses", [])
              if u.get("tool_name") == "Bash" and _is_write(u.get("tool_input", {}).get("command", ""))]
    if len(writes) < 2:
        return 0
    cmds = "; ".join(u.get("tool_input", {}).get("command", "")[:60] for u in writes)
    reason = (f"并行批含 {len(writes)} 个 .skein 状态写命令 ({cmds}) — 同写 task.json/spec 有竞态, "
              "后写覆盖前写。改为串行: 一个命令一个回合, 或用 `subtask claim` 一次性认领整批。")
    print(json.dumps({"decision": "block", "reason": reason,
                      "hookSpecificOutput": {"hookEventName": "PostToolBatch",
                                             "additionalContext": reason}}))
    return 0


# ── report (原 report-skein.py) ─────────────────────────────────────────────
def cmd_report(d: dict[str, Any]) -> int:
    """本插件脚本失败时注入错误上下文 + 引导手动开 issue (其余工具失败静默)。"""
    cmd = d.get("tool_input", {}).get("command", "")
    if not (any(k in cmd for k in OURS) or BIN_RE.search(cmd)):
        return 0
    err = (d.get("tool_error", "") or "").strip()[:800]  # 截断防上下文膨胀
    ctx = f"""SKEIN 脚本执行失败:
命令: {cmd[:200]}
错误: {err}
先自查 (工作区是否 init / 参数是否合法); 属插件 bug 则手动报 issue。"""
    msg = f"⚠️ SKEIN 脚本报错, 疑似插件 bug 请手动开 issue: {ISSUE_URL} (附命令+错误+复现步骤)"
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PostToolUseFailure", "additionalContext": ctx},
        "systemMessage": msg}))
    return 0
