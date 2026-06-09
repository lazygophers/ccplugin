"""classifier — 三轴信号识别 (时效 / 强度 / 复用面)。

对 L4-inbox 中每个 .md 文件抽取:
  - frontmatter (YAML 块, 失败回退到空 dict)
  - 内容主体 (用于关键词扫与复用面 token overlap)
  - mtime + frontmatter.created
  - weight (frontmatter.weight 或关键词推断)
  - keyword 命中 (L0 / L1 / L2 / L3 / forget)
  - reuse_count (与 inbox 其它文件 token overlap ≥ 阈值 的次数)

依赖: 优先用 pyyaml, 不可用回退到最简 K:V parser (仅支持 scalar + flow list).
"""
from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:  # pragma: no cover
    import yaml  # type: ignore

    _HAS_YAML = True
except Exception:  # pragma: no cover
    _HAS_YAML = False


# 关键词表 (中英混合, 大小写不敏感匹配)
KW_L0 = ("永远", "硬性", "never", "严禁", "绝不")
KW_L1 = ("永久记住", "长期保留", "long-term remember")
KW_L2 = ("记住", "以后也用", "remember it")
KW_L3 = ("暂时", "临时", "这次", "tentatively", "for now")
KW_FORGET = ("忘了", "不重要了", "forget it")

# token overlap 复用阈值
REUSE_MIN_OVERLAP = 3


@dataclass
class Entry:
    path: Path
    rel: str
    sha256: str
    mtime: float
    frontmatter: dict[str, Any]
    body: str
    weight: float
    kw_hits: dict[str, list[str]] = field(default_factory=dict)
    reuse_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "rel": self.rel,
            "sha256": self.sha256,
            "mtime": self.mtime,
            "frontmatter": self.frontmatter,
            "weight": self.weight,
            "kw_hits": self.kw_hits,
            "reuse_count": self.reuse_count,
        }


def _fallback_parse(text: str) -> dict[str, Any]:
    """极简 YAML 子集 parser (key: value / key: [a, b])."""
    out: dict[str, Any] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            items = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
            out[key] = items
        elif val:
            v = val.strip("'\"")
            try:
                out[key] = float(v) if "." in v else int(v)
            except ValueError:
                out[key] = v
    return out


def _parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    fm_text, body = parts[1], parts[2]
    try:
        fm = yaml.safe_load(fm_text) if _HAS_YAML else _fallback_parse(fm_text)
    except Exception:
        fm = _fallback_parse(fm_text)
    if not isinstance(fm, dict):
        fm = {}
    return fm, body.lstrip("\n")


def _kw_hits(text: str) -> dict[str, list[str]]:
    low = text.lower()
    hits: dict[str, list[str]] = {}
    for label, group in (
        ("L0", KW_L0),
        ("L1", KW_L1),
        ("L2", KW_L2),
        ("L3", KW_L3),
        ("forget", KW_FORGET),
    ):
        matched = [k for k in group if k.lower() in low or k in text]
        if matched:
            hits[label] = matched
    return hits


def _infer_weight(fm: dict[str, Any], hits: dict[str, list[str]]) -> float:
    w = fm.get("weight")
    if isinstance(w, (int, float)):
        return max(0.0, min(1.0, float(w)))
    if "L0" in hits or "L1" in hits:
        return 1.0
    if "L3" in hits:
        return 0.3
    return 0.5


_TOKEN_RE = re.compile(r"[\w一-鿿]{2,}", re.UNICODE)


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN_RE.findall(text)}


def scan_inbox(inbox_dir: Path) -> list[Entry]:
    """扫描 L4-inbox 全部 .md, 返回 Entry 列表 (含复用面统计)."""
    files = sorted(p for p in inbox_dir.glob("*.md") if p.is_file())
    entries: list[Entry] = []
    tokens_list: list[set[str]] = []
    for p in files:
        raw = p.read_text(encoding="utf-8", errors="replace")
        fm, body = _parse_frontmatter(raw)
        hits = _kw_hits(raw)
        weight = _infer_weight(fm, hits)
        sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        entries.append(
            Entry(
                path=p,
                rel=str(p.relative_to(inbox_dir)),
                sha256=sha,
                mtime=p.stat().st_mtime,
                frontmatter=fm,
                body=body,
                weight=weight,
                kw_hits=hits,
            )
        )
        tokens_list.append(_tokens(body))

    # 复用面: 与其它条目 token overlap ≥ REUSE_MIN_OVERLAP 的兄弟数 + 1 (自身基线)
    for i, e in enumerate(entries):
        cnt = 1
        for j, other in enumerate(tokens_list):
            if i == j:
                continue
            if len(tokens_list[i] & other) >= REUSE_MIN_OVERLAP:
                cnt += 1
        e.reuse_count = cnt
    return entries
