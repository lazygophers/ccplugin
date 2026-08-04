"""guard hook —— 硬阻直接读写 task.json/task.md + trellis 未初始化迁移门 + fileMatch 注入
(原 guard-skein.py)。

阻断语义: 本 hook 是四个 gate 面里唯一会返回 2 (真阻断) 的 —— 打断的是用户每一次对话。
"""
from __future__ import annotations

import fnmatch
import json
import os
import sys
from pathlib import Path
from typing import Any

from skeinlib.hooks.util import BLOCKED, git_root

GATED = {"Read", "Edit", "Write", "MultiEdit"}


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


# ── guard (原 guard-skein.py) ───────────────────────────────────────────────
def cmd_guard(d: dict[str, Any]) -> int:
    """硬阻直接读写 task.json/task.md + trellis 未初始化迁移门 + fileMatch 注入。"""
    fp = d.get("tool_input", {}).get("file_path", "")
    parts = fp.replace("\\", "/").split("/") if fp else []
    tool_name = d.get("tool_name", "")
    cwd = d.get("cwd") or os.getcwd()

    # A. .skein/ 脚本管理文件硬阻
    #    prd.md 只锁写不锁读: 加锁理由是「章节结构由引擎保证」, 不是保密, 而它本来就是给人读的散文。
    #    task.json / task.md 的读阻是既有行为, 不动 —— 它们的取态另有专门命令, 输出比原文好读。
    if (fp and ".skein" in parts and os.path.basename(fp) in BLOCKED
            and not (os.path.basename(fp) == "prd.md" and tool_name == "Read")):
        print(
            "禁直接读写 .skein/ 的 task.json / task.md / prd.md — 均由 skein CLI 维护。"
            "取态: `skein current` / `list` / `subtask list <id>` / `subtask ready <id>` / "
            "`skein prd read <id> --type <章节>`; "
            "改态: create/confirm/finishing/finish/del/subtask / "
            "`skein prd write|add|check|uncheck <id> --type <章节> --list <内容>`。",
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
                "初始化经 Bash 跑 `skein setup`, 完成后本门自动打开。",
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
