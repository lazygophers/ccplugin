"""cortex-digest CLI — evolution 抽取子命令.

借鉴 agent-playbook self-improving-agent 多 memory 架构: cortex 现 episodic
(jsonl) + working (hot.md), 本模块补 **semantic 层** — 扫近 N 天 sessions/
jsonl, 抽复发 pattern, 写 `记忆/L0-核心/patterns.md` 单 markdown 文件 (D1),
阈值过线 (confidence ≥ 0.8 AND applications ≥ 3, D4 硬编码) 时生 proposal
到 `_assets/evolution-proposals/<YYYY-MM-DD>-<slug>.md`.

本 CLI 仅生 proposal markdown, 不实际 patch SKILL/AGENT (PR4 范围).

属 python CLI 例外 (AGENT.md §协作约定 3): 走文件 IO 不受 MCP 写契约约束.
核心逻辑在 `lib/evolution.py`, 本文件仅 argparse + 调度 + JSON 输出.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

# Allow `python3 digest.py` invocation: add this dir to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lib.evolution import (  # noqa: E402
    DEFAULT_LOOKBACK_DAYS,
    extract_patterns,
    generate_proposals,
    scan_sessions,
    update_doc_scores,
    write_patterns_md,
)
from lib.vault_path import resolve_vault  # noqa: E402


def _cmd_evolution(args: argparse.Namespace) -> int:
    if args.vault:
        vault = Path(os.path.expanduser(args.vault)).resolve()
    else:
        try:
            vault = resolve_vault()
        except RuntimeError as e:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
            return 2

    if not vault.is_dir():
        print(
            json.dumps({"error": f"vault not a directory: {vault}"}),
            file=sys.stderr,
        )
        return 2

    episodes = scan_sessions(vault, args.lookback_days)
    patterns = extract_patterns(episodes)
    added, updated = write_patterns_md(patterns, vault, dry_run=args.dry_run)
    proposals = generate_proposals(patterns, vault, dry_run=args.dry_run)

    score_updates: dict[str, Any] | None = None
    if args.update_scores:
        score_results: list[dict[str, Any]] = []
        for md in vault.rglob("*.md"):
            try:
                rel = md.relative_to(vault)
            except ValueError:
                continue
            rel_str = str(rel).replace("\\", "/")
            if not (
                rel_str.startswith("知识库/")
                or rel_str.startswith("记忆/L0-")
                or rel_str.startswith("记忆/L1-")
                or rel_str.startswith("记忆/L2-")
                or rel_str.startswith("记忆/L3-")
            ):
                continue
            r = update_doc_scores(
                rel_str,
                vault,
                lookback_days=args.lookback_days,
                dry_run=args.dry_run,
            )
            if r.get("applied") or args.dry_run:
                score_results.append(r)
        score_updates = {
            "scanned": len(score_results),
            "applied": sum(1 for r in score_results if r.get("applied")),
            "samples": score_results[:5],
        }

    result: dict[str, Any] = {
        "vault": str(vault),
        "lookback_days": args.lookback_days,
        "dry_run": bool(args.dry_run),
        "sessions_scanned": len(episodes),
        "patterns_candidates": len(patterns),
        "patterns_added": added,
        "patterns_updated": updated,
        "proposals_generated": proposals,
    }
    if score_updates is not None:
        result["score_updates"] = score_updates
    indent = None if args.compact else 2
    print(json.dumps(result, ensure_ascii=False, indent=indent))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="digest",
        description="cortex-digest CLI (evolution 抽取子命令)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_evo = sub.add_parser(
        "evolution",
        help="扫 sessions/ 抽 pattern, 写 patterns.md + proposals",
    )
    p_evo.add_argument(
        "--lookback-days", type=int, default=DEFAULT_LOOKBACK_DAYS,
        help=f"扫描天数 (默认 {DEFAULT_LOOKBACK_DAYS})",
    )
    p_evo.add_argument("--vault", default=None, help="vault 路径覆盖 (默认自动 resolve)")
    p_evo.add_argument("--json", action="store_true", default=True, help="JSON 输出 (默认开)")
    p_evo.add_argument("--compact", action="store_true", help="compact JSON (单行)")
    p_evo.add_argument("--dry-run", action="store_true", help="仅扫不写盘")
    p_evo.add_argument(
        "--update-scores", dest="update_scores", action="store_true", default=True,
        help="跑 update_doc_scores 双路调整 importance/confidence (默认开)",
    )
    p_evo.add_argument(
        "--no-update-scores", dest="update_scores", action="store_false",
        help="跳过双路评分调整",
    )
    p_evo.set_defaults(func=_cmd_evolution)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
