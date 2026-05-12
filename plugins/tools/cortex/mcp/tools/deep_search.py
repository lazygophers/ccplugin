"""`cortex_deep_search` MCP tool — multi-mode deep retrieval over the vault.

Three modes:

- ``iterative``: multi-round retrieval. Each round mines "gap" tokens from
  current hit snippets, queries again, dedups, until path-set Jaccard ≥ 0.8
  or ``iter_max`` rounds (hard cap 3).
- ``subgraph``: expand seed hits via backlinks + forward wikilinks up to
  ``max_hops`` (hard cap 3). Hop-N nodes scored 1/(2N).
- ``hybrid``: smart-connections + ripgrep merged, BM25 reranked. SC
  unreachable → degraded mode, rg-only.

Returns a single TextContent whose ``.text`` is JSON:

    {"query", "mode", "hits": [...], "iterations", "subgraph_expanded",
     "degraded": bool}
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any

from mcp.types import TextContent, Tool

from lib.vault_path import resolve_vault
from tools.search import (
    _dedup,
    _grep_file,
    _ripgrep,
    _smart_connections,
    _title_from,
)

DEEP_SEARCH_TOOL = Tool(
    name="cortex_deep_search",
    description=(
        "深度检索 vault: iterative(多轮RAG) | subgraph(图邻扩展) | "
        "hybrid(语义+关键词+BM25重排)"
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "mode": {
                "type": "string",
                "enum": ["iterative", "subgraph", "hybrid"],
                "default": "hybrid",
            },
            "max_hops": {
                "type": "integer",
                "default": 2,
                "minimum": 1,
                "maximum": 3,
            },
            "iter_max": {
                "type": "integer",
                "default": 3,
                "minimum": 1,
                "maximum": 3,
            },
            "limit": {"type": "integer", "default": 15, "minimum": 1},
            "scope": {
                "type": "string",
                "enum": ["all", "concepts", "domains", "log"],
                "default": "all",
            },
        },
        "required": ["query"],
    },
)


_SCOPE_GLOB = {
    "all": "知识库",
    "concepts": "知识库/领域",
    "domains": "知识库/来源/代码仓库",
    "log": "知识库/日记",
}

_WIKILINK_RE = re.compile(
    r"(?<!\!)\[\[([^\[\]\n|#^]+)((?:[#^][^\[\]\n|]*)?(?:\|[^\[\]\n]*)?)\]\]"
)
_FORWARD_RE = re.compile(r"\[\[([^\[\]\n|#^]+)")
_TOKEN_RE = re.compile(r"[A-Za-z0-9一-鿿]+")

_EXCLUDE_DIRS = {"_meta", ".obsidian", ".trash", ".git"}


def _iter_md_files(vault: Path):
    for p in vault.rglob("*.md"):
        rel = p.relative_to(vault)
        if rel.parts and rel.parts[0] in _EXCLUDE_DIRS:
            continue
        yield p


def _base_search(
    vault: Path,
    query: str,
    limit: int,
    scope: str,
    sc_base: str,
) -> tuple[list[dict[str, Any]], bool]:
    """Run hot → index → SC → rg fallback (mirrors cortex_search core)."""
    hits: list[dict[str, Any]] = []
    degraded = False

    if scope == "all":
        hits.extend(_grep_file(vault, "hot.md", query, "hot"))
    if len(hits) < limit:
        hits.extend(_grep_file(vault, "index.md", query, "index"))

    if len(hits) < limit:
        sc_hits = _smart_connections(query, limit, sc_base)
        if sc_hits is None:
            degraded = True
        elif sc_hits:
            hits.extend(sc_hits)

    if len(hits) < limit:
        hits.extend(_ripgrep(vault, _SCOPE_GLOB.get(scope, "wiki"), query))

    return _dedup(hits)[:limit], degraded


def _bm25_rerank(
    hits: list[dict[str, Any]],
    query: str,
    k1: float = 1.5,
    b: float = 0.75,
) -> list[dict[str, Any]]:
    tokens = [t for t in query.lower().split() if t]
    if not tokens or not hits:
        return list(hits)
    docs = [
        (h, (str(h.get("snippet", "")) + " " + str(h.get("title", ""))).lower())
        for h in hits
    ]
    avgdl = max(
        1.0,
        sum(len(d.split()) for _, d in docs) / max(len(docs), 1),
    )
    scored: list[tuple[float, dict[str, Any]]] = []
    for h, doc in docs:
        tf = Counter(doc.split())
        dl = max(1, len(doc.split()))
        bm25 = 0.0
        for t in tokens:
            if tf[t] == 0:
                continue
            bm25 += (
                tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * dl / avgdl))
            )
        scored.append((bm25 + float(h.get("score", 0.0)), h))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [h for _, h in scored]


def _paths(hits: list[dict[str, Any]]) -> set[str]:
    return {str(h.get("path", "")) for h in hits if h.get("path")}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    u = a | b
    if not u:
        return 0.0
    return len(a & b) / len(u)


def _extract_gap_tokens(
    hits: list[dict[str, Any]], query: str, top: int = 3
) -> str:
    """Take high-frequency tokens from hit snippets that are NOT in query."""
    q_tokens = {t.lower() for t in _TOKEN_RE.findall(query)}
    counter: Counter[str] = Counter()
    for h in hits:
        text = (str(h.get("snippet", "")) + " " + str(h.get("title", ""))).lower()
        for tok in _TOKEN_RE.findall(text):
            if len(tok) < 2:
                continue
            if tok in q_tokens:
                continue
            counter[tok] += 1
    most = [tok for tok, _ in counter.most_common(top)]
    if not most:
        return query
    return query + " " + " ".join(most)


def _backlinks(vault: Path, page_stem: str) -> set[str]:
    """All vault md files whose body contains [[<stem>]] (any variant)."""
    out: set[str] = set()
    stem_lc = page_stem.lower()
    for md in _iter_md_files(vault):
        try:
            text = md.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in _WIKILINK_RE.finditer(text):
            target = m.group(1).strip()
            if target.lower().endswith(".md"):
                target = target[:-3]
            if target.split("/")[-1].lower() == stem_lc:
                out.add(str(md))
                break
    return out


def _forward_links(vault: Path, page: Path) -> set[str]:
    """All vault paths referenced by ``[[...]]`` inside page."""
    out: set[str] = set()
    try:
        text = page.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return out
    for m in _WIKILINK_RE.finditer(text):
        target = m.group(1).strip()
        if target.lower().endswith(".md"):
            target = target[:-3]
        stem = target.split("/")[-1].lower()
        # locate first md whose stem matches
        for md in _iter_md_files(vault):
            if md.stem.lower() == stem and md != page:
                out.add(str(md))
                break
    return out


def _path_to_hit(vault: Path, path_str: str, score: float) -> dict[str, Any]:
    p = Path(path_str)
    title = _title_from(p)
    snippet = ""
    try:
        snippet = p.read_text(encoding="utf-8", errors="replace")[:240]
        snippet = snippet.replace("\n", " ")
    except OSError:
        pass
    return {
        "path": path_str,
        "title": title,
        "snippet": snippet,
        "score": round(score, 4),
        "source": "subgraph",
    }


def _run_iterative(
    vault: Path,
    query: str,
    limit: int,
    iter_max: int,
    scope: str,
    sc_base: str,
) -> dict[str, Any]:
    iter_max = max(1, min(3, int(iter_max)))
    hits, degraded = _base_search(vault, query, limit, scope, sc_base)
    iterations = 1
    prev_paths: set[str] = set()
    for i in range(1, iter_max):
        cur = _paths(hits)
        if _jaccard(cur, prev_paths) >= 0.8:
            break
        prev_paths = cur
        gap_q = _extract_gap_tokens(hits, query)
        if gap_q == query:
            break
        new_hits, d2 = _base_search(vault, gap_q, limit, scope, sc_base)
        degraded = degraded or d2
        hits = _dedup(hits + new_hits)[:limit]
        iterations = i + 1
    return {
        "hits": hits,
        "iterations": iterations,
        "subgraph_expanded": 0,
        "degraded": degraded,
    }


def _run_subgraph(
    vault: Path,
    query: str,
    limit: int,
    max_hops: int,
    scope: str,
    sc_base: str,
) -> dict[str, Any]:
    max_hops = max(1, min(3, int(max_hops)))
    seed_hits, degraded = _base_search(vault, query, limit, scope, sc_base)
    seed_paths = {h["path"] for h in seed_hits if h.get("path")}
    expanded: set[str] = set(seed_paths)
    hop_score: dict[str, float] = {p: 1.0 for p in seed_paths}

    frontier = set(seed_paths)
    for hop in range(1, max_hops + 1):
        new_paths: set[str] = set()
        for p in list(frontier):
            page = Path(p)
            if not page.is_file():
                continue
            new_paths |= _backlinks(vault, page.stem)
            new_paths |= _forward_links(vault, page)
        new_paths -= expanded
        if not new_paths:
            break
        for p in new_paths:
            hop_score[p] = 1.0 / (hop * 2)
        expanded |= new_paths
        frontier = new_paths

    all_hits = list(seed_hits)
    seen = set(seed_paths)
    for p in expanded - seed_paths:
        if p in seen:
            continue
        seen.add(p)
        all_hits.append(_path_to_hit(vault, p, hop_score.get(p, 0.25)))
    all_hits.sort(key=lambda h: float(h.get("score", 0.0)), reverse=True)
    return {
        "hits": all_hits[:limit],
        "iterations": 1,
        "subgraph_expanded": max(0, len(expanded) - len(seed_paths)),
        "degraded": degraded,
    }


def _run_hybrid(
    vault: Path,
    query: str,
    limit: int,
    scope: str,
    sc_base: str,
) -> dict[str, Any]:
    sc_hits = _smart_connections(query, limit * 2, sc_base)
    degraded = sc_hits is None
    sc_hits = sc_hits or []
    rg_hits = _ripgrep(vault, _SCOPE_GLOB.get(scope, "wiki"), query)
    merged = sc_hits + rg_hits
    reranked = _bm25_rerank(merged, query)
    deduped = _dedup(reranked)[:limit]
    return {
        "hits": deduped,
        "iterations": 1,
        "subgraph_expanded": 0,
        "degraded": degraded,
    }


async def handle_deep_search(args: dict) -> list[TextContent]:
    query = (args or {}).get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError(
            "cortex_deep_search: 'query' required (non-empty string)"
        )
    mode = (args or {}).get("mode") or "hybrid"
    if mode not in ("iterative", "subgraph", "hybrid"):
        raise ValueError(f"cortex_deep_search: invalid mode {mode!r}")
    limit = int((args or {}).get("limit") or 15)
    if limit < 1:
        raise ValueError("cortex_deep_search: 'limit' must be ≥ 1")
    max_hops = int((args or {}).get("max_hops") or 2)
    iter_max = int((args or {}).get("iter_max") or 3)
    scope = (args or {}).get("scope") or "all"
    if scope not in _SCOPE_GLOB:
        raise ValueError(f"cortex_deep_search: invalid scope {scope!r}")

    vault = resolve_vault()
    sc_base = os.environ.get("CORTEX_SC_URL", "http://127.0.0.1:27123")

    if mode == "iterative":
        out = _run_iterative(vault, query, limit, iter_max, scope, sc_base)
    elif mode == "subgraph":
        out = _run_subgraph(vault, query, limit, max_hops, scope, sc_base)
    else:
        out = _run_hybrid(vault, query, limit, scope, sc_base)

    result = {
        "query": query,
        "mode": mode,
        **out,
    }
    return [
        TextContent(
            type="text",
            text=json.dumps(result, ensure_ascii=False),
        )
    ]
