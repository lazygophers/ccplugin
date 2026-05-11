#!/usr/bin/env python3
"""cortex refactor: dedupe — semantic near-duplicate detection + merge.

Usage:
    dedupe.py --vault PATH [--scope concepts] [--threshold 0.85]
              [--top-k 20] [--apply]

Algorithm: for each page in scope, ripgrep + (optional) Smart Connections
neighbor pages, compute TF-IDF cosine pairwise, keep pairs ≥ threshold.
--apply invokes merge.py for each pair (subprocess).

stdlib only. No numpy/scipy.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import iter_md_files  # noqa: E402

_SCOPE_DIRS = {
    "all": "",
    "concepts": "10_concepts",
    "domains": "30_domains",
    "log": "log",
}


def _title_from(path: Path) -> str:
    try:
        with path.open("r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if line.startswith("# "):
                    return line[2:].strip()
                if path.stat().st_size > 32_768:
                    break
    except OSError:
        pass
    return path.stem


def _cosine(text_a: str, text_b: str) -> float:
    def tfidf(text: str) -> dict[str, float]:
        tokens = re.findall(r"[A-Za-z0-9一-鿿]+", text.lower())
        if not tokens:
            return {}
        tf = Counter(tokens)
        total = len(tokens)
        return {t: c / total for t, c in tf.items()}

    va, vb = tfidf(text_a), tfidf(text_b)
    keys = set(va) & set(vb)
    dot = sum(va[k] * vb[k] for k in keys)
    na = math.sqrt(sum(v * v for v in va.values()))
    nb = math.sqrt(sum(v * v for v in vb.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _smart_connections(
    query: str, limit: int, base: str
) -> list[dict] | None:
    info_url = f"{base.rstrip('/')}/embeddings/info"
    try:
        urllib.request.urlopen(info_url, timeout=1.0).read()  # noqa: S310
    except (urllib.error.URLError, urllib.error.HTTPError, OSError,
            TimeoutError):
        return None
    search_url = f"{base.rstrip('/')}/search"
    payload = json.dumps({"query": query, "top_k": limit}).encode("utf-8")
    req = urllib.request.Request(  # noqa: S310
        search_url, data=payload,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=5.0).read()  # noqa: S310
    except (urllib.error.URLError, urllib.error.HTTPError, OSError,
            TimeoutError):
        return []
    try:
        data = json.loads(resp.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return []
    items = data.get("hits") or data.get("results") or data
    if not isinstance(items, list):
        return []
    out: list[dict] = []
    for item in items[:limit]:
        if not isinstance(item, dict):
            continue
        path = item.get("path") or item.get("file") or ""
        if path:
            out.append({"path": path})
    return out


def _ripgrep_paths(vault: Path, query: str, scope_dir: str) -> list[str]:
    target = vault / scope_dir if scope_dir else vault
    if not target.is_dir():
        return []
    try:
        proc = subprocess.run(  # noqa: S603,S607
            ["rg", "-l", "-i", query, str(target)],
            capture_output=True, text=True, timeout=5, check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    return [line for line in proc.stdout.splitlines() if line]


def _candidate_paths(
    vault: Path, page: Path, scope_dir: str, top_k: int, sc_base: str
) -> list[Path]:
    title = _title_from(page)
    try:
        body = page.read_text(encoding="utf-8", errors="replace")[:200]
    except OSError:
        body = ""
    query = f"{title} {body}".strip()
    seen: set[Path] = set()
    out: list[Path] = []

    sc_hits = _smart_connections(query, top_k, sc_base)
    for h in (sc_hits or []):
        p = Path(h["path"]).resolve()
        if p == page or p in seen or not p.is_file():
            continue
        seen.add(p)
        out.append(p)

    if len(out) < top_k:
        rg_hits = _ripgrep_paths(vault, title[:40], scope_dir)
        for hp in rg_hits:
            p = Path(hp).resolve()
            if p == page or p in seen or not p.is_file():
                continue
            seen.add(p)
            out.append(p)
            if len(out) >= top_k:
                break
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True)
    ap.add_argument("--scope", default="all", choices=sorted(_SCOPE_DIRS))
    ap.add_argument("--threshold", type=float, default=0.85)
    ap.add_argument("--top-k", type=int, default=20, dest="top_k")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    vault = Path(args.vault).expanduser().resolve()
    if not vault.is_dir():
        print(json.dumps({"error": f"vault not found: {vault}"}),
              file=sys.stderr)
        return 2

    scope_dir = _SCOPE_DIRS[args.scope]
    scope_root = vault / scope_dir if scope_dir else vault
    if not scope_root.is_dir():
        print(json.dumps({
            "op": "dedupe",
            "threshold": args.threshold,
            "candidates": [],
            "applied": False,
        }, ensure_ascii=False))
        return 0

    sc_base = os.environ.get("CORTEX_SC_URL", "http://127.0.0.1:27123")
    pages = [p for p in iter_md_files(scope_root) if p.is_file()]

    raw_candidates: list[dict] = []
    for page in pages:
        try:
            page_text = page.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for other in _candidate_paths(
            vault, page, scope_dir, args.top_k, sc_base
        ):
            try:
                other_text = other.read_text(
                    encoding="utf-8", errors="replace"
                )
            except OSError:
                continue
            score = _cosine(page_text, other_text)
            if score >= args.threshold:
                raw_candidates.append({
                    "pages": [
                        str(page.relative_to(vault)),
                        str(other.relative_to(vault)),
                    ],
                    "score": round(score, 4),
                    "suggestion": (
                        f"merge {page.stem} into {other.stem}"
                    ),
                })

    seen: set[frozenset] = set()
    deduped: list[dict] = []
    for c in raw_candidates:
        key = frozenset(c["pages"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(c)

    output: dict = {
        "op": "dedupe",
        "threshold": args.threshold,
        "candidates": deduped,
        "applied": False,
    }

    if args.apply and deduped:
        merge_script = Path(__file__).parent / "merge.py"
        for c in deduped:
            r = subprocess.run(  # noqa: S603
                [sys.executable, str(merge_script),
                 "--vault", str(vault),
                 "--from", c["pages"][0],
                 "--into", c["pages"][1],
                 "--apply"],
                capture_output=True, text=True, timeout=30, check=False,
            )
            c["merge_rc"] = r.returncode
        output["applied"] = True

    print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
