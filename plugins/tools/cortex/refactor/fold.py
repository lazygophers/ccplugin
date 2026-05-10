#!/usr/bin/env python3
"""cortex refactor: fold — roll up old log/ entries into folds/YYYY-MM-fold-NNN.md.

Strategy (2^k retention): keep last 7 days as-is, fold older days into a single
month-bucket fold file. Idempotent — already-folded files are skipped.

Usage:
    fold.py --vault PATH [--days N] [--apply]

Default dry-run. stdlib only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import backup_file, make_backup_ts


LOG_FILE_RE = re.compile(r"^(\d{2})-(\d{4})-([a-z0-9-]+)\.md$")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", required=True)
    ap.add_argument("--days", type=int, default=7, help="keep last N days unfolded")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    vault = Path(args.vault).expanduser().resolve()
    log_root = vault / "log"
    if not log_root.is_dir():
        print(json.dumps({"error": "log/ directory not found"}), file=sys.stderr)
        return 2

    cutoff = datetime.now() - timedelta(days=args.days)
    folds_root = vault / "folds"

    # group log files by YYYY-MM
    buckets: dict[str, list[Path]] = {}
    for month_dir in sorted(log_root.iterdir()):
        if not month_dir.is_dir() or not re.match(r"^\d{4}-\d{2}$", month_dir.name):
            continue
        for f in sorted(month_dir.glob("*.md")):
            if f.name == "_index.md":
                continue
            m = LOG_FILE_RE.match(f.name)
            if not m:
                continue
            try:
                day = int(m.group(1))
                hhmm = m.group(2)
                yyyymm = month_dir.name
                year, month = yyyymm.split("-")
                file_dt = datetime(int(year), int(month), day,
                                   int(hhmm[:2]), int(hhmm[2:]))
            except Exception:
                continue
            if file_dt < cutoff:
                buckets.setdefault(yyyymm, []).append(f)

    plan: list[dict] = []
    for yyyymm, files in buckets.items():
        # find next fold seq for that month
        existing = sorted(folds_root.glob(f"{yyyymm}-fold-*.md")) if folds_root.is_dir() else []
        used_seqs = set()
        for ef in existing:
            mm = re.match(rf"^{yyyymm}-fold-(\d{{3}})\.md$", ef.name)
            if mm:
                used_seqs.add(int(mm.group(1)))
        next_seq = (max(used_seqs) + 1) if used_seqs else 1
        target_name = f"{yyyymm}-fold-{next_seq:03d}.md"
        plan.append({
            "month": yyyymm,
            "files": [str(f.relative_to(vault)) for f in files],
            "fold_target": f"folds/{target_name}",
            "count": len(files),
        })

    out = {"op": "fold", "buckets": plan, "applied": False, "cutoff_days": args.days}

    if args.apply:
        ts = make_backup_ts()
        folds_root.mkdir(exist_ok=True)
        for entry in plan:
            month = entry["month"]
            target = vault / entry["fold_target"]
            chunks = [f"---\ntype: fold\ntitle: {month} fold\ncreated: {datetime.now().strftime('%Y-%m-%d')}\nupdated: {datetime.now().strftime('%Y-%m-%d')}\n---\n\n# {month} fold\n"]
            for relpath in entry["files"]:
                src = vault / relpath
                try:
                    text = src.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    continue
                chunks.append(f"\n## from [[{src.stem}]]\n\n{text}\n")
                backup_file(vault, "refactor-fold", ts, src)
            target.write_text("\n".join(chunks), encoding="utf-8")
            # delete folded sources
            for relpath in entry["files"]:
                p = vault / relpath
                try:
                    p.unlink()
                except Exception:
                    pass
        out["applied"] = True
        out["backup_ts"] = ts

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
