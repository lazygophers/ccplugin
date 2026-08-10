from __future__ import annotations

import fnmatch
import json
import os
import re
import sys
from pathlib import Path, PurePath
from typing import Any

from skeinlib.hooks.util import git_root

GATED = {"Read", "Edit", "Write", "MultiEdit"}


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


def find_filematch_specs(spec_root: str) -> list[tuple[Any, list[str], str]]:
    if not os.path.exists(spec_root):
        return []
    matches: list[tuple[Any, list[str], str]] = []
    try:
        for root, _, files in os.walk(spec_root):
            for filename in files:
                if not filename.endswith(".md"):
                    continue
                path = Path(root) / filename
                try:
                    text = path.read_text()
                    metadata = parse_frontmatter(text)
                    if metadata.get("inclusion", "") != "fileMatch":
                        continue
                    globs = [item.strip() for item in metadata.get("globs", "").split(",") if item.strip()]
                    body = strip_frontmatter(text).strip()
                    if globs and body:
                        matches.append((path, globs, body))
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


def filematch_context(file_path: str, workspace_root: str) -> str:
    sections: list[str] = []
    for path, globs, body in find_filematch_specs(os.path.join(workspace_root, ".skein", "spec")):
        if file_matches_globs(file_path, globs, workspace_root):
            title = parse_frontmatter(path.read_text()).get("title", path.name)
            sections.append(f"### {title}\n{body}")
    return "\n\n".join(sections)


def cmd_guard(payload: dict[str, Any]) -> int:
    # 曾在此拦「单条 Bash 串 ≥2 个 skein 状态写命令」。已撤: 串接中途失败本就由各命令自身报错,
    # 落盘状态是真值, 重跑照着回显改即可 —— 预防式硬阻反而逼出重试与等待, 净耗 token。
    file_path = payload.get("tool_input", {}).get("file_path", "")
    path_parts = file_path.replace("\\", "/").split("/") if file_path else []
    tool_name = payload.get("tool_name", "")
    cwd = payload.get("cwd") or os.getcwd()
    if (file_path and ".skein" in path_parts and os.path.basename(file_path) in {"task.json", "task.md", "prd.md"}
            and not (os.path.basename(file_path) == "prd.md" and tool_name == "Read")):
        print(
            "禁直接读写 .skein/ 的 task.json / task.md / prd.md — 均由 skein CLI 维护。"
            "取态: `skein list --status open` / `list` / `subtask list <id>` / `subtask ready <id>` / "
            "`skein prd read <id> --type <章节>`; "
            "改态: create/confirm/finishing/finish/del/subtask / "
            "`skein prd write|add|check|uncheck <id> --type <章节> --list <内容>`。",
            file=sys.stderr,
        )
        return 2
    if tool_name in GATED and ".skein" not in path_parts and ".trellis" not in path_parts:
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
    if file_path and tool_name in ("Read", "Edit", "Write", "MultiEdit"):
        try:
            context = filematch_context(file_path, cwd)
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
           "parse_frontmatter", "strip_frontmatter", "GATED"]
