"""router — 决策表实现。

输入: Entry. 输出: Decision(level/module, target relpath under .wiki/, reason, ask?).

决策顺序 (与 cortex-schema 路由表对齐):
  1. URL (含 github.com / gitlab.com / 任意 https?://) → 项目/<host>/<owner>/<repo>/
  2. frontmatter area → 领域/<area>/<sub or "general">/
  注: 三模块目录名为中文 (项目/领域/脚本); memory/L<n>-<suffix>/ 保留英文.
  3. 关键词 L0 (永远/硬性/never/严禁/绝不) → L0-core (ask)
  4. 关键词 L1 → L1-long (auto, 但同时打 promote 标)
  5. 关键词 L2 或 复用 ≥ 5 + weight ≥ 0.8 → L2-mid (复用高时打 promote-L1 标)
  6. 关键词 L3 或 默认 → L3-short
  7. 复用 ≥ 3 → 附加 promote-L2 标 (仍落 L3, 由 lint 后续晋级)
  8. 兜底 → L4-inbox/_archived/ 保留标记
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from .classifier import Entry


URL_RE = re.compile(r"https?://[^\s\)\]'\"]+")


@dataclass
class Decision:
    target_path: str  # .wiki/ 下相对路径 (不含文件名)
    target_filename: str
    level: str | None  # L0 / L1 / L2 / L3 / None (项目/domains)
    module: str  # memory / projects / domains / archive
    reason: str
    ask: bool = False
    promote_hint: str | None = None  # promote-L2 / promote-L1
    skip: bool = False  # 路由失败兜底


def _safe_seg(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9._-]+", "-", s)
    return s.strip("-_.") or "_"


def _find_url(entry: Entry) -> str | None:
    src = entry.frontmatter.get("source")
    if isinstance(src, str) and src.startswith(("http://", "https://")):
        return src
    m = URL_RE.search(entry.body)
    if m:
        return m.group(0)
    return None


def _route_project(url: str, entry: Entry) -> Decision:
    p = urlparse(url)
    host = _safe_seg(p.hostname or "unknown")
    parts = [s for s in p.path.split("/") if s]
    if host in ("github.com", "gitlab.com", "bitbucket.org") and len(parts) >= 2:
        owner = _safe_seg(parts[0])
        repo = _safe_seg(parts[1])
        target = f"项目/{host}/{owner}/{repo}"
    elif parts:
        target = f"项目/{host}/_/{_safe_seg(parts[0])}"
    else:
        target = f"项目/{host}/_/_"
    return Decision(
        target_path=target,
        target_filename="README.md" if not entry.frontmatter.get("filename") else str(entry.frontmatter["filename"]),
        level=None,
        module="项目",
        reason=f"URL 命中 → 项目/{host}",
    )


def _route_domain(area: str, entry: Entry) -> Decision:
    fm: dict[str, Any] = entry.frontmatter
    sub = fm.get("sub") or "general"
    target = f"领域/{_safe_seg(area)}/{_safe_seg(str(sub))}"
    fname = entry.path.name
    return Decision(
        target_path=target,
        target_filename=fname,
        level=None,
        module="领域",
        reason=f"frontmatter area={area} → 领域/{area}/{sub}",
    )


def decide(entry: Entry) -> Decision:
    fm = entry.frontmatter
    hits = entry.kw_hits

    # 2. domains 优先于 URL (显式 area 字段强信号)
    area = fm.get("area")
    if isinstance(area, str) and area.strip() and fm.get("type") == "domain":
        return _route_domain(area, entry)

    # 1. URL → projects
    url = _find_url(entry)
    if url:
        return _route_project(url, entry)

    # 3. L0 关键词 → ask
    if "L0" in hits:
        return Decision(
            target_path="memory/L0-core",
            target_filename=entry.path.name,
            level="L0",
            module="memory",
            reason=f"L0 关键词命中: {hits['L0']} (ask 用户)",
            ask=True,
        )

    # 4. L1 关键词
    if "L1" in hits:
        return Decision(
            target_path="memory/L1-long",
            target_filename=entry.path.name,
            level="L1",
            module="memory",
            reason=f"L1 关键词命中: {hits['L1']}",
        )

    # 5. L2 关键词 / 高复用 + 高权重
    promote_hint = None
    if entry.reuse_count >= 5 and entry.weight >= 0.8:
        promote_hint = "promote-L1"
    elif entry.reuse_count >= 3:
        promote_hint = "promote-L2"

    if "L2" in hits:
        return Decision(
            target_path="memory/L2-mid",
            target_filename=entry.path.name,
            level="L2",
            module="memory",
            reason=f"L2 关键词命中: {hits['L2']}",
            promote_hint=promote_hint,
        )

    # 6/7. L3 默认 (+ promote 标)
    reason = (
        f"L3 关键词命中: {hits['L3']}" if "L3" in hits else "无显式信号, 默认 L3 (extract 默认入口)"
    )
    return Decision(
        target_path="memory/L3-short",
        target_filename=entry.path.name,
        level="L3",
        module="memory",
        reason=reason,
        promote_hint=promote_hint,
    )
