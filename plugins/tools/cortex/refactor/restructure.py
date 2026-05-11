#!/usr/bin/env python3
"""cortex refactor: restructure — migrate vault between layout presets.

Usage:
    restructure.py --vault PATH --from <preset> --to <preset> [--apply]

Presets: flat | LYT | PARA

Dry-run prints {mv_plan, link_plan, warnings, applied:false}.
--apply moves files, backs up originals, then rewrites wikilinks
vault-wide via shared _common.rewrite_wikilinks.

stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import (  # noqa: E402
    backup_file,
    iter_md_files,
    make_backup_ts,
    rewrite_wikilinks,
)

PRESETS: dict[str, dict[str, str]] = {
    "flat": {
        "concepts": "concepts",
        "domains": "domains",
        "log": "log",
        "archive": ".archive",
    },
    "LYT": {
        "concepts": "10_concepts",
        "domains": "30_domains",
        "log": "log",
        "archive": "80_archive",
    },
    "PARA": {
        "concepts": "1_projects",
        "domains": "2_areas",
        "log": "4_archives/log",
        "archive": "4_archives",
    },
}


def _safe_rel(vault: Path, p: Path) -> Path:
    """Defensive: ensure p is inside vault."""
    return p.resolve().relative_to(vault.resolve())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True)
    ap.add_argument("--from", dest="src_preset", required=True,
                    choices=sorted(PRESETS.keys()))
    ap.add_argument("--to", dest="dst_preset", required=True,
                    choices=sorted(PRESETS.keys()))
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    vault = Path(args.vault).expanduser().resolve()
    if not vault.is_dir():
        print(json.dumps({"error": f"vault not found: {vault}"}),
              file=sys.stderr)
        return 2
    if args.src_preset == args.dst_preset:
        print(json.dumps({
            "op": "restructure",
            "from": args.src_preset,
            "to": args.dst_preset,
            "mv_plan": [],
            "link_plan": [],
            "warnings": ["from == to, nothing to do"],
            "applied": False,
        }, ensure_ascii=False))
        return 0

    src_map = PRESETS[args.src_preset]
    dst_map = PRESETS[args.dst_preset]
    ts = make_backup_ts()

    mv_plan: list[dict] = []
    link_plan: list[dict] = []
    warnings: list[str] = []
    seen_dst: set[str] = set()

    for role, src_rel in src_map.items():
        dst_rel = dst_map.get(role)
        if not dst_rel or src_rel == dst_rel:
            continue
        src_dir = (vault / src_rel).resolve()
        dst_dir = (vault / dst_rel).resolve()
        if not src_dir.is_dir():
            continue
        try:
            src_dir.relative_to(vault)
            dst_dir.relative_to(vault)
        except ValueError:
            warnings.append(f"skip role {role}: path escapes vault")
            continue
        for md in src_dir.rglob("*.md"):
            if not md.is_file():
                continue
            try:
                inner = md.relative_to(src_dir)
            except ValueError:
                continue
            dst = dst_dir / inner
            dst_rel_path = str(dst.relative_to(vault))
            if dst.exists() or dst_rel_path in seen_dst:
                dst = dst.with_name(
                    f"{dst.stem}.restructure-{ts}{dst.suffix}"
                )
                dst_rel_path = str(dst.relative_to(vault))
                warnings.append(f"collision → renamed: {dst_rel_path}")
            seen_dst.add(dst_rel_path)
            mv_plan.append({
                "from": str(md.relative_to(vault)),
                "to": dst_rel_path,
            })
            link_plan.append({
                "old_stem": md.stem,
                "new_rel": dst_rel_path,
            })

    output: dict = {
        "op": "restructure",
        "from": args.src_preset,
        "to": args.dst_preset,
        "mv_plan": mv_plan,
        "link_plan": link_plan,
        "warnings": warnings,
        "applied": False,
    }

    if args.apply and mv_plan:
        for mv in mv_plan:
            src_p = vault / mv["from"]
            dst_p = vault / mv["to"]
            if not src_p.is_file():
                warnings.append(f"missing at apply time: {mv['from']}")
                continue
            backup_file(vault, "restructure", ts, src_p)
            dst_p.parent.mkdir(parents=True, exist_ok=True)
            src_p.rename(dst_p)
        # rewire wikilinks
        mapping = {e["old_stem"]: e["new_rel"].rsplit(".md", 1)[0]
                   for e in link_plan}
        for md in iter_md_files(vault):
            try:
                text = md.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            new_text, n = rewrite_wikilinks(text, mapping)
            if n:
                md.write_text(new_text, encoding="utf-8")
        output["applied"] = True
        output["warnings"] = warnings

    print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
