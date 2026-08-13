"""runner — history-digest.sh 的 python 入口.

职责:
  - 解析 --mode / --target / --source-root / --since
  - 调 scanner → parser → extractor → router
  - 输出 JSON plan 到 stdout

退出:
  0 成功
  1 source-root 无 jsonl / 全失败
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import parser as _parser
from . import extractor as _extractor
from . import router as _router
from . import scanner as _scanner


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="history-digest", description="Claude Code transcripts → 全局记忆库 plan"
    )
    ap.add_argument("--mode", choices=("dry-run", "apply"), default="dry-run")
    ap.add_argument("--target", required=True)
    ap.add_argument("--source-root", required=True, dest="source_root")
    ap.add_argument("--since", default="")
    args = ap.parse_args(argv)

    source_root = Path(args.source_root).resolve()
    target = Path(args.target).resolve()

    files = _scanner.scan(source_root, since=args.since)
    plan: list[dict] = []
    stats = {"files_scanned": len(files), "messages": 0, "increments": 0}

    for fp in files:
        msgs = list(_parser.parse_file(fp))
        stats["messages"] += len(msgs)
        incs = _extractor.extract(msgs)
        stats["increments"] += len(incs)
        plan.extend(_router.route_all(incs))

    result = {
        "mode": args.mode,
        "source_root": str(source_root),
        "target": str(target),
        "since": args.since,
        "stats": stats,
        "plan": plan,
    }
    if args.mode == "apply":
        result["apply_note"] = "需 main 后处理 — 本 task 范围不实写, 用 cortex-extract --apply 或主会话审过后落盘"

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
