"""文本纯函数 — frontmatter 解析 / 正文清洗 / 摘要 / slug / 表格单元格转义。

无 IO 无状态, 只吃字符串返字符串, 所以能直接单测。规则文件的 frontmatter 是自定义极简格式
(非完整 YAML), 解析器容错优先: 缺字段一律给默认值, 不为一篇写坏的规则炸掉整次注入。
"""
from __future__ import annotations

import re
from typing import Optional

def _dist(by_cat: dict[str, int]) -> str:
    """类目分布串 '类目(条数), ...', 空则 '-'。"""
    return ", ".join(f"{c}({n})" for c, n in sorted(by_cat.items())) or "-"
def _cell(s: str) -> str:
    """索引表单元格: 空填 '-', 转义 '|' 免破坏 markdown 表格。"""
    return (s or "-").replace("|", "/")
def _months(days: Optional[int]) -> str:
    """天数 → 'N月' 概览 (粗算 30 天/月); None → '-'。"""
    return f"{int(days) // 30}月" if days is not None else "-"
def _sections(text: str) -> list[tuple[str, str]]:
    """主题文件 → [(规则标题, 规则正文)], 按 body 内 `## ` 切。

    无 `##` → 整篇算一条 (frontmatter title 为标题), 兼容尚未合并的旧单规则文件。
    `## ` 之前的引言不算规则 (主题说明), 不入索引。"""
    body = _strip_frontmatter(text)
    parts = re.split(r"^##\s+(.+?)\s*$", body, flags=re.M)
    if len(parts) < 3:
        t, b = _frontmatter(text).get("title", ""), body.strip()
        return [(t, b)] if (t or b) else []
    return [(parts[i].strip(), parts[i + 1].strip()) for i in range(1, len(parts), 2)]
def _slug(s: str) -> str:
    """标题 → 文件名 slug: 空白/路径/markdown 敏感字符 → '-'; 中文原样保留。空 → 'misc'。"""
    s = re.sub(r"[\s/\\:*?\"'<>|#\[\]]+", "-", s.strip())
    return re.sub(r"-{2,}", "-", s).strip("-.")[:60] or "misc"
def _link_target(raw: str) -> str:
    """`[[core/git/merge.md#标题|别名]]` → 归一 `merge#标题`; 无锚点 → `merge` (整篇主题)。"""
    stem, _, anchor = raw.split("|")[0].strip().partition("#")
    stem = stem.split("/")[-1].strip()
    if stem.endswith(".md"):
        stem = stem[:-3]
    anchor = anchor.strip()
    return f"{stem}#{anchor}" if anchor else stem
def _frontmatter(text: str) -> dict[str, str]:
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
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:]
    return text
def _clean_body(body: str) -> str:
    """合并前清洗规则正文: 剥掉正文里泄漏的 frontmatter 块, 一二级标题降为 `###`
    (免与主题文件的 `## 规则标题` 层级冲突把一条规则劈成多条)。"""
    body = re.sub(r"^---\n.*?\n---\n?", "", body.strip(), flags=re.S)
    return re.sub(r"^(#{1,2})\s+", "### ", body, flags=re.M).strip()
def _summary(body: str) -> str:
    s = _strip_frontmatter(body).strip().replace("\n", " ")
    s = re.sub(r"[|]", "/", s)  # 免破坏表格
    return (s[:60] + "…") if len(s) > 60 else s or "-"
