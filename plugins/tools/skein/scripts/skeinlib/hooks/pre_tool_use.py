from __future__ import annotations

import fnmatch
import json
import os
import re
import sys
from pathlib import Path, PurePath
from typing import Any

from skeinlib.hooks.util import git_root
from skeinlib.spec.model import INJECTION_BUDGETS
from skeinlib.utils.debug import budget_guard

GATED = {"Read", "Edit", "Write", "MultiEdit"}

# 按段前缀匹配 `git worktree add`: 只拦真执行段, 不误伤 grep/echo 里的字样引用
_WORKTREE_ADD_RE = re.compile(r"^\s*git\s+worktree\s+add\b")


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    frontmatter: dict[str, str] = {}
    for line in text[3:end].splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            frontmatter[key.strip()] = value.strip().strip("[]")
    return frontmatter


def strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:]
    return text


def find_filematch_specs(spec_root: str) -> list[tuple[Any, list[str], str, str]]:
    if not os.path.exists(spec_root):
        return []
    matches: list[tuple[Any, list[str], str, str]] = []
    try:
        for root, _, files in os.walk(spec_root):
            for filename in files:
                if not filename.endswith(".md"):
                    continue
                path = Path(root) / filename
                try:
                    # 曾把这里改成「先读 2KB 头判 inclusion, 命中才补读全文」省全文加载。已回退:
                    # A/B 实测 9 页省 0.02ms、500 页 x 8KB 省 0.3ms (均 <8%, 噪声量级), 瓶颈在
                    # os.walk 的 syscall 不在读内容; 换来的是「frontmatter 超头长即静默漏注入」这个
                    # 新故障面。别再改回去。
                    text = path.read_text()
                    metadata = parse_frontmatter(text)
                    if metadata.get("inclusion", "") != "fileMatch":
                        continue
                    globs = [item.strip() for item in metadata.get("globs", "").split(",") if item.strip()]
                    body = strip_frontmatter(text).strip()
                    if globs and body:
                        title = metadata.get("title", filename)
                        matches.append((path, globs, body, title))
                except (OSError, UnicodeDecodeError):
                    continue
    except OSError:
        return []
    return matches


def file_matches_globs(file_path: str, globs: list[str], workspace_root: str) -> bool:
    try:
        absolute_path = os.path.abspath(file_path)
        absolute_root = os.path.abspath(workspace_root)
        if not absolute_path.startswith(absolute_root):
            return False
        relative_path = os.path.relpath(absolute_path, absolute_root)
    except ValueError:
        return False
    return any(fnmatch.fnmatch(relative_path, glob) or PurePath(relative_path).match(glob) for glob in globs)


def filematch_context(file_path: str, workspace_root: str, session_id: str = "") -> str:
    """globs 命中规则正文注入; 同一 session 第二次命中同一页降级为一行提示 (见上文)。

    session_id 缺省时不做去重 (hook payload 正常都带 session_id)。"""
    absolute_path = os.path.abspath(file_path)
    absolute_root = os.path.abspath(workspace_root)
    if not absolute_path.startswith(absolute_root):
        return ""
    cache_file = Path(workspace_root) / ".skein" / ".cache" / "filematch-injected.json"
    injected: set[str] = set()
    if session_id:
        try:
            injected = set(json.loads(cache_file.read_text()).get(session_id, []))
        except (OSError, ValueError):
            injected = set()
    sections: list[str] = []
    fresh: list[str] = []
    for path, globs, body, title in find_filematch_specs(os.path.join(workspace_root, ".skein", "spec")):
        if file_matches_globs(file_path, globs, workspace_root):
            key = str(path)
            if key in injected:
                sections.append(f"### {title}\n规则 {title} 已注入过, 见上文")
            else:
                sections.append(f"### {title}\n{body}")
                fresh.append(key)
    if session_id and fresh:
        try:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            # 只留当前 session 的记录, 跨 session 的页该重新全文注入
            cache_file.write_text(json.dumps({session_id: sorted(injected | set(fresh))}))
        except OSError:
            pass
    return budget_guard("\n\n".join(sections), INJECTION_BUDGETS["filematch"], "skein-hooks:filematch")


def _deny_worktree_entry(tool_name: str, tool_input: dict[str, Any]) -> bool:
    """拦进入 worktree 的工具调用 — worktree 生命周期 (建/并/销) 全归 skein CLI,
    AI 经 EnterWorktree 或手拼 `git worktree add` 进去 = 绕过追踪的野生改动面。

    Bash 命令按 shell 分隔符拆段, 每段前缀匹配 `git worktree add` —
    grep/echo 引用该字样的只读命令不拦。"""
    if tool_name == "EnterWorktree":
        return True
    if tool_name == "Bash":
        command = str(tool_input.get("command", ""))
        return any(_WORKTREE_ADD_RE.match(seg.strip())
                   for seg in re.split(r"&&|\|\||;|\|", command))
    return False


def cmd_guard(payload: dict[str, Any]) -> int:
    # 曾在此拦「单条 Bash 串 ≥2 个 skein 状态写命令」。已撤: 串接中途失败本就由各命令自身报错,
    # 落盘状态是真值, 重跑照着回显改即可 —— 预防式硬阻反而逼出重试与等待, 净耗 token。
    file_path = payload.get("tool_input", {}).get("file_path", "")
    path_parts = file_path.replace("\\", "/").split("/") if file_path else []
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})
    cwd = payload.get("cwd") or os.getcwd()
    if _deny_worktree_entry(tool_name, tool_input):
        print(
            "禁进入 worktree — 生命周期 (创建/合并/销毁) 归 skein CLI: `skein task confirm/finish` 走配置的 worktree 隔离, 手动进出绕过追踪。",
            file=sys.stderr,
        )
        return 2
    if file_path and ".skein" in path_parts and os.path.basename(file_path) in {"task.json", "task.md", "prd.md"}:
        print(
            """禁直接读写 .skein/ 的 task.json / task.md / prd.md — 均由 skein CLI 维护。
取态: `skein list --status unfinished` / `list` / `subtask list <id>` / `subtask ready <id>` / `skein task spec <id>`;
改态: create/confirm/finishing/finish/del/subtask / `skein task spec <id> --desc ... --should ...`。""",
            file=sys.stderr,
        )
        return 2
    if file_path and tool_name in ("Read", "Edit", "Write", "MultiEdit"):
        try:
            session_id = str(payload.get("session_id", "") or "")
            context = filematch_context(file_path, cwd, session_id)
            if context:
                print(json.dumps({"hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "additionalContext": context
                }}))
                sys.stdout.flush()
        except Exception:
            pass
    return 0

__all__ = ["cmd_guard", "file_matches_globs", "filematch_context", "find_filematch_specs",
           "parse_frontmatter", "strip_frontmatter", "GATED", "_deny_worktree_entry"]
