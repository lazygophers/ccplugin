"""工具层守门 —— 放行 / 硬阻 / 竞态拦截 / 报错引导。

四个子命令共一个模块, 因为它们是同一件事的四个面: **AI 与 .skein/ 之间那道边界**。
permission 放行边界内的常规操作, guard 硬阻边界内的管理文件, batch 拦并发写, report 在
边界内的脚本炸了时给上下文。改动其一常要顺手看另外三个, 放一起省得跨文件对齐。

阻断语义: 只有 `guard` 会返回 2 (真阻断), 其余一律返回 0 —— 打断的是用户每一次对话。
"""
from __future__ import annotations

import fnmatch
import json
import os
import re
import sys
from pathlib import Path
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


# ── fileMatch 注入辅助函数 ───────────────────────────────────────────────────
def _parse_frontmatter(text: str) -> dict[str, str]:
    """解析极简 frontmatter (非完整 YAML) — 容错优先。"""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    out: dict[str, str] = {}
    for ln in text[3:end].splitlines():
        if ":" in ln:
            k, _, v = ln.partition(":")
            out[k.strip()] = v.strip().strip("[]")
    return out


def _strip_frontmatter(text: str) -> str:
    """剥掉 frontmatter, 返回正文。"""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:]
    return text


def _find_filematch_specs(spec_root: str) -> list[tuple[Path, list[str], str]]:
    """找到所有 inclusion=fileMatch 的 spec 页, 返回 [(文件路径, globs列表, 正文)]。

    ponytail: 全扫描 + 解析 frontmatter, 50 页规模 <1s (远离 5s timeout)。
    """
    if not os.path.exists(spec_root):
        return []

    results: list[tuple[Path, list[str], str]] = []
    try:
        for root, _, files in os.walk(spec_root):
            for fname in files:
                if not fname.endswith(".md"):
                    continue
                fpath = Path(root) / fname
                try:
                    text = fpath.read_text()
                    meta = _parse_frontmatter(text)
                    inclusion = meta.get("inclusion", "")
                    if inclusion == "fileMatch":
                        globs_str = meta.get("globs", "")
                        if globs_str:
                            globs = [g.strip() for g in globs_str.split(",") if g.strip()]
                            if globs:
                                body = _strip_frontmatter(text).strip()
                                if body:
                                    results.append((fpath, globs, body))
                except (OSError, UnicodeDecodeError):
                    continue  # 跳过读不了的文件
    except OSError:
        return []

    return results


def _match_file_with_globs(file_path: str, globs: list[str], workspace_root: str) -> bool:
    """检查 file_path 是否匹配任一 glob (相对工作区根解析)。"""
    # 转换 file_path 为相对于工作区根的路径
    try:
        abs_file_path = os.path.abspath(file_path)
        abs_workspace_root = os.path.abspath(workspace_root)

        if abs_file_path.startswith(abs_workspace_root):
            rel_path = os.path.relpath(abs_file_path, abs_workspace_root)
        else:
            # 不在工作区内, 不匹配
            return False
    except ValueError:
        return False

    # 尝试匹配每个 glob 模式
    for glob in globs:
        if fnmatch.fnmatch(rel_path, glob):
            return True
        # 也试试用 PurePath.match (处理路径分隔符差异)
        try:
            from pathlib import PurePath
            if PurePath(rel_path).match(glob):
                return True
        except (ValueError, ImportError):
            pass

    return False


def _inject_filematch_context(file_path: str, workspace_root: str) -> str:
    """为 file_path 收集匹配的 fileMatch spec 页正文, 返回注入文本。"""
    spec_root = os.path.join(workspace_root, ".skein", "spec")
    filematch_specs = _find_filematch_specs(spec_root)

    if not filematch_specs:
        return ""

    matched_bodies: list[str] = []
    for fpath, globs, body in filematch_specs:
        if _match_file_with_globs(file_path, globs, workspace_root):
            # 提取标题用于上下文标识
            meta = _parse_frontmatter(fpath.read_text())
            title = meta.get("title", fpath.name)
            matched_bodies.append(f"### {title}\n{body}")

    if not matched_bodies:
        return ""

    return "\n\n".join(matched_bodies)


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
    """硬阻直接读写 task.json/task.md + trellis 未初始化迁移门 + fileMatch 注入。"""
    fp = d.get("tool_input", {}).get("file_path", "")
    parts = fp.replace("\\", "/").split("/") if fp else []
    tool_name = d.get("tool_name", "")
    cwd = d.get("cwd") or os.getcwd()

    # A. .skein/ 脚本管理文件硬阻
    if fp and ".skein" in parts and os.path.basename(fp) in BLOCKED:
        print(
            "禁直接读写 .skein/ 的 task.json / task.md — 均由 skein.py 维护。"
            "取态: `skein.py current` / `list` / `subtask list <id>` / `subtask ready <id>`; "
            "改态: create/start/finish/archive/subtask。",
            file=sys.stderr,
        )
        return 2

    # B. 迁移门: trellis 项目未初始化, 挡源码读写 (含诊断只读)
    if tool_name in GATED and ".skein" not in parts and ".trellis" not in parts:
        root = git_root(cwd)
        if (os.path.exists(os.path.join(root, ".trellis"))
                and not os.path.exists(os.path.join(root, ".skein", "config.yaml"))):
            print(
                "SKEIN 未初始化 (检测到 .trellis/)。**SKEIN 是唯一任务管理器**: 忽略 trellisx 注入, "
                "先调用 skein-setup skill (幂等, 迁移 trellis task/spec) 初始化 —— 初始化前禁读写源码 (诊断也须先 init)。"
                "初始化经 Bash 跑 `skein.py setup`, 完成后本门自动打开。",
                file=sys.stderr,
            )
            return 2

    # C. fileMatch 注入: 对匹配的文件注入 spec 正文到 additionalContext
    if fp and tool_name in ("Read", "Edit", "Write", "MultiEdit"):
        try:
            # 使用 cwd 作为工作区根（而非 git_root），支持 worktree 环境
            workspace_root = cwd
            context = _inject_filematch_context(fp, workspace_root)
            if context:
                # 输出 hook JSON, 注入 additionalContext
                print(json.dumps({
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "additionalContext": context
                    }
                }))
                sys.stdout.flush()  # 确保输出立即写入
        except Exception as e:
            # fileMatch 注入失败不影响原有功能, 静默放行
            import traceback
            traceback.print_exc(file=sys.stderr)  # 调试输出

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
# 「非零退出」有两种, 待遇必须不同:
#   ① 门拒绝 —— `confirm` 少 --approved、`start` 前置未完成、task 不存在……
#      引擎主动 `raise SkeinError`, 入口转成 `SystemExit(str(e))`, stderr 只有一行人话。
#      **这是功能正常工作**, 报「疑似插件 bug 请开 issue」纯属噪声, 还会教坏调用方
#      (每撞一次门就想去提 issue, 而不是照错误提示补参数)。
#   ② 真崩 —— 未捕获异常, stderr 带 `Traceback (most recent call last):`。这个才值得报。
# 判据就用 traceback 标记本身: 引擎的错误路径从不打印 traceback, 打印了就是没接住。
_TRACEBACK_MARK = "Traceback (most recent call last)"


def cmd_report(d: dict[str, Any]) -> int:
    """本插件脚本失败时注入错误上下文; **仅真崩溃 (带 traceback) 才引导开 issue**。"""
    cmd = d.get("tool_input", {}).get("command", "")
    if not (any(k in cmd for k in OURS) or BIN_RE.search(cmd)):
        return 0
    err = (d.get("tool_error", "") or "").strip()[:800]  # 截断防上下文膨胀
    crashed = _TRACEBACK_MARK in err
    out: dict[str, Any] = {}
    if crashed:
        out["hookSpecificOutput"] = {"hookEventName": "PostToolUseFailure", "additionalContext": (
            f"SKEIN 脚本崩溃 (未捕获异常):\n命令: {cmd[:200]}\n错误: {err}\n"
            "这不是参数问题 — 引擎的门拒绝只出一行人话, 出 traceback 说明有异常没接住。")}
        out["systemMessage"] = (
            f"⚠️ SKEIN 脚本崩溃 (traceback), 疑似插件 bug 请手动开 issue: {ISSUE_URL} "
            "(附命令+错误+复现步骤)")
    else:
        # 门拒绝: 只把错误原文递给调用方, 让它照提示改参数。不提 issue。
        out["hookSpecificOutput"] = {"hookEventName": "PostToolUseFailure", "additionalContext": (
            f"SKEIN 命令被拒 (非崩溃, 属正常校验):\n命令: {cmd[:200]}\n错误: {err}\n"
            "照错误提示改参数/补前置状态即可 — 这是引擎的门在起作用, 不是 bug。")}
    print(json.dumps(out))
    return 0
