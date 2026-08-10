from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from typing import Any

from skeinlib.hooks.util import git_root

PRD_RE = re.compile(r"(?:^|/)\.skein/task/([^/]+)/prd\.md$")
SPEC_RE = re.compile(r"(?:^|/)\.skein/spec/[^/]+/[^/]+/.+\.md$")
SPEC_REQUIRED = ("title", "namespace", "inclusion", "keywords")
SPEC_INCLUSIONS = ("always", "auto", "fileMatch", "manual")


def cmd_fmt(payload: dict[str, Any]) -> int:
    file_path = payload.get("tool_input", {}).get("file_path", "")
    if not file_path:
        return 0
    normalized_path = file_path.replace("\\", "/")
    match = PRD_RE.search(normalized_path)
    if not match:
        return 0
    root = normalized_path[:match.start()] or (payload.get("cwd") or os.getcwd())
    from skeinlib.utils.paths import SKEIN_ENTRY
    try:
        subprocess.run([sys.executable, str(SKEIN_ENTRY), "fmt", match.group(1)], cwd=root,
                       capture_output=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        pass
    return 0


def parse_spec_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    block = text[4:end] if text[3] == "\n" else text[3:end]
    frontmatter: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line or line.startswith((" ", "\t", "-")):
            continue
        key, _, value = line.partition(":")
        frontmatter[key.strip()] = value.strip()
    return frontmatter


def spec_frontmatter_text(text: str) -> str:
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    if end < 0:
        return ""
    return text[4:end] if text[3] == "\n" else text[3:end]


def cmd_spec_meta(payload: dict[str, Any]) -> int:
    file_path = payload.get("tool_input", {}).get("file_path", "")
    if not file_path:
        return 0
    normalized_path = file_path.replace("\\", "/")
    if not SPEC_RE.search(normalized_path):
        return 0
    try:
        with open(file_path, encoding="utf-8") as file:
            text = file.read()
    except OSError:
        return 0
    metadata = parse_spec_frontmatter(text)
    warnings: list[str] = []
    for key in SPEC_REQUIRED:
        value = metadata.get(key, "")
        if key == "keywords" and not value.strip("[] ").strip():
            warnings.append("缺失: keywords")
        elif key != "keywords" and not value:
            warnings.append(f"缺失: {key}")
    frontmatter_text = spec_frontmatter_text(text).lower()
    if metadata.get("inclusion", "") == "fileMatch" and "globs:" not in frontmatter_text and "globs =" not in frontmatter_text:
        warnings.append("缺失: inclusion=fileMatch 时需配置 globs")
    namespace = metadata.get("namespace", "")
    if namespace in ("product", "map") and "anchors:" not in frontmatter_text and "anchors =" not in frontmatter_text:
        warnings.append(f"缺失: namespace={namespace} 时需配置 anchors")
    if warnings:
        short_path = normalized_path.split(".skein/spec/")[-1] if ".skein/spec/" in normalized_path else normalized_path
        context = f"⚠️ spec metadata 检查 ({short_path}):\n  - " + "\n  - ".join(warnings)
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PostToolUse", "additionalContext": context}}))
    return 0


__all__ = ["PRD_RE", "SPEC_RE", "SPEC_REQUIRED", "SPEC_INCLUSIONS",
           "cmd_fmt", "cmd_spec_meta", "parse_spec_frontmatter", "spec_frontmatter_text"]
