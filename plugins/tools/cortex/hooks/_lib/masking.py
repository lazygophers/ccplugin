#!/usr/bin/env python3
"""masking.py — cortex P0 安全过滤: secret 脱敏。

纯函数, 纯 stdlib。被 cortex-ingest / cortex-save / save_session.py 前置调用。

CLI:
    python3 masking.py < input > output   # stderr 打 hit 计数

API:
    mask(text) -> (masked_text, hit_list)
        hit_list: 命中的规则名列表 (不含原始 secret 值)。
"""

from __future__ import annotations

import os
import re
import sys
from typing import List, Tuple

# 规则表: (name, compiled_pattern, replacement)
# 命中规则只记 name, 严禁原值入日志。
_RULES: list[tuple[str, "re.Pattern[str]", str]] = [
    (
        "aws_akid",
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        "<REDACTED:aws_akid>",
    ),
    (
        "anthropic_key",  # 必须在 openai_key 之前匹配, 因为 sk-ant-... 也以 sk- 开头
        re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}\b"),
        "<REDACTED:anthropic_key>",
    ),
    (
        "openai_key",
        re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
        "<REDACTED:openai_key>",
    ),
    (
        "github_pat",
        re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"),
        "<REDACTED:github_pat>",
    ),
    (
        "jwt",
        re.compile(r"\beyJ[A-Za-z0-9_\-]+\.eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\b"),
        "<REDACTED:jwt>",
    ),
    (
        "pem_priv",
        re.compile(
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]+?-----END [A-Z ]*PRIVATE KEY-----"
        ),
        "<REDACTED:pem_priv>",
    ),
    (
        "slack_token",
        re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}\b"),
        "<REDACTED:slack_token>",
    ),
]


def mask(text: str) -> Tuple[str, List[str]]:
    """脱敏 text, 返回 (masked, hits)。

    hits 仅含规则名 (重复命中重复记一次), 不含原值。
    """
    if os.environ.get("CORTEX_SKIP_SANITIZE") == "1":
        return text, []
    hits: list[str] = []
    out = text
    for name, pat, repl in _RULES:
        new, n = pat.subn(repl, out)
        if n > 0:
            hits.extend([name] * n)
            out = new
    return out, hits


def _main() -> int:
    text = sys.stdin.read()
    masked, hits = mask(text)
    sys.stdout.write(masked)
    if hits:
        # 仅打 name 统计, 不含原值
        from collections import Counter

        counts = Counter(hits)
        for name, cnt in sorted(counts.items()):
            print(f"masking: {name} x{cnt}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(_main())
