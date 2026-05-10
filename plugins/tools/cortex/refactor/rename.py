#!/usr/bin/env python3
"""cortex refactor: rename — change a file's basename and rewrite all inbound wikilinks.

Usage:
    rename.py --vault PATH --from REL --to REL [--apply]

Default is dry-run. --apply writes to disk + backup at _meta/.cortex-backup/refactor/<ts>/.
stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import iter_md_files, rewrite_wikilinks, backup_file, make_backup_ts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True)
    ap.add_argument("--from", dest="src", required=True, help="source vault-relative path")
    ap.add_argument("--to", dest="dst", required=True, help="target vault-relative path")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    vault = Path(args.vault).expanduser().resolve()
    src = (vault / args.src).resolve()
    dst = (vault / args.dst).resolve()
    if not src.is_file():
        print(json.dumps({"error": f"source not found: {args.src}"}), file=sys.stderr)
        return 2
    if dst.exists():
        print(json.dumps({"error": f"target exists: {args.dst}"}), file=sys.stderr)
        return 2

    old_stem = src.stem
    new_stem = dst.stem
    mapping = {old_stem: new_stem, args.src.replace(".md", ""): args.dst.replace(".md", "")}

    plan: list[dict] = []
    for md in iter_md_files(vault):
        if md == src:
            continue
        try:
            text = md.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        _, n = rewrite_wikilinks(text, mapping)
        if n > 0:
            plan.append({"file": str(md.relative_to(vault)), "replacements": n})

    out = {
        "op": "rename",
        "from": args.src,
        "to": args.dst,
        "files_to_update": plan,
        "applied": False,
    }

    if args.apply:
        ts = make_backup_ts()
        # backup source
        backup_file(vault, "refactor-rename", ts, src)
        # rewrite all inbound
        for entry in plan:
            md = vault / entry["file"]
            try:
                text = md.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            backup_file(vault, "refactor-rename", ts, md)
            new_text, _ = rewrite_wikilinks(text, mapping)
            md.write_text(new_text, encoding="utf-8")
        # move file
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        out["applied"] = True
        out["backup_ts"] = ts

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
