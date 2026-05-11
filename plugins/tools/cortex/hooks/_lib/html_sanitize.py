#!/usr/bin/env python3
"""html_sanitize.py — cortex P0 安全过滤: 危险 HTML 剥离。

纯函数, 纯 stdlib。被 cortex-ingest defuddle/WebFetch 输出后置调用。

CLI:
    python3 html_sanitize.py < input > output

API:
    sanitize(markdown) -> sanitized_markdown
        - 剥 <script>/<iframe>/<object>/<embed>/<svg onload=...> 含闭合
        - 剥 on*="..."/'...' 内联事件属性
        - 剥 javascript: / data:text/html 协议链接 (替换为 #)
        - 跳过 fenced code block (``` 之间内容) 不处理
"""

from __future__ import annotations

import os
import re
import sys

# 危险标签 (含闭合)
_TAG_BLOCK_RE = re.compile(
    r"<(script|iframe|object|embed)\b[^>]*>[\s\S]*?</\1\s*>",
    re.IGNORECASE,
)
# 自闭合或无闭合的危险标签 (e.g. <script src="..."/> 或 <embed src=...>)
_TAG_SELF_RE = re.compile(
    r"<(script|iframe|object|embed)\b[^>]*/?>",
    re.IGNORECASE,
)
# 内联事件属性 on*="..." / on*='...' / on*=value
_ON_ATTR_RE = re.compile(
    r"""\s+on[a-z]+\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)""",
    re.IGNORECASE,
)
# javascript: / data:text/html 协议
_DANGEROUS_PROTOCOL_RE = re.compile(
    r"""((?:href|src|xlink:href)\s*=\s*['"]?)\s*(?:javascript:|data:text/html[^'"\s>]*)""",
    re.IGNORECASE,
)
# fenced code block (``` ... ``` 或 ~~~ ... ~~~)
_FENCE_RE = re.compile(r"(^|\n)(```|~~~)[^\n]*\n[\s\S]*?\n\2[^\n]*(?=\n|$)")


def _sanitize_segment(seg: str) -> str:
    """对非 code-fence 段落做剥离。"""
    out = _TAG_BLOCK_RE.sub("", seg)
    out = _TAG_SELF_RE.sub("", out)
    out = _ON_ATTR_RE.sub("", out)
    out = _DANGEROUS_PROTOCOL_RE.sub(r"\1#", out)
    return out


def sanitize(markdown: str) -> str:
    """剥危险 HTML, 跳过 fenced code block 内的字面量。"""
    if os.environ.get("CORTEX_SKIP_SANITIZE") == "1":
        return markdown
    if not markdown:
        return markdown
    # 切分: code-fence 块原样保留, 其它段过滤
    out: list[str] = []
    last = 0
    for m in _FENCE_RE.finditer(markdown):
        start, end = m.span()
        # 处理 fence 前的普通段
        out.append(_sanitize_segment(markdown[last:start]))
        # fence 块原样保留 (含前导换行)
        out.append(markdown[start:end])
        last = end
    out.append(_sanitize_segment(markdown[last:]))
    return "".join(out)


def _main() -> int:
    text = sys.stdin.read()
    sys.stdout.write(sanitize(text))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
