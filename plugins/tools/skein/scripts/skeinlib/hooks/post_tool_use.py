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
_SRC_EXT = (".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".rb", ".php",
            ".c", ".cc", ".cpp", ".h", ".hpp", ".swift", ".kt", ".sh")
_TALLY_MAX_AGE = 4 * 3600


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


def cmd_flow_gate(payload: dict[str, Any]) -> int:
    file_path = (payload.get("tool_input", {}) or {}).get("file_path", "")
    if not file_path or not file_path.endswith(_SRC_EXT):
        return 0
    normalized_path = file_path.replace("\\", "/")
    if ".skein/" in normalized_path or "/tests/" in normalized_path or "/test_" in normalized_path:
        return 0
    skein_dir = os.path.join(git_root(payload.get("cwd") or os.getcwd()), ".skein")
    if not os.path.exists(os.path.join(skein_dir, "config.yaml")):
        return 0
    try:
        with open(os.path.join(skein_dir, "task.json"), encoding="utf-8") as file:
            tasks = json.loads(file.read()).get("tasks", [])
        if any(task.get("status") in ("进行中", "检查中") for task in tasks):
            for path in (os.path.join(skein_dir, ".edit-tally"), os.path.join(skein_dir, ".edit-tally.warned")):
                if os.path.exists(path):
                    os.remove(path)
            return 0
    except (OSError, ValueError):
        return 0
    tally_path = os.path.join(skein_dir, ".edit-tally")
    warned_path = os.path.join(skein_dir, ".edit-tally.warned")
    if os.path.exists(warned_path):
        return 0
    # 写衍生物前幂等补 `.skein/.gitignore` (老工作区可能 init 于登记处新增 .edit-tally 之前)
    from pathlib import Path
    from skeinlib.utils.derivatives import ensure_gitignore
    try:
        ensure_gitignore(Path(skein_dir))
    except OSError:
        pass
    import time
    try:
        seen: set[str] = set()
        if os.path.exists(tally_path) and time.time() - os.path.getmtime(tally_path) < _TALLY_MAX_AGE:
            with open(tally_path, encoding="utf-8") as file:
                seen = {line.strip() for line in file if line.strip()}
        seen.add(normalized_path)
        with open(tally_path, "w", encoding="utf-8") as file:
            file.write("\n".join(sorted(seen)))
        if len(seen) < 2:
            return 0
        open(warned_path, "w").close()
    except (OSError, ValueError):
        return 0
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": (
        f"⚠️ 已改动 {len(seen)} 个源码文件但**无 active task** — 跨 ≥2 文件正是 flow 的判据线。\n"
        "若这本该走 flow: 立刻 `skein task create` 建 task, 把已改的纳入首个 subtask, 后续改动在 flow 内做。\n"
        "若确属 inline 豁免 (如同一处改动波及两文件): 忽略本提示, 继续。\n"
        f"已改: {', '.join(sorted(seen)[:5])}")}}))
    return 0


__all__ = ["PRD_RE", "SPEC_RE", "SPEC_REQUIRED", "SPEC_INCLUSIONS", "_SRC_EXT", "_TALLY_MAX_AGE",
           "cmd_flow_gate", "cmd_fmt", "cmd_spec_meta", "parse_spec_frontmatter", "spec_frontmatter_text"]
