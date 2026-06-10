"""cortex lint runner — 由 lint.sh 调用.

入参 (argparse):
  --mode check|fix
  --target <dir>
  --rules R1,R2,... (逗号分隔, 默认全部)

退出码:
  0 = 无 error
  1 = 有 error (check) 或 fix 失败 (fix)
  2 = 参数错误
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

# 允许以 `python3 -m _lint.runner` 或直接调用
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from _lint import Violation, vault_root_of  # type: ignore
    from _lint.rules import ALL_RULES, run_rules  # type: ignore
    from _lint.fixers import FIXABLE, apply_fix  # type: ignore
else:
    from . import Violation, vault_root_of
    from .rules import ALL_RULES, run_rules
    from .fixers import FIXABLE, apply_fix


def _print_report(violations: list[Violation]) -> None:
    by_rule: Counter = Counter(v.rule for v in violations)
    by_level: Counter = Counter(v.level for v in violations)
    print(f"violations: {len(violations)}")
    print(f"  error: {by_level.get('error', 0)}")
    print(f"  warn:  {by_level.get('warn', 0)}")
    print("by-rule:")
    for r in ALL_RULES:
        print(f"  {r}: {by_rule.get(r, 0)}")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="lint.runner")
    ap.add_argument("--mode", choices=["check", "fix"], default="check")
    ap.add_argument("--target", required=True)
    ap.add_argument("--rules", default="")
    args = ap.parse_args(argv)

    target = Path(args.target)
    if not target.is_dir():
        print(f"ERROR: target not a directory: {target}", file=sys.stderr)
        return 2

    rules = [r.strip() for r in args.rules.split(",") if r.strip()] or ALL_RULES
    bad = [r for r in rules if r not in ALL_RULES]
    if bad:
        print(f"ERROR: unknown rules: {bad} (allowed: {ALL_RULES})", file=sys.stderr)
        return 2

    vault_root = vault_root_of(target)
    violations = run_rules(target, vault_root, rules)

    # 写详情到 stderr
    for v in violations:
        print(v.format(), file=sys.stderr)

    if args.mode == "fix":
        fixed = 0
        fail = 0
        for v in violations:
            if v.rule not in FIXABLE:
                continue
            try:
                if apply_fix(vault_root, v):
                    fixed += 1
            except Exception as e:
                fail += 1
                print(f"FIX-FAIL: {v.format()} :: {e}", file=sys.stderr)
        print(f"fixed: {fixed}")
        if fail:
            print(f"fix-failed: {fail}")
            return 1
        # 重跑一次, 报告剩余
        residual = run_rules(target, vault_root, rules)
        _print_report(residual)
        return 0

    # check 模式
    _print_report(violations)
    errors = [v for v in violations if v.level == "error"]
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
