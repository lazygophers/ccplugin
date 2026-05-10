#!/usr/bin/env python3
"""cortex refactor: merge — concatenate two pages into one, redirect backlinks, archive old.

Usage:
    merge.py --vault PATH --from REL --into REL [--apply]

Behavior:
    1. Append <from>'s body (after frontmatter) to <into>, separated by H2 = old title.
    2. Redirect all wikilinks pointing at <from>'s stem to <into>'s stem.
    3. Move <from> to 80_archive/ (LYT) or .archive/ (others); keep history via backup.

Default dry-run. stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import iter_md_files, rewrite_wikilinks, backup_file, make_backup_ts


def split_frontmatter(text: str) -> tuple[str, str]:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end >= 0:
            return text[: end + 4], text[end + 4 :].lstrip("\n")
    return "", text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True)
    ap.add_argument("--from", dest="src", required=True)
    ap.add_argument("--into", dest="dst", required=True)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    vault = Path(args.vault).expanduser().resolve()
    src = (vault / args.src).resolve()
    dst = (vault / args.dst).resolve()
    for p, label in [(src, "from"), (dst, "into")]:
        if not p.is_file():
            print(json.dumps({"error": f"{label} not found: {p}"}), file=sys.stderr)
            return 2

    old_stem = src.stem
    new_stem = dst.stem
    mapping = {old_stem: new_stem}

    src_text = src.read_text(encoding="utf-8", errors="replace")
    dst_text = dst.read_text(encoding="utf-8", errors="replace")
    _src_fm, src_body = split_frontmatter(src_text)

    merged_body = dst_text.rstrip() + f"\n\n## (merged) {old_stem}\n\n" + src_body.strip() + "\n"

    redirect_plan: list[dict] = []
    for md in iter_md_files(vault):
        if md in (src, dst):
            continue
        try:
            text = md.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        _, n = rewrite_wikilinks(text, mapping)
        if n > 0:
            redirect_plan.append({"file": str(md.relative_to(vault)), "replacements": n})

    out = {
        "op": "merge",
        "from": args.src,
        "into": args.dst,
        "redirects": redirect_plan,
        "merged_body_lines": merged_body.count("\n") + 1,
        "applied": False,
    }

    if args.apply:
        ts = make_backup_ts()
        backup_file(vault, "refactor-merge", ts, src)
        backup_file(vault, "refactor-merge", ts, dst)
        # write merged
        dst.write_text(merged_body, encoding="utf-8")
        # redirect inbound
        for entry in redirect_plan:
            md = vault / entry["file"]
            try:
                text = md.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            backup_file(vault, "refactor-merge", ts, md)
            new_text, _ = rewrite_wikilinks(text, mapping)
            md.write_text(new_text, encoding="utf-8")
        # archive old
        archive_root = vault / "80_archive"
        if not archive_root.is_dir():
            archive_root = vault / ".archive"
        archive_root.mkdir(exist_ok=True)
        archived = archive_root / f"{ts}-{src.name}"
        src.rename(archived)
        out["applied"] = True
        out["backup_ts"] = ts
        out["archived_to"] = str(archived.relative_to(vault))

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
