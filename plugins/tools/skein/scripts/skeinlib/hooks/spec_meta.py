"""PostToolUse: spec 页写后校 frontmatter (只 warning)。

共同纪律 (三个 postwrite hook 共守): **永不返回非零**。写已经发生了, 这层再阻断也收不回来,
只会打断用户的 Edit/Write。
"""
from __future__ import annotations

import json
import re
from typing import Any

# ── spec-meta (PostToolUse: spec 文件 metadata 合法性检查) ──────────────────
SPEC_RE = re.compile(r"(?:^|/)\.skein/spec/[^/]+/[^/]+/.+\.md$")
SPEC_REQUIRED = ("title", "namespace", "inclusion", "keywords")
SPEC_INCLUSIONS = ("always", "auto", "fileMatch", "manual")


def _parse_fm(text: str) -> dict[str, str]:
    """简单 YAML frontmatter 解析 (只取顶层 key: value, 无嵌套)。返回 dict 或 {}。"""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    block = text[4:end] if text[3] == "\n" else text[3:end]
    fm: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line or line.startswith((" ", "\t", "-")):
            continue
        k, _, v = line.partition(":")
        fm[k.strip()] = v.strip()
    return fm


def cmd_spec_meta(d: dict[str, Any]) -> int:
    """写 .skein/spec/**/*.md 后检查 frontmatter: 必填缺失 + layer 合法。非阻塞 warning。"""
    fp = d.get("tool_input", {}).get("file_path", "")
    if not fp:
        return 0
    norm = fp.replace("\\", "/")
    if not SPEC_RE.search(norm):
        return 0
    try:
        with open(fp, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return 0
    fm = _parse_fm(text)
    short = norm.split(".skein/spec/")[-1] if ".skein/spec/" in norm else norm
    warns: list[str] = []
    for k in SPEC_REQUIRED:
        v = fm.get(k, "")
        if k == "keywords":
            inner = v.strip("[] ").strip()
            if not inner:
                warns.append("缺失: keywords")
            continue
        if not v:
            warns.append(f"缺失: {k}")
            continue

    # 提取 frontmatter 部分（用于更精确的字段检查）
    fm_text = ""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end >= 0:
            fm_text = text[4:end] if text[3] == "\n" else text[3:end]

    # inclusion:fileMatch 缺 globs 告警
    inclusion = fm.get("inclusion", "")
    if inclusion == "fileMatch":
        # 检查 frontmatter 中是否有 globs 字段（更精确的检查）
        if "globs:" not in fm_text.lower() and "globs =" not in fm_text.lower():
            warns.append("缺失: inclusion=fileMatch 时需配置 globs")

    # namespace:product|map 缺 anchors 告警
    namespace = fm.get("namespace", "")
    if namespace in ("product", "map"):
        # 检查 frontmatter 中是否有 anchors 字段（更精确的检查）
        if "anchors:" not in fm_text.lower() and "anchors =" not in fm_text.lower():
            warns.append(f"缺失: namespace={namespace} 时需配置 anchors")
    if warns:
        ctx = f"⚠️ spec metadata 检查 ({short}):\n  - " + "\n  - ".join(warns)
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PostToolUse", "additionalContext": ctx}}))
    return 0
