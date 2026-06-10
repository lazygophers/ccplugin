"""runner — ingest.sh 的 python 入口.

职责:
  - 解析 --mode {dry-run, apply} / --target / --source
  - identify → planner.build_plan → 输出 JSON

退出:
  0 plan 生成 OK
  1 识别 / 路由失败
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import identify as identify_mod
from . import planner


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="ingest", description="cortex 项目入库 planner")
    ap.add_argument("--mode", choices=("dry-run", "apply"), default="dry-run")
    ap.add_argument("--target", required=True)
    ap.add_argument("--source", required=True)
    args = ap.parse_args(argv)

    target = Path(args.target).expanduser()
    # target 不强制存在 (dry-run 仅算路径), 但若给了就尝试 resolve
    try:
        target = target.resolve()
    except Exception:
        pass

    try:
        kind = identify_mod.identify(args.source)
    except ValueError as e:
        json.dump(
            {"error": str(e), "source": args.source, "mode": args.mode},
            sys.stdout,
            ensure_ascii=False,
            indent=2,
        )
        sys.stdout.write("\n")
        return 1

    result = planner.build_plan(kind, str(target), args.mode)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
