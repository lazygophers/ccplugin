"""runner — extract.sh 的 python 入口.

职责:
  - 解析 --mode {dry-run, apply} / --target / --no-cursor
  - 调用 writer.build_plan / apply_plan
  - 输出 JSON 到 stdout

退出:
  0 成功
  1 错误 (inbox 缺失 / apply 失败)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import writer


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="extract", description="cortex L4-inbox extractor")
    ap.add_argument("--mode", choices=("dry-run", "apply"), default="dry-run")
    ap.add_argument("--target", required=True)
    ap.add_argument("--no-cursor", action="store_true", dest="no_cursor")
    args = ap.parse_args(argv)

    target = Path(args.target).resolve()
    if not target.is_dir():
        json.dump({"error": f"target not dir: {target}"}, sys.stdout, ensure_ascii=False)
        return 1

    result = writer.build_plan(target, ignore_cursor=args.no_cursor)
    if "error" in result:
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 1

    if args.mode == "apply":
        applied = writer.apply_plan(target, result["plan"])
        result["applied"] = applied["applied"]
        result["rejected"] = applied["rejected"]
        result["cursor"] = applied["cursor"]

    result["mode"] = args.mode
    result["target"] = str(target)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
