#!/usr/bin/env python3
"""cortex refactor: graph-rebalance — scan orphans/hubs + suggest link gaps.

Usage:
    graph_rebalance.py --vault PATH [--hub-threshold 20] [--scope all]
                       [--apply]

stdlib only.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import (  # noqa: E402
    WIKILINK_RE,
    backup_file,
    iter_md_files,
    make_backup_ts,
)

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


def _ripgrep_simple(vault: Path, query: str) -> list[str]:
    if not query.strip():
        return []
    try:
        proc = subprocess.run(  # noqa: S603,S607
            ["rg", "-l", "-i", "-g", "*.md",
             "-g", "!_meta/**", "-g", "!.obsidian/**", "-g", "!.git/**",
             "-g", "!.trash/**",
             query, str(vault)],
            capture_output=True, text=True, timeout=5, check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    return [line for line in proc.stdout.splitlines() if line]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True)
    ap.add_argument("--hub-threshold", type=int, default=20,
                    dest="hub_threshold")
    ap.add_argument("--scope", default="all",
                    choices=sorted(_SCOPE_DIRS.keys()))
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    vault = Path(args.vault).expanduser().resolve()
    if not vault.is_dir():
        print(json.dumps({"error": f"vault not found: {vault}"}),
              file=sys.stderr)
        return 2

    scope_dir = _SCOPE_DIRS[args.scope]
    scope_root = vault / scope_dir if scope_dir else vault

    backlinks: dict[str, set[str]] = defaultdict(set)
    forward: dict[str, set[str]] = defaultdict(set)
    for md in iter_md_files(vault):
        try:
            text = md.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in WIKILINK_RE.finditer(text):
            target = m.group(1).strip().split("/")[-1]
            if target.lower().endswith(".md"):
                target = target[:-3]
            backlinks[target].add(str(md.relative_to(vault)))
            forward[md.stem].add(target)

    if scope_root.is_dir():
        all_pages = [p for p in iter_md_files(scope_root) if p.is_file()]
    else:
        all_pages = []

    orphans = [
        p for p in all_pages
        if not backlinks[p.stem] and not forward[p.stem]
    ]
    hubs = [
        p for p in all_pages
        if len(backlinks[p.stem]) >= args.hub_threshold
    ]

    link_gaps: list[dict] = []
    for orphan in orphans[:50]:
        title = _title_from(orphan)
        rg_paths = _ripgrep_simple(vault, title[:40])
        candidates: list[str] = []
        for hp in rg_paths:
            ap_p = Path(hp).resolve()
            if ap_p == orphan:
                continue
            try:
                rel = str(ap_p.relative_to(vault))
            except ValueError:
                continue
            candidates.append(rel)
            if len(candidates) >= 3:
                break
        if candidates:
            link_gaps.append({
                "orphan": str(orphan.relative_to(vault)),
                "candidates": candidates,
            })

    output: dict = {
        "op": "graph_rebalance",
        "orphans": [
            {
                "path": str(p.relative_to(vault)),
                "forward_count": len(forward[p.stem]),
            }
            for p in orphans
        ],
        "hubs": [
            {
                "path": str(p.relative_to(vault)),
                "backlink_count": len(backlinks[p.stem]),
                "suggestion": "consider splitting",
            }
            for p in hubs
        ],
        "link_gaps": link_gaps,
        "applied": False,
    }

    if args.apply and link_gaps:
        ts = make_backup_ts()
        for gap in link_gaps:
            for candidate in gap["candidates"][:1]:
                cpath = vault / candidate
                if not cpath.is_file():
                    continue
                backup_file(vault, "graph-rebalance", ts, cpath)
                orphan_stem = Path(gap["orphan"]).stem
                with cpath.open("a", encoding="utf-8") as f:
                    f.write(f"\n相关: [[{orphan_stem}]]\n")
        output["applied"] = True

    print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
